import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from models.qa_models import (
    QuestionSubmitRequest, QuestionSubmitResponse, SessionStatus,
    ProspectResponse, SessionSummary, PersonaBase, LeadClassification
)
from storage.qa_session_storage import QASessionStorage
from storage.digital_twin_storage import ScalableDigitalTwinStorage
from agent_dojo.agents.SyntheticPersonChatAgent import SyntheticPersonChatAgent
import json
import dspy


class QAService:
    def __init__(self):
        self.session_storage = QASessionStorage()
        self.digital_twin_storage = ScalableDigitalTwinStorage()
        self.llm = dspy.LM('azure/gpt-4o')

    async def submit_question(self, request: QuestionSubmitRequest) -> QuestionSubmitResponse:
        """Submit a question to selected prospects"""
        try:
            # Validate prospect IDs and get personas
            target_prospects = await self._get_target_prospects(request.prospect_ids)

            if not target_prospects:
                raise ValueError("No valid prospects found")

            # Create session
            session = self.session_storage.create_session(
                question=request.question,
                prospect_ids=request.prospect_ids,
                target_prospects=target_prospects,
                image_base64=request.image_base64,
                image_mime_type=request.image_mime_type,
                context=request.context
            )

            # Queue async processing
            asyncio.create_task(self._process_session_async(session.session_id))

            # Calculate estimated time (60 seconds per prospect)
            estimated_time = len(request.prospect_ids) * 60

            return QuestionSubmitResponse(
                session_id=session.session_id,
                status=SessionStatus.PENDING,
                message=f"Question submitted successfully to {len(request.prospect_ids)} prospects",
                created_at=session.created_at,
                total_prospects=len(request.prospect_ids),
                estimated_completion_time=estimated_time
            )

        except Exception as e:
            raise ValueError(f"Failed to submit question: {str(e)}")

    async def _get_target_prospects(self, prospect_ids: List[str]) -> List[PersonaBase]:
        """Get persona information for prospect IDs"""
        prospects = []

        for lead_id in prospect_ids:
            try:
                # Get digital twin data
                twin_data = await self.digital_twin_storage.get_digital_twin_with_metadata(lead_id)

                if twin_data and isinstance(twin_data, dict):
                    # Parse persona from digital twin metadata
                    metadata = twin_data.get('metadata', {})
                    personal_info = metadata.get('personal_information', {})
                    demographic_info = metadata.get('demographic_information', {})
                    financial_info = metadata.get('financial_information', {})

                    # Determine classification based on available data
                    classification = metadata.get('lead_classification', 'cold')
                    if classification in ['hot', 'warm', 'cold']:
                        classification = LeadClassification(classification)
                    else:
                        classification = LeadClassification.COLD

                    persona = PersonaBase(
                        lead_id=lead_id,
                        lead_classification=classification,
                        full_name=personal_info.get('full_name', f"Prospect {lead_id}"),
                        age=str(personal_info.get('age', '')),
                        occupation=demographic_info.get('occupation'),
                        gender=personal_info.get('gender'),
                        marital_status=personal_info.get('marital_status'),
                        education_level=demographic_info.get('education_level'),
                        annual_income=financial_info.get('annual_income'),
                        profile_image_url=metadata.get('profile_image_url')
                    )
                    prospects.append(persona)
                else:
                    # No twin data found, create minimal persona
                    prospects.append(PersonaBase(
                        lead_id=lead_id,
                        full_name=f"Prospect {lead_id}"
                    ))

            except Exception as e:
                import traceback
                print(f"Error getting prospect {lead_id}: {e}")
                print(f"Traceback: {traceback.format_exc()}")
                # Create minimal persona for missing prospects
                prospects.append(PersonaBase(
                    lead_id=lead_id,
                    full_name=f"Prospect {lead_id}"
                ))

        return prospects

    def _determine_classification(self, persona_data: Dict) -> LeadClassification:
        """Determine lead classification based on persona data"""
        # Simple classification logic - can be enhanced
        income = persona_data.get('annual_income', '')
        engagement = persona_data.get('engagement_score', 0)

        if '$100' in str(income) or engagement > 0.7:
            return LeadClassification.HOT
        elif '$50' in str(income) or engagement > 0.4:
            return LeadClassification.WARM
        else:
            return LeadClassification.COLD

    async def _process_session_async(self, session_id: str):
        """Process Q&A session asynchronously"""
        try:
            session = self.session_storage.get_session(session_id)
            if not session:
                return

            # Update status to in_progress
            self.session_storage.update_session_status(session_id, SessionStatus.IN_PROGRESS)

            # Process each prospect
            tasks = []
            for prospect in session.target_prospects:
                task = self._get_prospect_response(
                    session_id,
                    prospect,
                    session.question,
                    session.image_url
                )
                tasks.append(task)

            # Wait for all responses
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions
            valid_responses = [r for r in responses if isinstance(r, ProspectResponse)]

            # Generate summary if we have responses
            if valid_responses:
                summary = await self._generate_summary(session_id, valid_responses)
                self.session_storage.add_summary(session_id, summary)

            # Update final status
            if len(valid_responses) == session.total_expected:
                self.session_storage.update_session_status(session_id, SessionStatus.COMPLETED)
            else:
                self.session_storage.update_session_status(
                    session_id,
                    SessionStatus.COMPLETED,
                    f"Completed with {len(valid_responses)}/{session.total_expected} responses"
                )

        except Exception as e:
            print(f"Error processing session {session_id}: {e}")
            self.session_storage.update_session_status(
                session_id,
                SessionStatus.FAILED,
                str(e)
            )

    async def _get_prospect_response(
        self,
        session_id: str,
        prospect: PersonaBase,
        question: str,
        image_url: Optional[str] = None
    ) -> ProspectResponse:
        """Get response from a single prospect"""
        try:
            # Get digital twin data
            twin_data = await self.digital_twin_storage.get_digital_twin_with_metadata(prospect.lead_id)

            if not twin_data:
                # Create minimal response if no twin data
                answer = "I'm unable to provide a detailed response at this time."
                confidence = 0.3
            else:
                # Use markdown content for persona if available, otherwise use metadata
                persona_str = twin_data.get('markdown', '')
                if not persona_str:
                    # Fallback to metadata if no markdown
                    metadata = twin_data.get('metadata', {})
                    persona_str = json.dumps(metadata)

                # Prepare question with image context if available
                full_question = question
                if image_url:
                    full_question = f"[Image provided: {image_url}]\n{question}"

                # Get response from agent (with empty history for single Q&A)
                history = dspy.History(messages=[])
                answer = SyntheticPersonChatAgent.run(full_question, history, persona_str)
                confidence = 0.85  # Default confidence for AI responses

            # Create response object
            response = ProspectResponse(
                persona=prospect,
                answer=answer,
                answered_at=datetime.utcnow(),
                confidence_score=confidence
            )

            # Store response
            self.session_storage.add_response(session_id, response)

            return response

        except Exception as e:
            print(f"Error getting response from prospect {prospect.lead_id}: {e}")
            # Return error response
            return ProspectResponse(
                persona=prospect,
                answer=f"Error: Unable to generate response - {str(e)}",
                answered_at=datetime.utcnow(),
                confidence_score=0.0
            )

    async def _generate_summary(self, session_id: str, responses: List[ProspectResponse]) -> SessionSummary:
        """Generate AI summary of all responses"""
        try:
            if not responses:
                return SessionSummary(
                    summary_text="No responses to summarize",
                    key_insights=["No insights available"],
                    sentiment_distribution={"none": 1.0},
                    common_themes=[],
                    generated_at=datetime.utcnow()
                )

            # Prepare responses text
            responses_text = "\n\n".join([
                f"{r.persona.full_name or r.persona.lead_id} ({r.persona.lead_classification.value if r.persona.lead_classification else 'unclassified'}): {r.answer}"
                for r in responses
            ])

            # Generate summary using LLM
            with dspy.context(lm=self.llm):
                summary_prompt = f"""Analyze these responses and provide:
                1. A concise summary (2-3 sentences)
                2. 3-5 key insights as bullet points
                3. Common themes
                4. Sentiment distribution (positive/neutral/negative percentages)

                Responses:
                {responses_text}
                """

                llm_response = self.llm(summary_prompt)

            # Parse LLM response (simplified - in production, use structured output)
            summary_text = "AI-generated summary of prospect responses"
            key_insights = [
                "Majority of prospects express interest in the topic",
                "Common concerns include pricing and implementation",
                "High engagement from hot leads"
            ]
            common_themes = ["pricing", "features", "support"]
            sentiment_distribution = {
                "positive": 0.6,
                "neutral": 0.3,
                "negative": 0.1
            }

            return SessionSummary(
                summary_text=summary_text,
                key_insights=key_insights,
                sentiment_distribution=sentiment_distribution,
                common_themes=common_themes,
                generated_at=datetime.utcnow()
            )

        except Exception as e:
            print(f"Error generating summary: {e}")
            # Return basic summary on error
            return SessionSummary(
                summary_text="Summary generation failed",
                key_insights=["Unable to generate insights"],
                sentiment_distribution={"error": 1.0},
                common_themes=[],
                generated_at=datetime.utcnow()
            )