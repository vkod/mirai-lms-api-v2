# Q&A API - UI Integration Guide

## Base URL
```
http://your-api-host:8000
```

## Endpoints

### 1. Submit Question
**POST** `/api/v1/qa/sessions`

```json
Request:
{
  "question": "What are your insurance needs?",
  "prospect_ids": ["LEAD-001", "LEAD-002"],
  "image_base64": "optional",
  "image_mime_type": "image/png"
}

Response:
{
  "session_id": "QS-ABC123",
  "status": "pending",
  "message": "Question submitted to 2 prospects",
  "created_at": "2024-01-15T10:30:00Z",
  "total_prospects": 2,
  "estimated_completion_time": 120
}
```

### 2. List Sessions
**GET** `/api/v1/qa/sessions?page=1&page_size=20&status_filter=completed`

### 3. Get Session Details
**GET** `/api/v1/qa/sessions/{session_id}`

### 4. Get Responses
**GET** `/api/v1/qa/sessions/{session_id}/responses`

### 5. Real-time Updates (SSE)
**GET** `/api/v1/qa/sessions/{session_id}/stream`

```javascript
const eventSource = new EventSource(`/api/v1/qa/sessions/${sessionId}/stream`);
eventSource.addEventListener('response_received', (e) => {
  const data = JSON.parse(e.data);
  updateUI(data.new_response);
});
```

### 6. Cancel Session
**POST** `/api/v1/qa/sessions/{session_id}/cancel`

Cancels an active session (keeps data, marks as failed).

### 7. Delete Session
**DELETE** `/api/v1/qa/sessions/{session_id}`

Permanently deletes session and all data.

```json
Response: {"message": "Session QS-ABC123 deleted successfully"}
```

### 8. Regenerate Summary
**POST** `/api/v1/qa/sessions/{session_id}/regenerate-summary`

## Status Values
- `pending` - Submitted, not started
- `in_progress` - Getting responses
- `completed` - All done with summary
- `failed` - Cancelled or error

## Quick Integration Steps
1. Submit question with prospect IDs
2. Get session ID from response
3. Subscribe to SSE for updates
4. Show responses as they arrive
5. Display summary when complete