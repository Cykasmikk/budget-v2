import pytest
import pandas as pd
import uuid
from io import BytesIO
from datetime import date, datetime
from src.main import app
from src.interface.dependencies import get_current_user
from src.application.context import set_tenant_id
from src.domain.user import User, UserRole

@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_upload_and_analysis(client):
    # Override Auth
    tenant_id = uuid.uuid4()
    
    async def mock_get_current_user():
        set_tenant_id(tenant_id)
        # Return object, not dict
        return User(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            email="test@example.com",
            role=UserRole.ADMIN,
            created_at=datetime.now()
        )
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    # Create a dummy Excel file
    df = pd.DataFrame({
        'Date': [date(2025, 1, 1), date(2025, 1, 2)],
        'Category': ['Food', 'Transport'],
        'Amount': [10.50, 5.00],
        'Description': ['Lunch', 'Bus'],
        'Project': ['Personal', 'Work'] # Added Project column to match schema
    })
    
    file_content = BytesIO()
    with pd.ExcelWriter(file_content, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    file_content.seek(0)
    
    # Upload
    files = [('files', ('test.xlsx', file_content, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))]
    response = await client.post("/api/v1/upload", files=files)
    
    if response.status_code != 200:
        assert False, f"Request failed: {response.text}"
    
    json_resp = response.json()
    assert 'data' in json_resp
    assert float(json_resp['data']['total_expenses']) == 15.5
    
    # Analysis
    response = await client.get("/api/v1/analysis")
    assert response.status_code == 200
    json_resp = response.json()
    assert 'data' in json_resp
    data = json_resp['data']
    assert float(data['total_expenses']) == 15.5
    assert float(data['category_breakdown']['Food']) == 10.5
    assert float(data['category_breakdown']['Transport']) == 5.0
    
    app.dependency_overrides.pop(get_current_user, None)
