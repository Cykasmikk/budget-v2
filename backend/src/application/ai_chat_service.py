from typing import List, Dict, Optional, AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.infrastructure.models import BudgetModel
from src.domain.user import User
from src.application.dtos import BudgetContextDTO, DateRangeDTO, TransactionDTO
from src.application.ports import LLMProvider
import re
import asyncio
import json
from src.application.ai.explanation_service import ExplanationService
from src.application.neuro_symbolic.hybrid_reasoner import HybridReasoner
from src.application.ai.response_verifier import ResponseVerifier

class AIChatService:
    """
    AI Chat Service that provides contextually aware responses about budget data.
    """
    
    def __init__(self, session: AsyncSession, user: User, llm_provider: Optional[LLMProvider] = None, 
                 explanation_service: Optional[ExplanationService] = None,
                 hybrid_reasoner: Optional[HybridReasoner] = None,
                 response_verifier: Optional[ResponseVerifier] = None):
        self.session = session
        self.user = user
        self.llm_provider = llm_provider
        self.explanation_service = explanation_service
        self.hybrid_reasoner = hybrid_reasoner
        self.verifier = response_verifier
    
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
        
        # Filter for expenses (exclude transfers, payments, income)
        # This matches the logic in analyze_budget.py
        exclude_categories = {"Payment", "Transfer", "Income", "Credit Card Payment", "Opening Balance"}
        expense_entries = [e for e in entries if e.category not in exclude_categories]
        
        # Calculate summary statistics using absolute values
        total = sum(abs(float(e.amount)) for e in expense_entries)
        categories = {}
        projects = {}
        merchants = {}
        monthly_map = {}
        dates = []
        large_transactions_list = []
        
        for entry in expense_entries:
            amount = abs(float(entry.amount))
            
            # Category breakdown
            cat = entry.category or "Uncategorized"
            categories[cat] = categories.get(cat, 0) + amount
            
            # Project breakdown
            proj = entry.project or "No Project"
            projects[proj] = projects.get(proj, 0) + amount
            
            # Merchant extraction (from description)
            merchant = self._extract_merchant(entry.description)
            merchants[merchant] = merchants.get(merchant, 0) + amount
            
            # Monthly breakdown (YYYY-MM)
            if entry.date:
                month_key = entry.date.strftime("%Y-%m")
                monthly_map[month_key] = monthly_map.get(month_key, 0) + amount
                dates.append(entry.date)

            # Large transactions (> $500)
            if amount > 500:
                large_transactions_list.append(entry)
        
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
            entry_count=len(expense_entries),
            # CRITICAL: Pass FULL maps for VerificationService. 
            # We will slice them for the LLM context string in generate_response.
            categories=categories,
            projects=projects,
            all_categories=list(categories.keys()),
            all_projects=list(projects.keys()),
            all_merchants=list(merchants.keys()),
            monthly_summary=monthly_map,
            date_range=date_range,
            average_expense=total / len(expense_entries) if expense_entries else 0,
            recent_transactions=recent_transactions,
            large_transactions=large_transactions,
            top_merchants=top_merchants
        )
    
    async def generate_response(self, message: str, conversation_history: List[Dict[str, str]] = []) -> tuple[str, str]:
        """
        Generate AI response based on user message and budget context.
        Uses LLM if available, otherwise heuristic fallback.
        """
        context = await self.get_budget_context()

        # --- Intent: Explanation ---
        # "Why is Netflix Entertainment?" or "Explain Netflix"
        explain_match = re.search(r"(why is|explain)\s+(.+?)(\?|$| classified)", message.lower())
        if explain_match and self.explanation_service and self.hybrid_reasoner:
            target = explain_match.group(2).strip()
            # 1. Run Reasoner
            result = await self.hybrid_reasoner.refine_prediction(target, rules=[])
            # 2. Explain
            explanation_data = await self.explanation_service.generate_explanation(result, {"description": target})
            
            # Format as text response
            proof_steps = "\n".join([f"- {step}" for step in explanation_data['proof']['steps']])
            response_text = f"**Classification Analysis for '{target}'**\n\n" \
                            f"**Predicted Category:** {explanation_data['decision']} ({explanation_data['confidence']*100:.1f}%)\n\n" \
                            f"**Reasoning Trace:**\n{proof_steps}"
            
            # TODO: We could return the raw explanation dict if we support structured ChatMessage 
            # (which we added validation for in frontend).
            # But the 'explanation' field in frontend is for "Trace", content is usually markdown.
            # We can put the proof trace IN the 'explanation' meta field of the return tuple?
            
            full_trace = json.dumps(explanation_data['proof'], indent=2)
            return response_text, full_trace
        
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
                # Slice logic moved here to support Full Verification Map in DTO
                "top_categories": dict(sorted(context.categories.items(), key=lambda x: x[1], reverse=True)[:5]),
                "top_projects": dict(sorted(context.projects.items(), key=lambda x: x[1], reverse=True)[:5]),
                "top_merchants": context.top_merchants,
                "recent_transactions": [t.model_dump() for t in context.recent_transactions],
                "large_transactions": [t.model_dump() for t in context.large_transactions],
                "all_categories": context.all_categories,
                "all_projects": context.all_projects
            }
            context_str = json.dumps(context_dict, indent=2)
            
            response = await self.llm_provider.generate_response(message, context_str, conversation_history)
            
            # --- Verification Layer ---
            verification_trace = ""
            final_response = response
            
            if self.verifier:
                result = self.verifier.verify_response(response, context)
                if not result.is_valid:
                    final_response = result.corrected_text
                    verification_trace = f"\n\n**Verification Correction:** Corrected {len([t for t in result.trace if t['status']=='failed'])} claim(s)."
                
                # Always append trace in debug/explanation if needed
                # For now, we append it to the explanation string
                verification_details = json.dumps(result.trace, indent=2)
                full_explanation = f"Generated by Google Gemini Flash 2.0.\nVerified by Neuro-Symbolic Logic.\nTrace: {verification_details}"
            else:
                full_explanation = "Generated by Google Gemini Flash 2.0 with strict context injection."

            return final_response, full_explanation

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
        
        return "\n\n".join(responses), f"Symbolic Trace: Analyzed {context.entry_count} transactions via deterministic SQL filters."

    async def generate_response_stream(self, message: str, conversation_history: List[Dict[str, str]] = []) -> AsyncIterator[str]:
        """
        Generate a streaming AI response, yielding tokens as they are generated.
        Uses LLM streaming if available, otherwise simulates streaming for heuristic fallback.
        """
        context = await self.get_budget_context()
        
        # If LLM Provider is available, use streaming
        # CRITICAL: Buffered Verification for raw stream too.
        if self.llm_provider:
            full_response, _ = await self.generate_response(message, conversation_history)
            
            for char in full_response:
                yield char
                await asyncio.sleep(0.005)
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
            
    async def generate_response_stream_with_meta(self, message: str, conversation_history: List[Dict[str, str]] = []) -> AsyncIterator[Dict[str, str]]:
        """
        Generate streaming response yielding dicts: {'type': 'token', 'content': '...'} or {'type': 'explanation', 'content': '...'}
        """
        context = await self.get_budget_context()
        explanation = f"Symbolic Trace: Analyzed {context.entry_count} transactions via deterministic SQL filters."
        
        # If LLM Provider is available, use streaming
        # If LLM Provider is available, use streaming
        # CRITICAL: For 100% Accuracy, we must use "Buffered Verification"
        # We cannot stream the raw LLM output because we must verify it first.
        # So we generate the full verified response, then stream it back to the client.
        if self.llm_provider:
             # Call the Main pipeline which uses the Verifier
             full_response, explanation = await self.generate_response(message, conversation_history)
             
             # Stream the VERIFIED text
             for char in full_response:
                 yield {'type': 'token', 'content': char}
                 # Tiny delay to simulate streaming feel if connection is too fast, 
                 # or just yield fast. 0.005 is subtle.
                 await asyncio.sleep(0.005)
                 
             yield {'type': 'explanation', 'content': explanation}
             return

        # --- Fallback Heuristic Logic (simulated streaming) ---
        message_lower = message.lower()
        
        response_text = ""
        if context.entry_count == 0:
            response_text = "I don't see any budget data uploaded yet. Please upload a budget file to get started."
        else:
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
            
            response_text = "\n\n".join(responses)

        # Simulate streaming
        for char in response_text:
            yield {'type': 'token', 'content': char}
            await asyncio.sleep(0.01)
            
        yield {'type': 'explanation', 'content': explanation}