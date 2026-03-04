from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.project import Project, ProjectStatus
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.setting_service import setting_service

router = APIRouter()

@router.get("/", response_model=List[ProjectResponse])
def read_projects(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve projects.
    """
    projects = db.query(Project).offset(skip).limit(limit).all()
    return projects

@router.post("/", response_model=ProjectResponse)
def create_project(
    *,
    db: Session = Depends(get_db),
    project_in: ProjectCreate,
) -> Any:
    """
    Create new project.
    """
    project = Project(**project_in.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.put("/{id}", response_model=ProjectResponse)
def update_project(
    *,
    db: Session = Depends(get_db),
    id: int,
    project_in: ProjectUpdate,
) -> Any:
    """
    Update a project.
    """
    project = db.query(Project).filter(Project.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
        
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # KPI Trigger: If status changed to DONE, award points
    if "status" in update_data and update_data["status"] == ProjectStatus.DONE:
        project_points = float(setting_service.get_int(db, "kpi_project_done_points", 100))
        kpi_service.log_event(
            db=db,
            user_id=1,  # Placeholder
            event_type="PROJECT_COMPLETED",
            points=project_points,
            reference_id=str(project.id),
            description=f"Completed Project: {project.title}"
        )
        # Bonus for large projects (>10kWp)
        if project.system_size_kwp > 10.0:
            bonus_points = float(setting_service.get_int(db, "kpi_large_project_bonus", 20))
            kpi_service.log_event(
                db=db,
                user_id=1,
                event_type="LARGE_PROJECT_BONUS",
                points=bonus_points,
                reference_id=str(project.id),
                description=f"Bonus for large project (>10kWp): {project.title}"
            )

    return project

@router.delete("/{id}")
def delete_project(
    *,
    db: Session = Depends(get_db),
    id: int,
) -> Any:
    """
    Delete a project.
    """
    project = db.query(Project).filter(Project.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"ok": True}
