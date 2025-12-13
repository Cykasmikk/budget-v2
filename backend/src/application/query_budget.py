from typing import List, Dict, Any
import re
from src.domain.repository import BudgetRepository
from src.application.dtos import QueryResultDTO

class QueryBudgetUseCase:
    def __init__(self, repo: BudgetRepository):
        self.repo = repo

    async def execute(self, query: str) -> QueryResultDTO:
        """
        Processes a natural language query and returns an answer.
        
        Supported intents:
        - Total spend: "total", "spend", "spent"
        - Category spend: "on [Category]"
        - Merchant spend: "at [Merchant]"
        """
        entries = await self.repo.get_all()
        query = query.lower()
        
        # Intent: Total Spend
        if "total" in query or query == "how much did i spend":
            total = sum(e.amount for e in entries)
            return QueryResultDTO(
                answer=f"You have spent a total of ${total:,.2f}.",
                type="total",
                data={"total": float(total)}
            )
            
        # Intent: Spend by Category
        # Look for "on [word]"
        category_match = re.search(r"on\s+(\w+)", query)
        if category_match:
            category = category_match.group(1)
            # Fuzzy match category
            total = 0
            found = False
            for e in entries:
                if category.lower() in e.category.lower():
                    total += e.amount
                    found = True
            
            if found:
                return QueryResultDTO(
                    answer=f"You spent ${total:,.2f} on {category}.",
                    type="category",
                    data={"category": category, "total": float(total)}
                )
        
        # Intent: Spend by Merchant
        # Look for "at [word]"
        merchant_match = re.search(r"at\s+(\w+)", query)
        if merchant_match:
            merchant = merchant_match.group(1)
            total = 0
            found = False
            for e in entries:
                if merchant.lower() in e.description.lower():
                    total += e.amount
                    found = True
            
            if found:
                return QueryResultDTO(
                    answer=f"You spent ${total:,.2f} at {merchant}.",
                    type="merchant",
                    data={"merchant": merchant, "total": float(total)}
                )

        return QueryResultDTO(
            answer="I didn't understand that. Try asking 'How much did I spend on Food?' or 'How much at Uber?'",
            type="unknown",
            data={}
        )
