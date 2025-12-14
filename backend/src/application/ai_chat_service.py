from typing import List, Dict, Optional, AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.infrastructure.models import BudgetModel
from src.domain.user import User
from src.application.dtos import BudgetContextDTO, DateRangeDTO, TransactionDTO
from src.application.ports import LLMProvider
import json
import asyncio
import re

class AIChatService:
    """
    AI Chat Service that provides contextually aware responses about budget data.
    """
    
    def __init__(self, session: AsyncSession, user: User, llm_provider: Optional[LLMProvider] = None):
        self.session = session
        self.user = user
        self.llm_provider = llm_provider
    
    def _extract_merchant(self, description: str) -> str:
        """
        Extract merchant name from transaction description.
        Simple heuristic: take first meaningful words (skip common prefixes).
        """
        # Remove common prefixes
        desc = description.strip()
        prefixes = ['PAYMENT', 'PAY', 'AUTH', 'PURCHASE', 'DEBIT', 'CREDIT', 'ONLINE']
        for prefix in prefixes:
            if desc.upper().startswith(prefix):
                desc = desc[len(prefix):].strip()
        
        # Take first 2-3 words as merchant name
        words = desc.split()[:3]
        merchant = ' '.join(words).strip()
        return merchant if merchant else description[:30]  # Fallback to truncated description

    async def get_budget_context(self) -> BudgetContextDTO:
        """
        Gather budget data context for the AI.
        Always queries fresh from database to ensure current state.
        Limits data to manage token usage efficiently.
        """
        # Always query fresh from DB - no caching to ensure current state
        stmt = select(BudgetModel).where(BudgetModel.tenant_id == self.user.tenant_id)
        result = await self.session.execute(stmt)
        entries = result.scalars().all()
        
        if not entries:
            return BudgetContextDTO(
                total_expenses=0.0,
                entry_count=0,
                categories={},
                projects={},
                all_categories=[],
                all_projects=[],
                date_range=None,
                average_expense=0.0,
                recent_transactions=[],
                large_transactions=[],
                top_merchants={}
            )
        
        # Calculate summary statistics
        total = sum(float(e.amount) for e in entries)
        categories = {}
        projects = {}
        merchants = {}
        dates = []
        large_transactions_list = []
        
        for entry in entries:
            # Category breakdown
            cat = entry.category or "Uncategorized"
            categories[cat] = categories.get(cat, 0) + float(entry.amount)
            
            # Project breakdown
            proj = entry.project or "No Project"
            projects[proj] = projects.get(proj, 0) + float(entry.amount)
            
            # Merchant extraction (from description)
            merchant = self._extract_merchant(entry.description)
            merchants[merchant] = merchants.get(merchant, 0) + float(entry.amount)
            
            # Large transactions (> $500)
            if float(entry.amount) > 500:
                large_transactions_list.append(entry)
            
            # Date range
            if entry.date:
                dates.append(entry.date)
        
        dates.sort()
        date_range = DateRangeDTO(
            earliest=dates[0].isoformat() if dates else None,
            latest=dates[-1].isoformat() if dates else None
        )
        
        # Top categories and projects (limit to top 5)
        top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
        top_projects = sorted(projects.items(), key=lambda x: x[1], reverse=True)[:5]
        top_merchants = dict(sorted(merchants.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Recent transactions (last 10, ordered by date descending)
        sorted_entries = sorted(entries, key=lambda e: e.date, reverse=True)
        recent_transactions = [
            TransactionDTO(
                date=e.date.isoformat(),
                amount=float(e.amount),
                description=e.description,
                category=e.category or "Uncategorized",
                project=e.project
            )
            for e in sorted_entries[:10]
        ]
        
        # Large transactions (top 10 by amount)
        large_transactions_sorted = sorted(
            large_transactions_list,
            key=lambda e: float(e.amount),
            reverse=True
        )[:10]
        large_transactions = [
            TransactionDTO(
                date=e.date.isoformat(),
                amount=float(e.amount),
                description=e.description,
                category=e.category or "Uncategorized",
                project=e.project
            )
            for e in large_transactions_sorted
        ]
        
        return BudgetContextDTO(
            total_expenses=total,
            entry_count=len(entries),
            categories=dict(top_categories),
            projects=dict(top_projects),
            all_categories=list(categories.keys()),
            all_projects=list(projects.keys()),
            date_range=date_range,
            average_expense=total / len(entries) if entries else 0,
            recent_transactions=recent_transactions,
            large_transactions=large_transactions,
            top_merchants=top_merchants
        )
    
    async def generate_response(self, message: str, conversation_history: List[Dict[str, str]] = []) -> str:
        """
        Generate AI response based on user message and budget context.
        Uses LLM if available, otherwise heuristic fallback.
        """
        context = await self.get_budget_context()
        
        # If LLM Provider is available, use it
        if self.llm_provider:
            # Format context as string/JSON for the LLM
            # Include enhanced context but keep it concise to manage token usage
            context_dict = {
                "summary": {
                    "total_expenses": context.total_expenses,
                    "entry_count": context.entry_count,
                    "average_transaction": context.average_expense,
                    "date_range": context.date_range.model_dump() if context.date_range else None
                },
                "top_categories": context.categories,
                "top_projects": context.projects,
                "top_merchants": context.top_merchants,
                "recent_transactions": [t.model_dump() for t in context.recent_transactions],
                "large_transactions": [t.model_dump() for t in context.large_transactions],
                "all_categories": context.all_categories,
                "all_projects": context.all_projects
            }
            context_str = json.dumps(context_dict, indent=2)
            
            return await self.llm_provider.generate_response(message, context_str, conversation_history)

        # --- Fallback Heuristic Logic ---
        message_lower = message.lower()
        
        if context.entry_count == 0:
            return "I don't see any budget data uploaded yet. Please upload a budget file to get started."
        
        responses = []
        
        if any(word in message_lower for word in ["total", "spent", "spending", "expenses", "cost"]):
            total = context.total_expenses
            responses.append(f"Your total expenses are **${total:,.2f}** across {context.entry_count} transactions.")
            
        if any(word in message_lower for word in ["category", "categories"]):
            if context.categories:
                top_cats = list(context.categories.items())[:3]
                cat_list = ", ".join([f"{cat} (${amt:,.2f})" for cat, amt in top_cats])
                responses.append(f"Your top spending categories are: {cat_list}.")
        
        if not responses:
            total = context.total_expenses
            responses.append(f"You have {context.entry_count} transactions totaling **${total:,.2f}**. Ask me about categories or projects!")
        
        return "\n\n".join(responses)

    async def generate_response_stream(self, message: str, conversation_history: List[Dict[str, str]] = []) -> AsyncIterator[str]:
        """
        Generate a streaming AI response, yielding tokens as they are generated.
        Uses LLM streaming if available, otherwise simulates streaming for heuristic fallback.
        """
        context = await self.get_budget_context()
        
        # If LLM Provider is available, use streaming
        if self.llm_provider:
            # Format context as string/JSON for the LLM
            # Include enhanced context but keep it concise to manage token usage
            context_dict = {
                "summary": {
                    "total_expenses": context.total_expenses,
                    "entry_count": context.entry_count,
                    "average_transaction": context.average_expense,
                    "date_range": context.date_range.model_dump() if context.date_range else None
                },
                "top_categories": context.categories,
                "top_projects": context.projects,
                "top_merchants": context.top_merchants,
                "recent_transactions": [t.model_dump() for t in context.recent_transactions],
                "large_transactions": [t.model_dump() for t in context.large_transactions],
                "all_categories": context.all_categories,
                "all_projects": context.all_projects
            }
            context_str = json.dumps(context_dict, indent=2)
            
            async for token in self.llm_provider.generate_response_stream(message, context_str, conversation_history):
                yield token
            return

        # --- Fallback Heuristic Logic (simulated streaming) ---
        message_lower = message.lower()
        
        if context.entry_count == 0:
            response = "I don't see any budget data uploaded yet. Please upload a budget file to get started."
            # Simulate streaming by yielding in chunks
            for char in response:
                yield char
                await asyncio.sleep(0.01)  # Small delay to simulate streaming
            return
        
        responses = []
        
        if any(word in message_lower for word in ["total", "spent", "spending", "expenses", "cost"]):
            total = context.total_expenses
            responses.append(f"Your total expenses are **${total:,.2f}** across {context.entry_count} transactions.")
        
        if any(word in message_lower for word in ["category", "categories"]):
            if context.categories:
                top_cats = list(context.categories.items())[:3]
                cat_list = ", ".join([f"{cat} (${amt:,.2f})" for cat, amt in top_cats])
                responses.append(f"Your top spending categories are: {cat_list}.")
        
        if not responses:
            total = context.total_expenses
            responses.append(f"You have {context.entry_count} transactions totaling **${total:,.2f}**. Ask me about categories or projects!")
        
        full_response = "\n\n".join(responses)
        # Simulate streaming by yielding in chunks
        for char in full_response:
            yield char
            await asyncio.sleep(0.01)  # Small delay to simulate streaming