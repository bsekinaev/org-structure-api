from typing import Optional, Dict
from fastapi import HTTPException
from sqlalchemy.orm import Session
from . import models


# ---- Вспомогательные функции ----
def _check_parent_exists(db: Session, parent_id: int):
    # Проверяет, что подразделение с указанным id существует, иначе 404
    if not db.query(models.Department).filter(models.Department.id == parent_id).first():
        raise HTTPException(status_code=404, detail="Родительское подразделение не найдено")

def _check_department(db: Session, dep_id: int) -> models.Department:
    dep = db.query(models.Department).filter(models.Department.id == dep_id).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Подразделение не найдено")
    return dep


def _check_unique_name_in_parent(db: Session, name: str, parent_id: Optional[int],exclude_id: Optional[int] = None):
    # Проверяем, что name уникален внутри одного родителя
    q = db.query(models.Department).filter(
        models.Department.name == name,
        models.Department.parent_id == parent_id
    )
    if exclude_id:
        q = q.filter(models.Department.id != exclude_id)
    if q.first():
        raise HTTPException(status_code=400,detail='Подразделение с таким именем уже существует в данном родителе')

def _would_create_cycle(db: Session, dep_id: int, new_parent_id: int) -> bool:
    # Проверяем, не создаст ли перемещение цикла
    if dep_id == new_parent_id:
        return True

    # Собираем всех предков new_parent_id
    ancestor = set()
    current_parent_id = new_parent_id
    while current_parent_id:
        ancestor.add(current_parent_id)
        parent = db.query(models.Department).filter(models.Department.id == current_parent_id).first()
        current_parent_id = parent.parent_id if parent else None
    return dep_id in ancestor


# ---- CRUD для Department --------
def create_department(db: Session, data):
    _check_unique_name_in_parent(db, data.name, data.parent_id)
    if data.parent_id is not None:
        _check_parent_exists(db, data.parent_id)
    dep = models.Department(name=data.name, parent_id=data.parent_id)
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return dep


def get_department_tree(db: Session, dep_id: int, depth:int = 1, include_employees:bool = True) -> Dict:
    dep = _check_department(db, dep_id)
    return _build_tree(db, dep, depth, include_employees)


def _build_tree(db: Session, dep: models.Department,
                max_depth:int = 1, include_employees:bool = True,
                current_depth:int = 0):
    result = {
        'id': dep.id,
        'name': dep.name,
        'parent_id': dep.parent_id,
        'created_at': dep.created_at,
        'employees': [],
        'children': [],
    }
    if include_employees:
        # Сортировка по created_at (или full_name)
        emps = sorted(dep.employees, key=lambda e: e.created_at)
        result['employees'] = [{
            'id': e.id,
            'department_id': e.department_id,
            'full_name': e.full_name,
            'position': e.position,
            'hired_at': e.hired_at,
            'created_at': e.created_at
        } for e in emps]
    if current_depth < max_depth:
        children = sorted(dep.children, key=lambda d: d.name)
        result['children'] = [_build_tree(db, child, max_depth, include_employees, current_depth + 1) for child in
                              children]
    return result

def update_department(db: Session, dep_id: int, data):
    dep = _check_department(db, dep_id)

    # Проверка уникальности имени
    if data.name is not None and data.name != dep.name:
        _check_unique_name_in_parent(db, data.name,
            data.parent_id if data.parent_id is not None else dep.parent_id,
            exclude_id=dep_id)

    # Проверка цикла при смене родителя
    if data.parent_id is not None:
        new_parent = data.parent_id
        if new_parent != dep.parent_id:
            _check_parent_exists(db, new_parent)
            if _would_create_cycle(db, dep_id, new_parent):
                raise HTTPException(status_code=409, detail="Перемещение создаст цикл в дереве подразделений")
            dep.parent_id = new_parent

    if data.name is not None:
        dep.name = data.name

    db.commit()
    db.refresh(dep)
    return dep

def delete_department(db: Session, dep_id: int, mode: str, reassign_to: Optional[int] = None):
    dep = _check_department(db, dep_id)
    if mode == 'reassign':
        if reassign_to is None:
            raise HTTPException(status_code=400, detail='Не указан reassign_to_department_id')
        target_dep = _check_department(db, reassign_to)
        for emp in dep.employees:
            emp.department_id = target_dep.id
        db.delete(dep)   # удаляем после переноса всех сотрудников
    elif mode == 'cascade':
        db.delete(dep)
    else:
        raise HTTPException(status_code=400, detail='Неверный режим удаления')
    db.commit()
    return None
