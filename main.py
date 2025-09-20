import uuid
import dspy
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Response, WebSocket
from fastapi.responses import FileResponse
from agent_dojo.tools.file_utils import get_persona_photographs_directory
from fastapi.middleware.cors import CORSMiddleware
from agent_dojo.agents.DigitalTwinCreatorAgent import DigitalTwinCreatorAgent
from agent_dojo.agent_management import get_agents_list, get_agent
from agent_dojo.agents.PersonaImageGenerationAgent import PersonaImageGenerationAgent
from agent_dojo.agents.SyntheticPersonChatAgent import SyntheticPersonChatAgent
from agent_dojo.agents.SyntheticPersonChatAgent.SyntheticPersonChatAgent import get_instructions_for_persona
from agent_dojo.agents.SurveyResponseAgent import SurveyResponseAgent
from storage.persona_image_storage import PersonaImageStorage
from storage.digital_twin_storage import ScalableDigitalTwinStorage
from storage.digital_twin_search import DigitalTwinSearch
from storage.qa_session_storage import QASessionStorage
from voice_chat.voice_chat_manager import create_realtime_session
from services.qa_service import QAService
from models.qa_models import (
    QuestionSubmitRequest, QuestionSubmitResponse,
    SessionListRequest, SessionListResponse,
    QuestionSession, ResponsesListResponse,
    CancelSessionResponse, RegenerateSummaryRequest,
    SessionSummary, SessionStatus, ResponseUpdateNotification
)
import json
import os
import asyncio
from flask import  jsonify, request, abort
from datetime import datetime
import secrets

# Initialize storage instances
persona_image_storage = PersonaImageStorage()
digital_twin_storage = ScalableDigitalTwinStorage()
digital_twin_search = DigitalTwinSearch()
qa_session_storage = QASessionStorage()
qa_service = QAService()



app = FastAPI(title="Mirai LMS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pydantic import BaseModel
from typing import List, Optional
from fastapi.responses import StreamingResponse

class QuestionPayload(BaseModel):
    question: str
    persona: str = None

class DigitalTwinInputPayload(BaseModel):
    data: str
    existing_digital_twin: str = ""
    lead_id: str = None

class SearchPayload(BaseModel):
    query: str
    filters: dict = None
    top: int = 50

class SurveyPayload(BaseModel):
    survey_input: str
    is_image: bool = False
    max_personas: int = 20
    lead_ids: List[str] = None

class ImageSurveyPayload(BaseModel):
    image_base64: str
    initial_questions: str = None
    max_personas: int = 20

# Add this with your other Pydantic models
class PersonaImagePayload(BaseModel):
    persona: str
    lead_id: str = None


@app.get("/")
async def root():
    return {"message": "Mirai LMS API is running"}

#API to trigger optimizing of the DigitalTwinCreatorAgent
@app.post("/optimize_digital_twin_agent")
async def optimize_digital_twin_agent(background_tasks: BackgroundTasks):
    background_tasks.add_task(DigitalTwinCreatorAgent.optimize)
    return {"message": "optimizing started in the background"}

@app.post("/optimize_synthetic_persona_chat_agent")
async def optimize_synthetic_persona_chat_agent(background_tasks: BackgroundTasks):
    background_tasks.add_task(SyntheticPersonChatAgent.optimize)
    return {"message": "optimizing started in the background"}



#API to run  DigitalTwinCreatorAgent
@app.post("/run_digital_twin_agent")
def run_digital_twin_agent(data, existing_digital_twin=""):
   return DigitalTwinCreatorAgent.run(data, existing_digital_twin=existing_digital_twin )


#API to run  DigitalTwinCreatorAgent
@app.post("/create_digital_twin_agent")
def create_digital_twin_agent(payload: DigitalTwinInputPayload):
   output = DigitalTwinCreatorAgent.create(payload.data, existing_digital_twin=payload.existing_digital_twin)

   lead_id = output["lead_id"]
   digital_twin = output["digital_twin"]
   PersonaImageGenerationAgent.run(digital_twin, lead_id=lead_id)
   
   return output


#API to run  DigitalTwinCreatorAgent
@app.post("/test_digital_twin_agent")
def test_digital_twin_agent(payload: DigitalTwinInputPayload):
   return DigitalTwinCreatorAgent.run(payload.data, existing_digital_twin=payload.existing_digital_twin)

#API to return list of agents
@app.get("/agent_list")
async def agent_list():
    return get_agents_list()

#API to return list of agents
@app.get("/agent")
async def agent(id: str):
    return get_agent(id)

#API to return list of SP
@app.get("/get_synthetic_personas")
async def get_synthetic_personas_route():
    from digital_twins.digital_twin_management import get_synthetic_personas
    return await get_synthetic_personas()

#API to return SP
@app.get("/get_synthetic_persona/{id}")
async def get_synthetic_persona_route(id: str):
    from digital_twins.digital_twin_management import get_synthetic_persona
    return await get_synthetic_persona(id)

@app.post("/generate_persona_image")
def generate_persona_image(persona: str, lead_id: str = None):
   return PersonaImageGenerationAgent.run(persona, lead_id=lead_id)

# Update the endpoint
@app.post("/test_lead_image_generation_agent")
def test_lead_image_generation_agent(payload: PersonaImagePayload):

    #Generate a uuid and send as lead_id if not provided
    lead_id = payload.lead_id or str(uuid.uuid4())

    return PersonaImageGenerationAgent.run(payload.persona, lead_id=lead_id)

chat_sessions: dict[str, dspy.History] = {}

def get_or_create_history(session_id: str | None) -> tuple[str, dspy.History]:
    if not session_id:
        session_id = secrets.token_urlsafe(12)
    hist = chat_sessions.get(session_id)
    if hist is None:
        hist = dspy.History(messages=[])
        chat_sessions[session_id] = hist
    return session_id, hist

@app.post("/chat_with_synthetic_persona/{lead_id}")
async def chat_with_synthetic_persona(lead_id: str, payload: QuestionPayload, session_id: str | None = None):
    session_id, history = get_or_create_history(session_id)
    persona = await digital_twin_storage.get_digital_twin(lead_id)
    if not persona:
        persona = PERSONA
    answer = SyntheticPersonChatAgent.run(payload.question, history, persona)
    history.messages.append({"question": payload.question, "answer": answer})
    return {
        "answer": answer,
        "session_id": session_id,
        "messages": history.messages
    }

@app.post("/test_synthetic_person_chat_agent")
def test_synthetic_person_chat_agent(payload: QuestionPayload, session_id: str | None = None):
    session_id, history = get_or_create_history(session_id)
    answer = SyntheticPersonChatAgent.run(
        question=payload.question,
        history=history,
        persona=payload.persona
    )
    history.messages.append({"question": payload.question, "answer": answer})
    return {
        "answer": answer,
        "session_id": session_id,
        "messages": history.messages
    }

# New API endpoints for Azure storage
@app.post("/search_digital_twins")
async def search_digital_twins_route(payload: SearchPayload):
    """Search digital twins using Azure AI Search or Cosmos DB"""
    return digital_twin_search.search_twins(payload.query, payload.filters, payload.top)

@app.get("/digital_twin/{lead_id}")
async def get_digital_twin_route(lead_id: str):
    """Get a specific digital twin by ID"""
    content = await digital_twin_storage.get_digital_twin(lead_id)
    if not content:
        raise HTTPException(status_code=404, detail="Digital twin not found")
    return {"lead_id": lead_id, "content": content}

@app.get("/digital_twin_metadata/{lead_id}")
async def get_digital_twin_metadata_route(lead_id: str):
    """Get digital twin metadata"""
    metadata = await digital_twin_storage.get_digital_twin_metadata(lead_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Digital twin metadata not found")
    return metadata

@app.get("/search_facets")
async def get_search_facets():
    """Get available search facets for filtering"""
    return digital_twin_search.get_facets()

@app.get("/similar_twins/{lead_id}")
async def get_similar_twins(lead_id: str, top: int = 10):
    """Find similar digital twins based on a lead ID"""
    return digital_twin_search.search_similar_twins(lead_id, top)


# API to return persona image by image_id
@app.get("/persona_image_thumbnail/{image_id}")
async def get_persona_image_thumbnail(image_id: str):
    # Try Azure storage first
    image_bytes = await persona_image_storage.get_persona_image(image_id, "thumbnail")
    if image_bytes:
        return Response(content=image_bytes, media_type="image/jpeg")
    
    # Fall back to local storage
    image_dir = get_persona_photographs_directory()
    image_path = os.path.join(image_dir, f"{image_id}_icon.jpeg")
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image_path)

# API to return persona image by image_id
@app.get("/persona_image_medium/{image_id}")
async def get_persona_image_medium(image_id: str):
    # Try Azure storage first
    image_bytes = await persona_image_storage.get_persona_image(image_id, "medium")
    if image_bytes:
        return Response(content=image_bytes, media_type="image/jpeg")
    
    # Fall back to local storage
    image_dir = get_persona_photographs_directory()
    image_path = os.path.join(image_dir, f"{image_id}_medium.jpeg")
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image_path)

# API to return persona image by image_id
@app.get("/persona_image/{image_id}")
async def get_persona_image_full(image_id: str):
    # Try Azure storage first
    image_bytes = await persona_image_storage.get_persona_image(image_id, "full")
    if image_bytes:
        return Response(content=image_bytes, media_type="image/jpeg")
    
    # Fall back to local storage
    image_dir = get_persona_photographs_directory()
    image_path = os.path.join(image_dir, f"{image_id}.jpeg")
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image_path)

PERSONA="""Persona Summary
- User U005 is likely a new parent (inferred) living in Sydney, Australia, actively seeking term life insurance to protect their spouse and child.
- They are exploring coverage options focused on family needs, including education planning, and have demonstrated clear purchase intent by starting a quote.

Personal Information
- User ID: U005
- Age: Unknown
- Gender: Unknown
- Marital Status: Married/Partnered (inferred)
- Dependents: 1 (inferred)
- Smoker Status: Unknown
- Location: Sydney, Australia
- Language: en-AU
- Timezone: Australia/Sydney

Demographic Information
- Occupation: Unknown
- Education Level: Unknown
- Household Size: Unknown

Financial Information
- Annual Income: Unknown
- Assets: Unknown
- Liabilities: Unknown
- Currency: AUD

Insurance History & Current Behavior
- Current Policies: Unknown
- Product Interests: Term life insurance with beneficiaries spouse and child (inferred)
- Beneficiaries: Spouse, child (inferred)
- Coverage Preferences: Interested in coverage planning including education goal
- Term Preference: Unknown
- Quick Quote Parameters: None explicitly provided
- Recent Actions: quote_started
- Notable Pages Viewed: New baby checklist, term life product page with beneficiaries, coverage planner tool focused on dependents and education goal

Behavioral Signals & Preferences
- Device: Smartphone (iPhone)
- OS: iOS 17
- Browser: Mobile Safari
- Screen and Viewport: 1170x2532 / 414x896
- Primary Channel/Referrer: Instagram (cpc campaign \"new_baby_term\")
- Session Metrics: Start – 2025-07-10T08:30:10Z; End – 2025-07-10T08:33:41Z; Duration – 211 sec; Pages – 4
- Language Preference: en-AU
- Tech/Privacy: DNT false; No ad blocker; Cookies enabled

Marketing & Consent
- Consent: Analytics: Yes; Marketing: Yes; Personalization: Yes
- Contactability: No email captured – user not currently contactable

Engagement & Opportunities
- Funnel Stage: Consideration/Intent (quote started)
- Messaging Preferences: Family-focused coverage, education planning, benefits for spouse and child
- Recommended Next Actions: Prompt user to complete and save quote, provide tailored term life comparisons emphasizing family and education benefits
- Conversion Potential: High given purchase intent and targeted new parent campaign"""


# Survey Response Agent endpoints
@app.post("/run_survey")
async def run_survey(payload: SurveyPayload):
    """Run a survey across multiple digital twin personas"""
    try:
        result = SurveyResponseAgent.run(
            survey_input=payload.survey_input,
            is_image=payload.is_image,
            max_personas=payload.max_personas,
            lead_ids=payload.lead_ids
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run_image_survey")
async def run_image_survey(payload: ImageSurveyPayload):
    """Run a survey based on an image across multiple personas"""
    try:
        import base64
        import tempfile
        
        # Decode base64 image and save to temp file
        image_data = base64.b64decode(payload.image_base64)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpeg') as tmp_file:
            tmp_file.write(image_data)
            tmp_path = tmp_file.name
        
        # Process image survey
        result = SurveyResponseAgent.process_image_survey(
            image_path=tmp_path,
            initial_questions=payload.initial_questions
        )
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/optimize_survey_response_agent")
async def optimize_survey_response_agent(background_tasks: BackgroundTasks):
    """Optimize the Survey Response Agent (requires training data)"""
    background_tasks.add_task(SurveyResponseAgent.optimize)
    return {"message": "Survey Response Agent optimization started in the background"}

    

# Q&A Feature Endpoints

@app.post("/api/v1/qa/sessions", response_model=QuestionSubmitResponse)
async def submit_qa_session(request: QuestionSubmitRequest):
    """Submit a new question to selected prospects"""
    try:
        return await qa_service.submit_question(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/v1/qa/sessions")
async def list_qa_sessions(
    status_filter: Optional[str] = None,
    prospect_id: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search_query: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc"
):
    """Get a paginated list of Q&A sessions with filtering options"""
    try:
        # Parse status filter if provided
        status_list = None
        if status_filter:
            status_list = [SessionStatus(s) for s in status_filter.split(',')]

        result = qa_session_storage.list_sessions(
            status_filter=status_list,
            prospect_id=prospect_id,
            date_from=date_from,
            date_to=date_to,
            search_query=search_query,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )

        return SessionListResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/qa/sessions/{session_id}", response_model=QuestionSession)
async def get_qa_session_details(session_id: str):
    """Get detailed information about a specific Q&A session"""
    session = qa_session_storage.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.get("/api/v1/qa/sessions/{session_id}/responses", response_model=ResponsesListResponse)
async def get_session_responses(session_id: str, since_timestamp: Optional[datetime] = None):
    """Get all responses for a specific session"""
    session = qa_session_storage.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    responses = qa_session_storage.get_responses(session_id, since_timestamp)

    return ResponsesListResponse(
        session_id=session_id,
        responses=responses,
        total_responded=len(responses),
        total_expected=session.total_expected,
        is_complete=session.status == SessionStatus.COMPLETED,
        summary=session.summary
    )

@app.post("/api/v1/qa/sessions/{session_id}/cancel", response_model=CancelSessionResponse)
async def cancel_qa_session(session_id: str):
    """Cancel an ongoing Q&A session"""
    success = qa_session_storage.cancel_session(session_id)
    if not success:
        raise HTTPException(status_code=400, detail="Session cannot be cancelled or not found")

    return CancelSessionResponse(
        session_id=session_id,
        status=SessionStatus.FAILED,
        message="Session cancelled successfully",
        cancelled_at=datetime.utcnow()
    )

@app.delete("/api/v1/qa/sessions/{session_id}")
async def delete_qa_session(session_id: str):
    """Delete a Q&A session permanently"""
    success = qa_session_storage.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"message": f"Session {session_id} deleted successfully"}

@app.post("/api/v1/qa/sessions/{session_id}/regenerate-summary", response_model=SessionSummary)
async def regenerate_session_summary(session_id: str, request: RegenerateSummaryRequest):
    """Regenerate the AI summary for a completed session"""
    session = qa_session_storage.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != SessionStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Session must be completed to regenerate summary")

    # Regenerate summary
    summary = await qa_service._generate_summary(session_id, session.responses)
    qa_session_storage.add_summary(session_id, summary)

    return summary

@app.get("/api/v1/qa/sessions/{session_id}/stream")
async def stream_session_updates(session_id: str):
    """Server-Sent Events endpoint for real-time session updates"""
    async def event_generator():
        last_check = datetime.utcnow()

        while True:
            session = qa_session_storage.get_session(session_id)
            if not session:
                yield f"event: error\ndata: Session not found\n\n"
                break

            # Check for new responses
            new_responses = qa_session_storage.get_responses(session_id, last_check)

            for response in new_responses:
                notification = ResponseUpdateNotification(
                    event_type="response_received",
                    session_id=session_id,
                    timestamp=datetime.utcnow(),
                    new_response=response,
                    progress={
                        "responded": session.total_responded,
                        "total": session.total_expected
                    }
                )
                yield f"event: response_received\ndata: {notification.model_dump_json()}\n\n"

            # Check if session completed
            if session.status == SessionStatus.COMPLETED:
                notification = ResponseUpdateNotification(
                    event_type="session_completed",
                    session_id=session_id,
                    timestamp=datetime.utcnow(),
                    summary=session.summary,
                    progress={
                        "responded": session.total_responded,
                        "total": session.total_expected
                    }
                )
                yield f"event: session_completed\ndata: {notification.model_dump_json()}\n\n"
                break

            # Check if session failed
            if session.status == SessionStatus.FAILED:
                notification = ResponseUpdateNotification(
                    event_type="session_failed",
                    session_id=session_id,
                    timestamp=datetime.utcnow(),
                    data={"error": session.error_message}
                )
                yield f"event: session_failed\ndata: {notification.model_dump_json()}\n\n"
                break

            last_check = datetime.utcnow()
            await asyncio.sleep(2)  # Poll every 2 seconds

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )

class RealtimeSessionRequest(BaseModel):
    persona_id: str | None = None

class RealtimeSessionResponse(BaseModel):
    session_id: str
    client_secret: str
    expires_at: datetime

# Voice chat endpoint
@app.post("/realtime/session", response_model=RealtimeSessionResponse)
async def issue_session(payload: RealtimeSessionRequest):

    #Get persona markdown for the user_id if provided
    if payload.persona_id:
        from digital_twins.digital_twin_management import get_synthetic_persona
        persona_data = await get_synthetic_persona(payload.persona_id)
        if persona_data:
            persona = persona_data.persona_summary
            created = create_realtime_session(instructions=get_instructions_for_persona(persona), markdown=persona_data.markdown, gender=persona_data.gender)
            return RealtimeSessionResponse(
                session_id=created.id,
                client_secret=created.client_secret,
                expires_at=created.expires_at
            )
        else:
            #Throw error if persona_id not found
            raise HTTPException(status_code=404, detail="Persona ID not found")




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)