from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base


Base = declarative_base()

class Department(Base):
    __tablename__ = 'departments'
    __table_args__ = (
        UniqueConstraint('parent_id', 'name', name='uq_department_parent_name'),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200),nullable=False)
    parent_id = Column(Integer, ForeignKey('departments.id', ondelete='CASCADE'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    parent = relationship('Department', remote_side=[id], backref='children')
    employees = relationship('Employee', back_populates='department', cascade='all, delete-orphan',
                             passive_deletes=True)


class Employee(Base):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)
    full_name = Column(String(200), nullable=False)
    position = Column(String(200), nullable=False)
    hired_at = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    department = relationship('Department', back_populates='employees')