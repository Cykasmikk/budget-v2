from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.infrastructure.models import BudgetModel
from src.domain.user import User

class AIChatService:
    """
    AI Chat Service that provides contextually aware responses about budget data.
    This is a basic implementation that can be extended with actual LLM integration.
    """
    
    def __init__(self, session: AsyncSession, user: User):
        self.session = session
        self.user = user
    
    async def get_budget_context(self) -> Dict[str, Any]:
        """Gather budget data context for the AI"""
        # Get all budget entries for the user's tenant
        stmt = select(BudgetModel).where(BudgetModel.tenant_id == self.user.tenant_id)
        result = await self.session.execute(stmt)
        entries = result.scalars().all()
        
        if not entries:
            return {
                "total_expenses": 0,
                "entry_count": 0,
                "categories": {},
                "projects": {},
                "date_range": None
            }
        
        # Calculate summary statistics
        total = sum(float(e.amount) for e in entries)
        categories = {}
        projects = {}
        dates = []
        
        for entry in entries:
            # Category breakdown
            cat = entry.category or "Uncategorized"
            categories[cat] = categories.get(cat, 0) + float(entry.amount)
            
            # Project breakdown
            proj = entry.project or "No Project"
            projects[proj] = projects.get(proj, 0) + float(entry.amount)
            
            # Date range
            if entry.date:
                dates.append(entry.date)
        
        dates.sort()
        date_range = {
            "earliest": dates[0].isoformat() if dates else None,
            "latest": dates[-1].isoformat() if dates else None
        }
        
        # Top categories and projects
        top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
        top_projects = sorted(projects.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_expenses": total,
            "entry_count": len(entries),
            "categories": dict(top_categories),
            "projects": dict(top_projects),
            "all_categories": list(categories.keys()),
            "all_projects": list(projects.keys()),
            "date_range": date_range,
            "average_expense": total / len(entries) if entries else 0
        }
    
    async def generate_response(self, message: str, conversation_history: List[Dict[str, str]]) -> str:
        """
        Generate AI response based on user message and budget context.
        This is a basic implementation - can be replaced with actual LLM.
        """
        context = await self.get_budget_context()
        message_lower = message.lower()
        
        # Check if user has no data
        if context["entry_count"] == 0:
            return "I don't see any budget data uploaded yet. Please upload a budget file to get started, and I'll be able to help you analyze your spending patterns, answer questions about your expenses, and provide insights!"
        
        # Handle different types of questions
        responses = []
        
        # Total spending questions
        if any(word in message_lower for word in ["total", "spent", "spending", "expenses", "cost"]):
            total = context["total_expenses"]
            responses.append(f"Your total expenses are **${total:,.2f}** across {context['entry_count']} transactions.")
            
            if context["date_range"]["earliest"]:
                responses.append(f"Data spans from {context['date_range']['earliest']} to {context['date_range']['latest']}.")
        
        # Category questions
        if any(word in message_lower for word in ["category", "categories", "what categories", "which category"]):
            if context["categories"]:
                top_cats = list(context["categories"].items())[:3]
                cat_list = ", ".join([f"{cat} (${amt:,.2f})" for cat, amt in top_cats])
                responses.append(f"Your top spending categories are: {cat_list}.")
        
        # Project questions
        if any(word in message_lower for word in ["project", "projects", "what projects"]):
            if context["projects"]:
                top_projs = list(context["projects"].items())[:3]
                proj_list = ", ".join([f"{proj} (${amt:,.2f})" for proj, amt in top_projs])
                responses.append(f"Your top projects by spending are: {proj_list}.")
        
        # Specific category/project lookup
        for category in context["all_categories"]:
            if category.lower() in message_lower:
                amount = context["categories"].get(category, 0)
                responses.append(f"You've spent **${amount:,.2f}** on {category}.")
                break
        
        for project in context["all_projects"]:
            if project.lower() in message_lower:
                amount = context["projects"].get(project, 0)
                responses.append(f"Project '{project}' has expenses totaling **${amount:,.2f}**.")
                break
        
        # Average spending
        if any(word in message_lower for word in ["average", "avg", "mean"]):
            avg = context["average_expense"]
            responses.append(f"Your average transaction amount is **${avg:,.2f}**.")
        
        # Help/guidance
        if any(word in message_lower for word in ["help", "what can you", "how can you", "what do you"]):
            responses.append("I can help you with:")
            responses.append("• Total spending and expense summaries")
            responses.append("• Category and project breakdowns")
            responses.append("• Specific spending questions about categories or projects")
            responses.append("• Budget analysis and insights")
            responses.append("\nJust ask me questions about your budget data!")
        
        # Default response if no specific pattern matched
        if not responses:
            # Try to provide a helpful general response
            total = context["total_expenses"]
            top_cat = list(context["categories"].items())[0] if context["categories"] else None
            
            responses.append(f"Based on your budget data, you have {context['entry_count']} transactions totaling **${total:,.2f}**.")
            if top_cat:
                responses.append(f"Your largest spending category is {top_cat[0]} at ${top_cat[1]:,.2f}.")
            responses.append("\nYou can ask me about specific categories, projects, totals, or averages. What would you like to know?")
        
        return "\n\n".join(responses)

