import pytest
from unittest.mock import Mock, AsyncMock
from src.domain.budget import BudgetEntry
from src.application.upload_budget import UploadBudgetUseCase
from datetime import date
from decimal import Decimal

@pytest.mark.asyncio
async def test_upload_budget_use_case():
    # Mock dependencies
    mock_repo = AsyncMock()
    mock_parser = Mock()
    
    # Setup mock parser return value
    mock_entries = [
        BudgetEntry(date=date(2025, 1, 1), category="Food", amount=Decimal("10.0"), description="Lunch"),
        BudgetEntry(date=date(2025, 1, 2), category="Transport", amount=Decimal("5.0"), description="Bus")
    ]
    mock_parser.parse.return_value = mock_entries
    
    # Initialize Use Case
    use_case = UploadBudgetUseCase(repo=mock_repo, parser=mock_parser)
    
    # Execute
    file_content = b"fake_excel_content"
    result = await use_case.execute(file_content)
    
    # Verify
    mock_parser.parse.assert_called_once_with(file_content)
    mock_repo.save_bulk.assert_called_once_with(mock_entries)
    assert result == {"count": 2, "status": "success"}
