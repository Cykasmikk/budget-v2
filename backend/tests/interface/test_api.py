import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
import pandas as pd
from io import BytesIO
from datetime import date

from src.infrastructure.db import init_db
import os

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_upload_and_analysis():
    # Initialize DB
    await init_db()
    
    # Create a dummy Excel file
    df = pd.DataFrame({
        'Date': [date(2025, 1, 1), date(2025, 1, 2)],
        'Category': ['Food', 'Transport'],
        'Amount': [10.50, 5.00],
        'Description': ['Lunch', 'Bus']
    })
    
    file_content = BytesIO()
    with pd.ExcelWriter(file_content, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    file_content.seek(0)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Upload
        files = {'file': ('test.xlsx', file_content, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = await ac.post("/api/v1/upload", files=files)
        if response.status_code != 200:
            assert False, f"Request failed: {response.text}"
        assert response.status_code == 200
        assert response.json()['count'] == 2
        
        # Analysis
        response = await ac.get("/api/v1/analysis")
        assert response.status_code == 200
        data = response.json()
        assert data['total_expenses'] == 15.5
        assert data['category_breakdown']['Food'] == 10.5
        assert data['category_breakdown']['Transport'] == 5.0
