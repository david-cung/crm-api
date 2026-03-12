from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db.session import get_db
from app.models.project import Project, ProjectStatus, ProjectItem
from app.models.inventory import InventoryLevel, StockTransaction
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.setting_service import setting_service
from app.services.kpi_service import kpi_service

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
    # Enrich items with product names
    for project in projects:
        for item in project.items:
             item.item_name = item.inventory_item.name if item.inventory_item else None
             item.item_sku = item.inventory_item.sku if item.inventory_item else None
    return projects

@router.post("/", response_model=ProjectResponse)
def create_project(
    *,
    db: Session = Depends(get_db),
    project_in: ProjectCreate,
) -> Any:
    """
    Create new project with items.
    """
    project_data = project_in.model_dump(exclude={"items"})
    project = Project(**project_data)
    db.add(project)
    db.flush() # Get project ID

    if project_in.items:
        for item_in in project_in.items:
            project_item = ProjectItem(
                project_id=project.id,
                **item_in.model_dump()
            )
            db.add(project_item)

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
    Update a project and handle stock consumption on DONE.
    """
    project = db.query(Project).filter(Project.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    old_status = project.status
    update_data = project_in.model_dump(exclude_unset=True, exclude={"items"})
    
    for field, value in update_data.items():
        setattr(project, field, value)
    
    # Handle status change to DONE (Closing the loop)
    if project.status == ProjectStatus.DONE and old_status != ProjectStatus.DONE:
        # Deduct stock for all items
        for p_item in project.items:
            # We assume for now that items are taken from a default warehouse or a specific one linked to project
            # If project doesn't have a warehouse_id, we might need to add it or use a default.
            # For now, let's look for any warehouse that has this item.
            level = db.query(InventoryLevel).filter(
                InventoryLevel.item_id == p_item.item_id,
                InventoryLevel.quantity_on_hand >= p_item.required_quantity
            ).first()

            if not level:
                 # In a real ERP, we might want to allow negative stock or throw an error
                 # For now, let's just log it or continue if we find a level with at least some stock
                 level = db.query(InventoryLevel).filter(InventoryLevel.item_id == p_item.item_id).first()

            if level:
                level.quantity_on_hand -= p_item.required_quantity
                p_item.issued_quantity = p_item.required_quantity
                
                # Create Stock Transaction
                stock_tx = StockTransaction(
                    item_id=p_item.item_id,
                    warehouse_id=level.warehouse_id,
                    transaction_type="OUT",
                    quantity=-p_item.required_quantity,
                    reference=f"PROJECT-{project.id}",
                    notes=f"Project Completion: {project.title}",
                    created_at=datetime.now(timezone.utc)
                )
                db.add(stock_tx)

        # KPI Trigger
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

    db.add(project)
    db.commit()
    db.refresh(project)
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
