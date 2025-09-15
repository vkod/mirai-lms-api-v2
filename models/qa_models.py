from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict
from datetime import datetime
from enum import Enum


class LeadClassification(str, Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class SessionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class PersonaBase(BaseModel):
    lead_id: str
    lead_classification: Optional[LeadClassification] = None
    full_name: Optional[str] = None
    age: Optional[str] = None
    occupation: Optional[str] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    education_level: Optional[str] = None
    annual_income: Optional[str] = None
    profile_image_url: Optional[str] = None


class QuestionSubmitRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="The question to ask prospects")
    prospect_ids: List[str] = Field(..., min_items=1, description="List of prospect/lead IDs to ask")
    image_base64: Optional[str] = Field(None, description="Base64 encoded image attachment")
    image_mime_type: Optional[str] = Field(None, description="MIME type of the attached image")
    context: Optional[Dict] = Field(default_factory=dict, description="Additional context for the question")


class QuestionSubmitResponse(BaseModel):
    session_id: str = Field(..., description="Unique identifier for the Q&A session")
    status: SessionStatus
    message: str = Field(..., description="Success or error message")
    created_at: datetime
    total_prospects: int
    estimated_completion_time: Optional[int] = Field(None, description="Estimated time in seconds")


class ProspectResponse(BaseModel):
    persona: PersonaBase
    answer: str = Field(..., description="The prospect's response to the question")
    answered_at: datetime
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="AI confidence in the response")


class SessionSummary(BaseModel):
    summary_text: str = Field(..., description="AI-generated summary of all responses")
    key_insights: List[str] = Field(..., description="Bullet points of key insights")
    sentiment_distribution: Dict = Field(..., description="Distribution of sentiments across responses")
    common_themes: List[str] = Field(..., description="Common themes identified in responses")
    generated_at: datetime


class QuestionSession(BaseModel):
    session_id: str
    question: str
    image_url: Optional[str] = None
    target_prospects: List[PersonaBase]
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    responses: List[ProspectResponse] = Field(default_factory=list)
    summary: Optional[SessionSummary] = None
    total_expected: int
    total_responded: int
    error_message: Optional[str] = None


class SessionListRequest(BaseModel):
    status_filter: Optional[List[SessionStatus]] = Field(None, description="Filter by session status")
    prospect_id: Optional[str] = Field(None, description="Filter by specific prospect ID")
    date_from: Optional[datetime] = Field(None, description="Filter sessions created after this date")
    date_to: Optional[datetime] = Field(None, description="Filter sessions created before this date")
    search_query: Optional[str] = Field(None, description="Search in questions and prospect names")
    page: int = Field(1, ge=1, description="Page number for pagination")
    page_size: int = Field(20, ge=1, le=100, description="Number of items per page")
    sort_by: Literal["created_at", "completed_at", "status"] = Field("created_at")
    sort_order: Literal["asc", "desc"] = Field("desc")


class SessionListResponse(BaseModel):
    sessions: List[QuestionSession]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    active_sessions_count: int
    completed_sessions_count: int


class SessionDetailRequest(BaseModel):
    session_id: str


class ResponseUpdateNotification(BaseModel):
    """WebSocket/SSE message for real-time updates"""
    event_type: Literal["response_received", "session_completed", "session_failed"]
    session_id: str
    timestamp: datetime
    data: Optional[Dict] = None
    new_response: Optional[ProspectResponse] = None
    summary: Optional[SessionSummary] = None
    progress: Optional[Dict] = Field(None, description="Progress info: {responded: int, total: int}")


class ResponsesListResponse(BaseModel):
    session_id: str
    responses: List[ProspectResponse]
    total_responded: int
    total_expected: int
    is_complete: bool
    summary: Optional[SessionSummary] = None


class CancelSessionResponse(BaseModel):
    session_id: str
    status: SessionStatus
    message: str
    cancelled_at: datetime


class RegenerateSummaryRequest(BaseModel):
    focus_areas: Optional[List[str]] = Field(None, description="Specific areas to focus on in the summary")
    summary_style: Literal["detailed", "concise", "bullet_points"] = Field("concise")


class APIError(BaseModel):
    error_code: str
    message: str
    details: Optional[Dict] = None
    timestamp: datetime