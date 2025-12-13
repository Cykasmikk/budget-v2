import pytest
import pandas as pd
import io
from datetime import date
from decimal import Decimal
from src.infrastructure.excel_parser import PandasExcelParser

def test_excel_parser_parse():
    # Create a sample Excel file in memory
    data = {
        "Date": [date(2025, 1, 1), date(2025, 1, 2)],
        "Category": ["Food", "Transport"],
        "Amount": [10.50, 5.00],
        "Description": ["Lunch", "Bus"]
    }
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    file_content = output.getvalue()
    
    # Initialize Parser
    parser = PandasExcelParser()
    
    # Execute
    entries = parser.parse(file_content)
    
    # Verify
    assert len(entries) == 2
    assert entries[0].date == date(2025, 1, 1)
    assert entries[0].category == "Food"
    assert entries[0].amount == Decimal("10.50")
    assert entries[0].description == "Lunch"
