import asyncio
import json
from decimal import Decimal
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
    
    file_path = "sample_budget.xlsx"
    with open(file_path, "rb") as f:
        content = f.read()
        
    print(f"Executing UploadBudgetUseCase with {file_path}...")
    result = await use_case.execute(content)
    
    print("\n--- RAW RESULT ---")
    print(result)
    
    total = result.get("total_expenses")
    print(f"\nTotal type: {type(total)}")
    print(f"Total value: {total}")
    
    # Simulate JSON dump (FastAPI behavior)
    try:
        # Standard json doesn't support Decimal, but default=str mimics Pydantic's string mode
        json_output = json.dumps(result, default=str, indent=2)
        print("\n--- JSON OUTPUT (Simulated) ---")
        print(json_output)
    except Exception as e:
        print(f"\nJSON Serialization Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
