# Q&A Feature API Specification

## Overview
This document outlines the API endpoints required for the Prospect Digital Twins Q&A feature, including request/response models using Pydantic schemas.

## Table of Contents
1. [Data Models](#data-models)
2. [REST API Endpoints](#rest-api-endpoints)
3. [WebSocket/SSE Endpoints](#websocketsse-endpoints)
4. [Implementation Notes](#implementation-notes)

---

## Data Models

### Pydantic Models (Python)

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
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
    context: Optional[dict] = Field(default={}, description="Additional context for the question")

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
    sentiment_distribution: dict = Field(..., description="Distribution of sentiments across responses")
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
    data: Optional[dict] = None
    new_response: Optional[ProspectResponse] = None
    summary: Optional[SessionSummary] = None
    progress: Optional[dict] = Field(None, description="Progress info: {responded: int, total: int}")
```

---

## REST API Endpoints

### 1. Submit Question to Prospects
**POST** `/api/v1/qa/sessions`

Submit a new question to selected prospects.

**Request Body:**
```python
QuestionSubmitRequest
```

**Response:**
```python
QuestionSubmitResponse
```

**Example Request:**
```json
{
  "question": "What are your primary concerns when considering life insurance?",
  "prospect_ids": ["LEAD-1001", "LEAD-1002", "LEAD-1003"],
  "image_base64": "iVBORw0KGgoAAAANS...",
  "image_mime_type": "image/png",
  "context": {
    "campaign_id": "CAMP-2024-Q1",
    "agent_id": "AGENT-001"
  }
}
```

**Example Response:**
```json
{
  "session_id": "QS-1234567890",
  "status": "pending",
  "message": "Question submitted successfully to 3 prospects",
  "created_at": "2024-01-15T10:30:00Z",
  "total_prospects": 3,
  "estimated_completion_time": 180
}
```

---

### 2. Get Q&A Sessions List
**GET** `/api/v1/qa/sessions`

Retrieve a paginated list of Q&A sessions with filtering options.

**Query Parameters:**
- All fields from `SessionListRequest`

**Response:**
```python
SessionListResponse
```

**Example Request:**
```
GET /api/v1/qa/sessions?status_filter=in_progress,completed&page=1&page_size=20&sort_by=created_at&sort_order=desc
```

---

### 3. Get Session Details
**GET** `/api/v1/qa/sessions/{session_id}`

Get detailed information about a specific Q&A session.

**Path Parameters:**
- `session_id`: String - The unique session identifier

**Response:**
```python
QuestionSession
```

---

### 4. Get Session Responses
**GET** `/api/v1/qa/sessions/{session_id}/responses`

Get all responses for a specific session (supports polling for updates).

**Path Parameters:**
- `session_id`: String - The unique session identifier

**Query Parameters:**
- `since_timestamp`: Optional[datetime] - Only return responses received after this timestamp

**Response:**
```python
class ResponsesListResponse(BaseModel):
    session_id: str
    responses: List[ProspectResponse]
    total_responded: int
    total_expected: int
    is_complete: bool
    summary: Optional[SessionSummary] = None
```

---

### 5. Cancel/Stop Session
**POST** `/api/v1/qa/sessions/{session_id}/cancel`

Cancel an ongoing Q&A session.

**Path Parameters:**
- `session_id`: String - The unique session identifier

**Response:**
```python
class CancelSessionResponse(BaseModel):
    session_id: str
    status: SessionStatus
    message: str
    cancelled_at: datetime
```

---

### 6. Regenerate Summary
**POST** `/api/v1/qa/sessions/{session_id}/regenerate-summary`

Regenerate the AI summary for a completed session.

**Path Parameters:**
- `session_id`: String - The unique session identifier

**Request Body:**
```python
class RegenerateSummaryRequest(BaseModel):
    focus_areas: Optional[List[str]] = Field(None, description="Specific areas to focus on in the summary")
    summary_style: Literal["detailed", "concise", "bullet_points"] = Field("concise")
```

**Response:**
```python
SessionSummary
```

---

## WebSocket/SSE Endpoints

### Real-time Updates via Server-Sent Events (SSE)
**GET** `/api/v1/qa/sessions/{session_id}/stream`

Subscribe to real-time updates for a specific session.

**Event Types:**
1. `response_received` - New prospect response available
2. `session_completed` - All responses received and summary generated
3. `session_failed` - Session encountered an error

**Event Format:**
```python
ResponseUpdateNotification
```

**Example SSE Message:**
```
event: response_received
data: {
  "event_type": "response_received",
  "session_id": "QS-1234567890",
  "timestamp": "2024-01-15T10:32:30Z",
  "new_response": {
    "persona": {
      "lead_id": "LEAD-1001",
      "full_name": "John Doe",
      "lead_classification": "hot"
    },
    "answer": "My primary concern is ensuring adequate coverage for my family...",
    "answered_at": "2024-01-15T10:32:30Z",
    "confidence_score": 0.95
  },
  "progress": {
    "responded": 1,
    "total": 3
  }
}
```

### Alternative: WebSocket Connection
**WS** `/api/v1/qa/sessions/ws`

Connect via WebSocket for bidirectional communication.

**Connection Protocol:**
1. Client connects with authentication token
2. Client subscribes to specific session IDs
3. Server sends updates for subscribed sessions
4. Client can unsubscribe from sessions

**Subscribe Message:**
```json
{
  "action": "subscribe",
  "session_ids": ["QS-1234567890", "QS-0987654321"]
}
```

---

## Implementation Notes

### Backend Processing Flow
1. **Question Submission**
   - Validate prospect IDs exist
   - Create session record with `pending` status
   - Queue tasks for each prospect AI agent
   - Return session ID immediately

2. **Asynchronous Processing**
   - Each prospect agent (SyntheticPersonChatAgent) processes the question independently
   - Responses are saved as they complete
   - Status updates to `in_progress` after first response
   - Generate summary when all responses received
   - Update status to `completed`

3. **Real-time Updates**
   - SSE connection for one-way updates (recommended)

### Error Handling
```python
class APIError(BaseModel):
    error_code: str
    message: str
    details: Optional[dict] = None
    timestamp: datetime

# Common error codes:
# - INVALID_PROSPECT_IDS: One or more prospect IDs not found
# - SESSION_NOT_FOUND: Requested session doesn't exist
# - QUOTA_EXCEEDED: User has exceeded Q&A quota
# - PROCESSING_ERROR: Error during AI processing
```
