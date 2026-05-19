from fastapi import FastAPI, Depends, Query, Path
from sqlalchemy.orm import Session
from . import schemas, services
from .database import get_db
from . import models

app = FastAPI(title='API организационной структуры', version='1.0.0')

@app.get('/')
def root():
    return {'status': 'ok'}

# ---- Department Endpoints ----
@app.post('/departments/', response_model=schemas.DepartmentResponse, status_code=201)
def create_department(data: schemas.DepartmentCreate, db: Session = Depends(get_db)):
    return services.create_department(db, data)

@app.get('/departments/{dep_id}', response_model=schemas.DepartmentTreeResponse)
def get_department(
    dep_id: int = Path(..., description='ID подразделения'),
    depth: int = Query(1, ge=1, le=5, description='Глубина вложенности'),
    include_employees: bool = Query(True, description='Включать ли сотрудников'),
    db: Session = Depends(get_db)
):
    return services.get_department_tree(db, dep_id, depth, include_employees)

@app.patch('/departments/{dep_id}', response_model=schemas.DepartmentResponse)
def update_department(dep_id: int, data: schemas.DepartmentUpdate, db: Session = Depends(get_db)):
    return services.update_department(db, dep_id, data)

@app.delete('/departments/{dep_id}', status_code=204)
def delete_department(
    dep_id: int,
    mode: str = Query(..., regex="^(cascade|reassign)$"),
    reassign_to_department_id: int = Query(None),
    db: Session = Depends(get_db)
):
    services.delete_department(db, dep_id, mode, reassign_to_department_id)

# ---- Employee Endpoint -------

@app.post('/departments/{dep_id}/employees/', response_model=schemas.EmployeeResponse, status_code=201)
def create_employee(dep_id: int, data: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    dep = services._check_department(db, dep_id)
    emp = models.Employee(
        department_id=dep.id,
        full_name=data.full_name,
        position=data.position,
        hired_at=data.hired_at
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp