import pytest
import pandas as pd
import io
from httpx import AsyncClient
from src.main import app
from src.infrastructure.db import get_session
from src.domain.repository import BudgetRepository
from src.infrastructure.repository import SQLBudgetRepository
from sqlalchemy.ext.asyncio import AsyncSession

# We need to recreate the generation logic or just read the file to get exact expected values
# For this test, we accept the file exists on disk from the previous step.

from src.interface.dependencies import get_current_user
from src.application.context import set_tenant_id
from uuid import uuid4

@pytest.mark.asyncio
async def test_multisheet_upload_accuracy(client: AsyncClient, db_session: AsyncSession):
    # Mock User and Context
    fake_tenant_id = uuid4()
    set_tenant_id(fake_tenant_id)
    app.dependency_overrides[get_current_user] = lambda: {"id": "test-user", "email": "test@example.com", "role": "admin", "tenant_id": str(fake_tenant_id)}

    
    # 1. Read the file source of truth
    # We use pandas to sum it up independently to verify our backend parser matches pandas
    file_path = "sample_budget.xlsx" # Working dir is root in tests? or we need absolute? 
    # In CI/Test environment, we assume the file was just generated in the root.
    # We might need to adjust path if running from backend/ dir.
    # For now, let's try reading absolute path or relative to project root
    
    import os
    if not os.path.exists(file_path):
        file_path = "../sample_budget.xlsx" # Try one up
        
    print(f"Reading verification file from: {os.path.abspath(file_path)}")
    
    # Independent verification sum
    all_sheets = pd.read_excel(file_path, sheet_name=None)
    expected_total = 0.0
    for sheet_name, df in all_sheets.items():
        if "Amount" in df.columns:
            expected_total += df["Amount"].sum()
            
    print(f"Expected Total (from Pandas): {expected_total}")

    # 2. Upload to Backend
    with open(file_path, "rb") as f:
        files = {'files': (file_path, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = await client.post("/api/v1/upload", files=files)
        
    assert response.status_code == 200, f"Upload failed: {response.text}"
    
    # 3. Fetch Analysis
    response = await client.get("/api/v1/analysis")
    assert response.status_code == 200
    data = response.json()
    
    backend_total = float(data["total_expenses"])
    print(f"Backend Total: {backend_total}")
    
    # 4. Assert Equality
    # Floating point tolerance
    assert abs(backend_total - expected_total) < 0.01, \
        f"Mismatch! Pandas said {expected_total}, Backend said {backend_total}"
    
    # 5. Verify Breakdown
    # All our generated data was "Cloud Infrastructure" category.
    # So category breakdown should have exactly one key with the full total.
    categories = data["category_breakdown"]
    assert "Cloud Infrastructure" in categories
    assert abs(float(categories["Cloud Infrastructure"]) - expected_total) < 0.01

    # 6. Verify Project Names (should handle "AWS Migration", "Azure Migration", etc.)
    projects = data["project_breakdown"]
    assert "AWS Migration" in projects
    assert "Azure Migration" in projects
    assert "GCP Migration" in projects
    
    print("✅ Multi-Sheet Data Integrity Verified")
