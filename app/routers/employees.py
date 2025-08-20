from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime
from typing import Optional

from ..database import get_db
from ..models import Employee, EmployeeStatus
from .. import schemas

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/employees", response_class=HTMLResponse)
def employees_list(
    request: Request, 
    q: Optional[str] = None,
    department: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Employee)
    
    if q:
        query = query.filter(or_(
            Employee.name.contains(q),
            Employee.employee_id.contains(q),
            Employee.name_kana.contains(q) if Employee.name_kana else False,
            Employee.email.contains(q) if Employee.email else False
        ))
    
    if department:
        query = query.filter(Employee.department.contains(department))
    
    if status:
        try:
            status_enum = EmployeeStatus(status)
            query = query.filter(Employee.status == status_enum)
        except ValueError:
            pass
    
    employees = query.order_by(Employee.employee_id).all()
    
    # Get unique departments for filter dropdown
    departments = db.query(Employee.department).filter(Employee.department.isnot(None)).distinct().all()
    departments = [dept[0] for dept in departments if dept[0]]
    
    return templates.TemplateResponse("employees_list.html", {
        "request": request,
        "employees": employees,
        "search_query": q or "",
        "department_filter": department or "",
        "status_filter": status or "",
        "departments": departments
    })

@router.get("/employees/new", response_class=HTMLResponse)
def employee_new_form(request: Request):
    return templates.TemplateResponse("employee_new.html", {"request": request})

@router.post("/employees/new")
def create_employee(
    request: Request,
    employee_id: str = Form(...),
    name: str = Form(...),
    name_kana: str = Form(""),
    email: str = Form(""),
    department: str = Form(""),
    position: str = Form(""),
    phone: str = Form(""),
    hire_date: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db)
):
    if not employee_id.strip() or not name.strip():
        return templates.TemplateResponse("employee_new.html", {
            "request": request,
            "error": "社員番号と氏名は必須です",
            "employee_id": employee_id,
            "name": name,
            "name_kana": name_kana,
            "email": email,
            "department": department,
            "position": position,
            "phone": phone,
            "hire_date": hire_date,
            "notes": notes
        })
    
    # Check for duplicate employee_id
    existing_employee = db.query(Employee).filter(Employee.employee_id == employee_id.strip()).first()
    if existing_employee:
        return templates.TemplateResponse("employee_new.html", {
            "request": request,
            "error": "この社員番号は既に存在します",
            "employee_id": employee_id,
            "name": name,
            "name_kana": name_kana,
            "email": email,
            "department": department,
            "position": position,
            "phone": phone,
            "hire_date": hire_date,
            "notes": notes
        })
    
    # Parse hire_date
    hire_date_obj = None
    if hire_date.strip():
        try:
            hire_date_obj = datetime.strptime(hire_date, "%Y-%m-%d")
        except ValueError:
            return templates.TemplateResponse("employee_new.html", {
                "request": request,
                "error": "入社日の形式が正しくありません (YYYY-MM-DD)",
                "employee_id": employee_id,
                "name": name,
                "name_kana": name_kana,
                "email": email,
                "department": department,
                "position": position,
                "phone": phone,
                "hire_date": hire_date,
                "notes": notes
            })
    
    db_employee = Employee(
        employee_id=employee_id.strip(),
        name=name.strip(),
        name_kana=name_kana.strip() if name_kana.strip() else None,
        email=email.strip() if email.strip() else None,
        department=department.strip() if department.strip() else None,
        position=position.strip() if position.strip() else None,
        phone=phone.strip() if phone.strip() else None,
        hire_date=hire_date_obj,
        notes=notes.strip() if notes.strip() else None
    )
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    
    return RedirectResponse(url=f"/employees/{db_employee.id}", status_code=303)

@router.get("/employees/{employee_id}", response_class=HTMLResponse)
def employee_detail(request: Request, employee_id: int, db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get loan history for this employee
    loans = db.query(employee.loans).order_by(employee.loans.checkout_at.desc()).all()
    
    # Get active reservations for this employee
    reservations = db.query(employee.reservations).filter(
        employee.reservations.status == "active"
    ).all()
    
    return templates.TemplateResponse("employee_detail.html", {
        "request": request,
        "employee": employee,
        "loans": loans,
        "reservations": reservations
    })

@router.get("/employees/{employee_id}/edit", response_class=HTMLResponse)
def employee_edit_form(request: Request, employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return templates.TemplateResponse("employee_edit.html", {
        "request": request,
        "employee": employee
    })

@router.post("/employees/{employee_id}/edit")
def update_employee(
    request: Request,
    employee_id: int,
    employee_id_field: str = Form(..., alias="employee_id"),
    name: str = Form(...),
    name_kana: str = Form(""),
    email: str = Form(""),
    department: str = Form(""),
    position: str = Form(""),
    phone: str = Form(""),
    hire_date: str = Form(""),
    status: str = Form("active"),
    notes: str = Form(""),
    db: Session = Depends(get_db)
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if not employee_id_field.strip() or not name.strip():
        return templates.TemplateResponse("employee_edit.html", {
            "request": request,
            "error": "社員番号と氏名は必須です",
            "employee": employee
        })
    
    # Check for duplicate employee_id (excluding current employee)
    existing_employee = db.query(Employee).filter(
        Employee.employee_id == employee_id_field.strip(),
        Employee.id != employee_id
    ).first()
    if existing_employee:
        return templates.TemplateResponse("employee_edit.html", {
            "request": request,
            "error": "この社員番号は既に存在します",
            "employee": employee
        })
    
    # Parse hire_date
    hire_date_obj = None
    if hire_date.strip():
        try:
            hire_date_obj = datetime.strptime(hire_date, "%Y-%m-%d")
        except ValueError:
            return templates.TemplateResponse("employee_edit.html", {
                "request": request,
                "error": "入社日の形式が正しくありません (YYYY-MM-DD)",
                "employee": employee
            })
    
    # Update employee fields
    employee.employee_id = employee_id_field.strip()
    employee.name = name.strip()
    employee.name_kana = name_kana.strip() if name_kana.strip() else None
    employee.email = email.strip() if email.strip() else None
    employee.department = department.strip() if department.strip() else None
    employee.position = position.strip() if position.strip() else None
    employee.phone = phone.strip() if phone.strip() else None
    employee.hire_date = hire_date_obj
    employee.status = EmployeeStatus(status)
    employee.notes = notes.strip() if notes.strip() else None
    employee.updated_at = datetime.utcnow()
    
    db.commit()
    
    return RedirectResponse(url=f"/employees/{employee_id}", status_code=303)

# API endpoints for dropdown population
@router.get("/api/employees")
def get_employees_api(status: str = "active", db: Session = Depends(get_db)):
    query = db.query(Employee).filter(Employee.status == EmployeeStatus(status))
    employees = query.order_by(Employee.employee_id).all()
    return [{"id": emp.id, "employee_id": emp.employee_id, "name": emp.name, "department": emp.department} for emp in employees]

@router.get("/api/employees/active")
def get_active_employees_api(db: Session = Depends(get_db)):
    employees = db.query(Employee).filter(Employee.status == EmployeeStatus.active).order_by(Employee.employee_id).all()
    return [{"id": emp.id, "employee_id": emp.employee_id, "name": emp.name, "department": emp.department} for emp in employees]