from fastapi import APIRouter, Depends, HTTPException, status

from ..database import SessionLocal
from ..models import ApplicationDB
from ..schemas import ApplicationRequest, ApplicationResponse, ApplicationStatus


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
    db=Depends(get_db)
):
    query = db.query(ApplicationDB)

    if status:
        query = query.filter(ApplicationDB.status == status.value)

    return query.all()


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