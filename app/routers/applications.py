from fastapi import APIRouter, Depends, HTTPException, status, Query

from ..database import SessionLocal
from ..models import ApplicationDB
from ..schemas import ApplicationRequest, ApplicationResponse, ApplicationStatus, SortOrder, ApplicationStatsResponse
from sqlalchemy import or_, func


router = APIRouter(
    prefix="/applications",
    tags=["Applications"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(
    application: ApplicationRequest,
    db=Depends(get_db)
):
    new_application = ApplicationDB(
        company=application.company,
        role=application.role,
        status=application.status
    )

    db.add(new_application)
    db.commit()
    db.refresh(new_application)

    return new_application


@router.get("", response_model=list[ApplicationResponse])
def get_applications(
    status: ApplicationStatus | None = None,
    company: str | None = None,
    role: str | None = None,
    search: str | None = None,
    sort_by: str | None = None,
    order: SortOrder | None = SortOrder.ASC,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db=Depends(get_db)
):

    sort_columns = {
        "id": ApplicationDB.id,
        "company": ApplicationDB.company,
        "role": ApplicationDB.role,
        "status": ApplicationDB.status,
        "created_at": ApplicationDB.created_at
    }

    query = db.query(ApplicationDB)

    if status:
        query = query.filter(ApplicationDB.status == status.value)

    if company:
        query = query.filter(ApplicationDB.company.ilike(f"%{company}%"))

    if role:
        query = query.filter(ApplicationDB.role.ilike(f"%{role}%"))

    if search:
        query = query.filter(
            or_(
                ApplicationDB.company.ilike(f"%{search}%"),
                ApplicationDB.role.ilike(f"%{search}%")
            )
        )

    offset = (page - 1) * limit

    if sort_by:
        sort_column = sort_columns.get(sort_by)

        if sort_column is None:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sort_by value: {sort_by}. Valid values are: {', '.join(sort_columns.keys())}"
            )
        
        if order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

    query = query.offset(offset).limit(limit)

    return query.all()

@router.get("/stats", response_model=ApplicationStatsResponse)
def get_application_stats(db=Depends(get_db)):
    total_applications = db.query(ApplicationDB).count()

    status_counts = db.query(
        ApplicationDB.status,
        func.count(ApplicationDB.id)
    ).group_by(ApplicationDB.status).all()

    company_counts = db.query(
        ApplicationDB.company,
        func.count(ApplicationDB.id)
    ).group_by(ApplicationDB.company).all()

    return {
        "total_applications": total_applications,
        "status_counts": dict(status_counts),  # Convert list of tuples to dictionary
        "company_counts": dict(company_counts)  
    }

@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(
    application_id: int,
    db=Depends(get_db)
):
    application = db.query(ApplicationDB).filter(
        ApplicationDB.id == application_id
    ).first()

    if application is None:
        raise HTTPException(
            status_code=404,
            detail=f"Application with ID {application_id} not found"
        )

    return application


@router.put("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: int,
    application: ApplicationRequest,
    db=Depends(get_db)
):
    existing_application = db.query(ApplicationDB).filter(
        ApplicationDB.id == application_id
    ).first()

    if existing_application is None:
        raise HTTPException(
            status_code=404,
            detail=f"Application with ID {application_id} not found"
        )

    existing_application.company = application.company
    existing_application.role = application.role
    existing_application.status = application.status
    db.commit()
    db.refresh(existing_application)

    return existing_application


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: int,
    db=Depends(get_db)
):
    application = db.query(ApplicationDB).filter(
        ApplicationDB.id == application_id
    ).first()

    if application is None:
        raise HTTPException(
            status_code=404,
            detail=f"Application with ID {application_id} not found"
        )

    db.delete(application)
    db.commit()

    return {
        "message": f"Application with ID {application_id} deleted successfully"
    }