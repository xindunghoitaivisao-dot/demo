from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class User(BaseModel):
    id: str = Field(alias="_id")
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class UserSession(BaseModel):
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ChatMessage(BaseModel):
    id: Optional[str] = None
    user_id: str
    role: str  # 'user' or 'assistant'
    content: str
    confidence: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class DashboardMetrics(BaseModel):
    total_revenue: dict
    active_customers: dict
    conversion_rate: dict
    ai_confidence: dict


class Report(BaseModel):
    id: Optional[str] = None
    user_id: str
    name: str
    type: str
    status: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
