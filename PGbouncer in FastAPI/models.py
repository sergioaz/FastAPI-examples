from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from fastapi import Query


class UserIdRequest(BaseModel):
    """Request model for link aggregate speed data"""
    
    id: int = Field(Query(..., description="User ID"))

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1
            }
        }
    )


class UserIdResponse(BaseModel):
    """Response model for link aggregate speed data with metadata"""
    id: int = Field(..., description="Unique identifier for the user")
    username: str = Field(..., description="username")
    first_name: str = Field(..., description="First Name")
    last_name: str = Field(..., description="Last Name")
    role: int = Field(..., description="User's role")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "username": "johnsonjoshua",
                "first_name": "Jeffrey",
                "last_name": "Doyle",
                "role": 3
            }
        }
    )
