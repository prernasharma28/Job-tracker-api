from fastapi import APIRouter, Depends, HTTPException, status, Query

from ..database import SessionLocal
from ..models import ApplicationDB
from ..schemas import ApplicationRequest, ApplicationResponse, ApplicationStatus, SortOrder, ApplicationStatsResponse
from sqlalchemy import or_, func
from app.security import get_current_user
from app.exceptions import ApplicationNotFoundException

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


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED, summary="Create a new job application",
    description="Create a new job application for the currently authenticated user.")
def create_application(
    application: ApplicationRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    new_application = ApplicationDB(
        user_id=current_user["user_id"],
        company=application.company,
        role=application.role,
        status=application.status
    )

    db.add(new_application)
    db.commit()
    db.refresh(new_application)

    return new_application


@router.get("", response_model=list[ApplicationResponse], summary="Get job applications",
    description="Retrieve a list of job applications for the currently authenticated user."
)
def get_applications(
    page: int = Query(
    1,
    ge=1,
    description="Page number. Must be greater than or equal to 1."
    ),
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Number of applications per page. Must be between 1 and 100."
    ),
    status: ApplicationStatus | None = Query(
        None,
        description="Filter applications by application status."
    ),
    company: str | None = Query(
        None,
        description="Filter applications by company name."
    ),
    role: str | None = Query(
        None,
        description="Filter applications by job role."
    ),
    search: str | None = Query(
        None,
        description="Search for applications by company or job role."
    ),
    sort_by: str | None = Query(
        None,
        description="Sort by: id, company, role, status, or created_at."
    ),
    order: SortOrder = Query(
        SortOrder.ASC,
        description="Sort order: ascending or descending."
    ),
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):

    sort_columns = {
        "id": ApplicationDB.id,
        "company": ApplicationDB.company,
        "role": ApplicationDB.role,
        "status": ApplicationDB.status,
        "created_at": ApplicationDB.created_at
    }

    query = db.query(ApplicationDB).filter(
        ApplicationDB.user_id == current_user["user_id"]
    )

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

@router.get("/stats", response_model=ApplicationStatsResponse, summary="Get job application statistics",
    description="Retrieve statistics about job applications for the currently authenticated user, including total applications, counts by status, and counts by company."
)
def get_application_stats(
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    total_applications = db.query(ApplicationDB).filter(
        ApplicationDB.user_id == current_user["user_id"]
    ).count()

    status_counts = db.query(
        ApplicationDB.status,
        func.count(ApplicationDB.id)
    ).filter(
        ApplicationDB.user_id == current_user["user_id"]
    ).group_by(ApplicationDB.status).all()

    company_counts = db.query(
        ApplicationDB.company,
        func.count(ApplicationDB.id)
    ).filter(
        ApplicationDB.user_id == current_user["user_id"]
    ).group_by(ApplicationDB.company).all()

    return {
        "total_applications": total_applications,
        "status_counts": dict(status_counts),  # Convert list of tuples to dictionary
        "company_counts": dict(company_counts)  
    }

@router.get("/{application_id}", response_model=ApplicationResponse, summary="Get a specific job application",
    description="Retrieve a specific job application by its ID for the currently authenticated user.",
    responses={
        404: {"description": "Application not found"},
        422: {"description": "Invalid application ID"},
    }
)
def get_application(
    application_id: int,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    application = db.query(ApplicationDB).filter(
        ApplicationDB.id == application_id,
        ApplicationDB.user_id == current_user["user_id"]
    ).first()

    if application is None:
        raise ApplicationNotFoundException()

    return application


@router.put("/{application_id}", response_model=ApplicationResponse, summary="Update a specific job application",
    description="Update a specific job application by its ID for the currently authenticated user.",
    responses={
        404: {"description": "Application not found"},
        422: {"description": "Invalid application ID"},
    })
def update_application(
    application_id: int,
    application: ApplicationRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    existing_application = db.query(ApplicationDB).filter(
        ApplicationDB.id == application_id,
        ApplicationDB.user_id == current_user["user_id"]
    ).first()

    if existing_application is None:
        raise ApplicationNotFoundException()

    existing_application.company = application.company
    existing_application.role = application.role
    existing_application.status = application.status
    db.commit()
    db.refresh(existing_application)

    return existing_application


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a specific job application",
    description="Delete a specific job application by its ID for the currently authenticated user.",
    responses={
        404: {"description": "Application not found"},
        422: {"description": "Invalid application ID"},
    }
)
def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    application = db.query(ApplicationDB).filter(
        ApplicationDB.id == application_id,
        ApplicationDB.user_id == current_user["user_id"]
    ).first()

    if application is None:
        raise ApplicationNotFoundException()

    db.delete(application)
    db.commit()