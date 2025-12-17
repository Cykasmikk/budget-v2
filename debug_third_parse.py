import asyncio
import json
import os
from decimal import Decimal
# Mocking imports since we are running in root context
# We need to make sure PYTHONPATH is set to include ./backend
import sys
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from src.application.upload_budget import UploadBudgetUseCase
from src.application.analyze_budget import AnalyzeBudgetUseCase
from src.infrastructure.excel_parser import PandasExcelParser
from src.domain.repository import BudgetRepository
from src.domain.budget import BudgetEntry

class MockRepo(BudgetRepository):
    async def save(self, entry: BudgetEntry): pass
    async def get_all(self): return []
    async def get_by_category(self, category: str): return []
    async def save_bulk(self, entries): pass
    async def clear(self): pass

async def main():
    repo = MockRepo()
    parser = PandasExcelParser()
    analyzer = AnalyzeBudgetUseCase(repo)
    use_case = UploadBudgetUseCase(repo, parser, analyzer)
    
    file_path = "third_sample_budget.xlsx"
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    with open(file_path, "rb") as f:
        content = f.read()
        
    print(f"Executing UploadBudgetUseCase with {file_path}...")
    result = await use_case.execute(content)
    
    print("\n--- RAW RESULT ---")
    print(result)
    
    total = result.get("total_expenses")
    print(f"\nTotal type: {type(total)}")
    print(f"Total value: {total}")

    trend = result.get("monthly_trend", [])
    print(f"\nMonthly Trend Length: {len(trend)}")
    if trend:
        print(f"First Trend Item: {trend[0]}")

if __name__ == "__main__":
    asyncio.run(main())
