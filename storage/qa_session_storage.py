import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from storage.azure_config import azure_config
from models.qa_models import (
    QuestionSession, ProspectResponse, SessionSummary,
    SessionStatus, PersonaBase
)
import base64
import io


class QASessionStorage:
    def __init__(self):
        self.cosmos_client = azure_config.get_cosmos_container_client("qa_sessions")
        self.blob_container = azure_config.get_blob_container_client("qa-images")
        self._ensure_container_exists()

    def _ensure_container_exists(self):
        """Ensure QA sessions container exists in Cosmos DB"""
        try:
            if azure_config.cosmos_client:
                database = azure_config.cosmos_client.get_database_client("mirai-lms")
                database.create_container_if_not_exists(
                    id="qa_sessions",
                    partition_key={"paths": ["/session_id"], "kind": "Hash"}
                )
        except Exception as e:
            print(f"Error ensuring QA sessions container exists: {e}")

    def create_session(
        self,
        question: str,
        prospect_ids: List[str],
        target_prospects: List[PersonaBase],
        image_base64: Optional[str] = None,
        image_mime_type: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> QuestionSession:
        """Create a new Q&A session"""
        session_id = f"QS-{uuid.uuid4().hex[:10].upper()}"

        # Upload image if provided
        image_url = None
        if image_base64 and image_mime_type:
            image_url = self._upload_session_image(session_id, image_base64, image_mime_type)

        session = QuestionSession(
            session_id=session_id,
            question=question,
            image_url=image_url,
            target_prospects=target_prospects,
            status=SessionStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completed_at=None,
            responses=[],
            summary=None,
            total_expected=len(prospect_ids),
            total_responded=0,
            error_message=None
        )

        # Store in Cosmos DB
        session_dict = session.model_dump(mode='json')
        session_dict['id'] = session_id
        session_dict['partition_key'] = session_id
        session_dict['context'] = context or {}

        try:
            self.cosmos_client.create_item(body=session_dict)
        except Exception as e:
            print(f"Error creating session in Cosmos DB: {e}")
            raise

        return session

    def _upload_session_image(self, session_id: str, image_base64: str, mime_type: str) -> str:
        """Upload session image to blob storage"""
        try:
            # Decode base64 image
            image_data = base64.b64decode(image_base64)

            # Determine file extension from mime type
            extension = mime_type.split('/')[-1] if '/' in mime_type else 'png'
            blob_name = f"qa-sessions/{session_id}/image.{extension}"

            # Upload to blob storage
            blob_client = self.blob_container.get_blob_client(blob_name)
            blob_client.upload_blob(
                data=image_data,
                overwrite=True,
                content_settings={"content_type": mime_type}
            )

            return blob_client.url
        except Exception as e:
            print(f"Error uploading session image: {e}")
            return None

    def get_session(self, session_id: str) -> Optional[QuestionSession]:
        """Get a Q&A session by ID"""
        try:
            item = self.cosmos_client.read_item(
                item=session_id,
                partition_key=session_id
            )
            return QuestionSession(**item)
        except Exception as e:
            print(f"Error getting session: {e}")
            return None

    def update_session_status(self, session_id: str, status: SessionStatus, error_message: Optional[str] = None):
        """Update session status"""
        try:
            session = self.get_session(session_id)
            if session:
                session.status = status
                session.updated_at = datetime.utcnow()
                if status == SessionStatus.COMPLETED:
                    session.completed_at = datetime.utcnow()
                if error_message:
                    session.error_message = error_message

                self._update_session(session)
        except Exception as e:
            print(f"Error updating session status: {e}")

    def add_response(self, session_id: str, response: ProspectResponse):
        """Add a response to a session"""
        try:
            session = self.get_session(session_id)
            if session:
                session.responses.append(response)
                session.total_responded = len(session.responses)

                # Update status to in_progress if first response
                if session.status == SessionStatus.PENDING:
                    session.status = SessionStatus.IN_PROGRESS

                session.updated_at = datetime.utcnow()

                # Check if all responses received
                if session.total_responded >= session.total_expected:
                    session.status = SessionStatus.COMPLETED
                    session.completed_at = datetime.utcnow()

                self._update_session(session)
        except Exception as e:
            print(f"Error adding response: {e}")

    def add_summary(self, session_id: str, summary: SessionSummary):
        """Add or update summary for a session"""
        try:
            session = self.get_session(session_id)
            if session:
                session.summary = summary
                session.updated_at = datetime.utcnow()
                self._update_session(session)
        except Exception as e:
            print(f"Error adding summary: {e}")

    def _update_session(self, session: QuestionSession):
        """Update session in Cosmos DB"""
        try:
            session_dict = session.model_dump(mode='json')
            session_dict['id'] = session.session_id
            session_dict['partition_key'] = session.session_id

            self.cosmos_client.upsert_item(body=session_dict)
        except Exception as e:
            print(f"Error updating session in Cosmos DB: {e}")
            raise

    def list_sessions(
        self,
        status_filter: Optional[List[SessionStatus]] = None,
        prospect_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search_query: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """List Q&A sessions with filtering and pagination"""
        try:
            # Build query
            query = "SELECT * FROM c WHERE 1=1"
            parameters = []

            if status_filter:
                status_values = [s.value for s in status_filter]
                query += f" AND c.status IN ({','.join(['@status' + str(i) for i in range(len(status_values))])})"
                for i, status in enumerate(status_values):
                    parameters.append({"name": f"@status{i}", "value": status})

            if date_from:
                query += " AND c.created_at >= @date_from"
                parameters.append({"name": "@date_from", "value": date_from.isoformat()})

            if date_to:
                query += " AND c.created_at <= @date_to"
                parameters.append({"name": "@date_to", "value": date_to.isoformat()})

            if search_query:
                query += " AND CONTAINS(LOWER(c.question), LOWER(@search))"
                parameters.append({"name": "@search", "value": search_query})

            # Add sorting
            sort_direction = "DESC" if sort_order == "desc" else "ASC"
            query += f" ORDER BY c.{sort_by} {sort_direction}"

            # Execute query
            items = list(self.cosmos_client.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))

            # Apply prospect_id filter (if needed)
            if prospect_id:
                items = [
                    item for item in items
                    if any(p.get('lead_id') == prospect_id for p in item.get('target_prospects', []))
                ]

            # Calculate pagination
            total_count = len(items)
            total_pages = (total_count + page_size - 1) // page_size
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size

            # Get page items
            page_items = items[start_idx:end_idx]
            sessions = [QuestionSession(**item) for item in page_items]

            # Count active and completed sessions
            active_count = sum(1 for item in items if item['status'] in ['pending', 'in_progress'])
            completed_count = sum(1 for item in items if item['status'] == 'completed')

            return {
                "sessions": sessions,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "active_sessions_count": active_count,
                "completed_sessions_count": completed_count
            }

        except Exception as e:
            print(f"Error listing sessions: {e}")
            return {
                "sessions": [],
                "total_count": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "active_sessions_count": 0,
                "completed_sessions_count": 0
            }

    def get_responses(self, session_id: str, since_timestamp: Optional[datetime] = None) -> List[ProspectResponse]:
        """Get responses for a session, optionally filtered by timestamp"""
        try:
            session = self.get_session(session_id)
            if not session:
                return []

            responses = session.responses

            if since_timestamp:
                responses = [
                    r for r in responses
                    if r.answered_at > since_timestamp
                ]

            return responses
        except Exception as e:
            print(f"Error getting responses: {e}")
            return []

    def cancel_session(self, session_id: str) -> bool:
        """Cancel a Q&A session"""
        try:
            session = self.get_session(session_id)
            if session and session.status in [SessionStatus.PENDING, SessionStatus.IN_PROGRESS]:
                session.status = SessionStatus.FAILED
                session.error_message = "Session cancelled by user"
                session.updated_at = datetime.utcnow()
                self._update_session(session)
                return True
            return False
        except Exception as e:
            print(f"Error cancelling session: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """Delete a Q&A session permanently"""
        try:
            # Check if session exists
            session = self.get_session(session_id)
            if not session:
                return False

            # Delete from Cosmos DB
            self.cosmos_client.delete_item(
                item=session_id,
                partition_key=session_id
            )

            # Delete associated images from blob storage if any
            if session.image_url:
                try:
                    blob_name = f"qa-sessions/{session_id}/image.png"
                    blob_client = self.blob_container.get_blob_client(blob_name)
                    blob_client.delete_blob()
                except Exception as e:
                    print(f"Error deleting session image: {e}")

            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False