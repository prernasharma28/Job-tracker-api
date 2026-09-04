from datetime import datetime

from pydantic import BaseModel, Field
from enum import Enum

class ApplicationStatus(str, Enum):
    APPLIED = "Applied"
    INTERVIEW = "Interview"
    REJECTED = "Rejected"
    OFFER = "Offer"

class ApplicationRequest(BaseModel): # Pydantic model for the request applications table
    company: str = Field(min_length=1, max_length=100) # Company name must be between 1 and 100 characters
    role: str = Field(min_length=1, max_length=100) # Role name must be between 1 and 100 characters
    status: ApplicationStatus # Status must be one of the predefined values

class ApplicationResponse(BaseModel): # Pydantic model for the response applications table
    id: int
    company: str
    role: str
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True # Create a response model by reading the attributes from this object.
    }