from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

# ------------------ Department ------------------
class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    parent_id: Optional[int] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()

class DepartmentUpdate(BaseModel):
    name: str = Field(None, min_length=1, max_length=200)
    parent_id: Optional[int] = None

    @field_validator('name')
    @classmethod
    def trim_name(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v


class DepartmentResponse(BaseModel):
    id: int
    name: str
    parent_id: Optional[int]
    created_at: datetime

    model_config = {'from_attributes': True}

class DepartmentTreeResponse(BaseModel):
    id: int
    name: str
    parent_id: Optional[int]
    created_at: datetime
    employees: List['EmployeeResponse'] = []
    children: List['DepartmentTreeResponse'] = []

    model_config = {'from_attributes': True}

# ------------------ Employee ------------------

class EmployeeCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    position: str = Field(..., min_length=1, max_length=200)
    hired_at: Optional[date] = None

    @field_validator('full_name','position')
    @classmethod
    def trim_str(cls, v: str) -> str:
        return v.strip()

class EmployeeResponse(BaseModel):
    id: int
    department_id: int
    full_name: str
    position: str
    hired_at: Optional[date]
    created_at: datetime

    model_config = {'from_attributes': True}