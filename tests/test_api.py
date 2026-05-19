from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import pytest

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/org_db")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_db():
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM employees"))
        conn.execute(text("DELETE FROM departments"))
        # Сбрасываем последовательности, чтобы id начинались с 1
        conn.execute(text("ALTER SEQUENCE employees_id_seq RESTART WITH 1"))
        conn.execute(text("ALTER SEQUENCE departments_id_seq RESTART WITH 1"))
        conn.commit()

def test_create_root_department():
    resp = client.post("/departments/", json={"name": "Head Office"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Head Office"
    assert data["parent_id"] is None

def test_create_child_department():
    parent_resp = client.post("/departments/", json={"name": "Parent"})
    parent_id = parent_resp.json()["id"]
    resp = client.post("/departments/", json={"name": "Child", "parent_id": parent_id})
    assert resp.status_code == 201
    data = resp.json()
    assert data["parent_id"] == parent_id

def test_create_duplicate_name_same_parent():
    client.post("/departments/", json={"name": "Unique"})
    resp = client.post("/departments/", json={"name": "Unique"})
    assert resp.status_code == 400
    assert "уже существует" in resp.json()["detail"]

def test_create_department_nonexistent_parent():
    resp = client.post("/departments/", json={"name": "Orphan", "parent_id": 999})
    assert resp.status_code == 404

def test_create_employee():
    dep_resp = client.post("/departments/", json={"name": "IT"})
    dep_id = dep_resp.json()["id"]
    resp = client.post(f"/departments/{dep_id}/employees/", json={"full_name": "Ivan", "position": "Dev"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["full_name"] == "Ivan"
    assert data["department_id"] == dep_id

def test_get_department_tree():
    root_resp = client.post("/departments/", json={"name": "Root"})
    root_id = root_resp.json()["id"]
    branch_resp = client.post("/departments/", json={"name": "Branch", "parent_id": root_id})
    branch_id = branch_resp.json()["id"]
    client.post(f"/departments/{branch_id}/employees/", json={"full_name": "E", "position": "P"})
    resp = client.get(f"/departments/{root_id}?depth=2&include_employees=true")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["children"]) == 1
    assert len(data["children"][0]["employees"]) == 1

def test_move_creates_cycle():
    a_resp = client.post("/departments/", json={"name": "A"})
    a_id = a_resp.json()["id"]
    b_resp = client.post("/departments/", json={"name": "B", "parent_id": a_id})
    b_id = b_resp.json()["id"]
    resp = client.patch(f"/departments/{a_id}", json={"parent_id": b_id})
    assert resp.status_code == 409

def test_cascade_delete():
    top_resp = client.post("/departments/", json={"name": "Top"})
    top_id = top_resp.json()["id"]
    sub_resp = client.post("/departments/", json={"name": "Sub", "parent_id": top_id})
    sub_id = sub_resp.json()["id"]
    client.post(f"/departments/{sub_id}/employees/", json={"full_name": "X", "position": "Y"})
    resp = client.delete(f"/departments/{sub_id}?mode=cascade")
    assert resp.status_code == 204
    # Проверяем, что дочернее подразделение удалено
    check_resp = client.get(f"/departments/{top_id}?depth=1")
    data = check_resp.json()
    assert len(data["children"]) == 0