import dspy
import os
import sys
import asyncio
import base64
from typing import List, Dict, Any, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from dotenv import load_dotenv

load_dotenv()

# Add parent directories to path for storage imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from storage.digital_twin_storage import ScalableDigitalTwinStorage
from utils.async_helper import run_async
from agent_dojo.tools.file_utils import get_optimized_program_file_directory, get_training_set_directory
from agent_dojo.tools.lmtools import log_lm_execution_cost

# Initialize storage
digital_twin_storage = ScalableDigitalTwinStorage()

# Model configurations
model_for_execution = dspy.LM(os.getenv('GROQ_LLAMA_MODEL', 'openai/gpt-4-mini'), temperature=0.7, max_tokens=4000)
model_for_survey = dspy.LM('openai/gpt-4-mini', temperature=0.8, max_tokens=2000)


class GenerateSurveyQuestionsSig(dspy.Signature):
    """Generate a comprehensive list of survey questions based on the input topic or initial questions"""
    survey_input: str = dspy.InputField(desc="Initial survey question(s) or topic")
    is_image: bool = dspy.InputField(desc="Whether the input is an image description")
    survey_questions: List[str] = dspy.OutputField(desc="List of 5-10 comprehensive survey questions")


class PersonaResponseSig(dspy.Signature):
    """Generate authentic survey responses from a digital twin persona's perspective"""
    digital_twin: str = dspy.InputField(desc="Digital twin markdown content")
    survey_questions: List[str] = dspy.InputField(desc="List of survey questions")
    image_description: str = dspy.InputField(desc="Image description if provided, otherwise empty")
    responses: Dict[str, str] = dspy.OutputField(desc="Question-answer pairs from persona's perspective")


class ConsolidateResponsesSig(dspy.Signature):
    """Consolidate and analyze responses from multiple personas"""
    all_responses: List[Dict[str, Any]] = dspy.InputField(desc="List of all persona responses")
    survey_questions: List[str] = dspy.InputField(desc="Original survey questions")
    consolidated_report: Dict[str, Any] = dspy.OutputField(desc="Consolidated analysis with patterns and insights")


class SurveyResponseAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate_questions = dspy.ChainOfThought(GenerateSurveyQuestionsSig)
        self.persona_response = dspy.ChainOfThought(PersonaResponseSig)
        self.consolidate = dspy.ChainOfThought(ConsolidateResponsesSig)
    
    def forward(self, survey_input: str, is_image: bool = False, max_personas: int = 20):
        # Step 1: Generate comprehensive survey questions
        questions_output = self.generate_questions(
            survey_input=survey_input,
            is_image=is_image
        )
        survey_questions = questions_output.survey_questions
        
        # Step 2: Get digital twins from storage
        digital_twins = self._get_digital_twins(limit=max_personas)
        
        if not digital_twins:
            return dspy.Prediction(
                survey_questions=survey_questions,
                responses=[],
                consolidated_report={"error": "No digital twins found in storage"},
                total_respondents=0
            )
        
        # Step 3: Collect responses from personas in parallel
        all_responses = self._collect_parallel_responses(
            digital_twins=digital_twins,
            survey_questions=survey_questions,
            image_description=survey_input if is_image else ""
        )
        
        # Step 4: Consolidate responses
        consolidated_output = self.consolidate(
            all_responses=all_responses,
            survey_questions=survey_questions
        )
        
        return dspy.Prediction(
            survey_questions=survey_questions,
            responses=all_responses,
            consolidated_report=consolidated_output.consolidated_report,
            total_respondents=len(all_responses)
        )
    
    def _get_digital_twins(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve digital twins from storage"""
        try:
            # Get list of digital twins with their metadata
            twins_metadata = run_async(
                digital_twin_storage.list_digital_twins(limit=limit)
            )
            
            digital_twins = []
            for twin_meta in twins_metadata:
                twin_content = run_async(
                    digital_twin_storage.get_digital_twin(twin_meta['id'])
                )
                if twin_content:
                    digital_twins.append({
                        'lead_id': twin_meta['id'],
                        'classification': twin_meta.get('lead_classification', 'unknown'),
                        'content': twin_content,
                        'metadata': twin_meta
                    })
            
            return digital_twins
        except Exception as e:
            print(f"Error retrieving digital twins: {e}")
            return []
    
    def _collect_parallel_responses(self, digital_twins: List[Dict[str, Any]], 
                                   survey_questions: List[str],
                                   image_description: str = "",
                                   batch_size: int = 5) -> List[Dict[str, Any]]:
        """Collect survey responses from multiple personas in parallel"""
        all_responses = []
        
        def get_persona_response(twin_data: Dict[str, Any]) -> Dict[str, Any]:
            """Get response from a single persona"""
            try:
                response = self.persona_response(
                    digital_twin=twin_data['content'],
                    survey_questions=survey_questions,
                    image_description=image_description
                )
                
                return {
                    'lead_id': twin_data['lead_id'],
                    'classification': twin_data['classification'],
                    'responses': response.responses,
                    'metadata': {
                        'age': twin_data['metadata'].get('age'),
                        'income': twin_data['metadata'].get('income'),
                        'location': twin_data['metadata'].get('location'),
                        'occupation': twin_data['metadata'].get('occupation')
                    }
                }
            except Exception as e:
                print(f"Error getting response from {twin_data['lead_id']}: {e}")
                return None
        
        # Process personas in parallel batches
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = []
            for twin_data in digital_twins:
                future = executor.submit(get_persona_response, twin_data)
                futures.append(future)
            
            # Collect results as they complete
            for future in as_completed(futures):
                result = future.result()
                if result:
                    all_responses.append(result)
                    print(f"Collected response from {result['lead_id']}")
        
        return all_responses


def run(survey_input: str, is_image: bool = False, max_personas: int = 20, lead_ids: List[str] = None) -> Dict[str, Any]:
    """
    Run the survey response agent
    
    Args:
        survey_input: Survey questions or image description
        is_image: Whether the input is an image
        max_personas: Maximum number of personas to survey
        lead_ids: Optional specific lead IDs to survey
    
    Returns:
        Dictionary containing survey questions, individual responses, and consolidated report
    """
    agent = SurveyResponseAgent()
    
    # Try to load optimized program if available
    optimized_program_file_dir = get_optimized_program_file_directory(__file__)
    optimized_program_file = os.path.join(optimized_program_file_dir, 'SurveyResponseAgent_Optimized')
    if os.path.exists(optimized_program_file):
        agent = dspy.load(optimized_program_file)
    
    lm = model_for_execution
    with dspy.context(lm=lm):
        output = agent(survey_input=survey_input, is_image=is_image, max_personas=max_personas)
        log_lm_execution_cost(lm, "SurveyResponseAgent")
    
    # Format the output
    result = {
        "survey_questions": output.survey_questions,
        "total_respondents": output.total_respondents,
        "responses": output.responses,
        "consolidated_report": output.consolidated_report,
        "summary": _generate_summary(output.consolidated_report, output.total_respondents)
    }
    
    return result


def _generate_summary(consolidated_report: Dict[str, Any], total_respondents: int) -> str:
    """Generate a brief summary of the survey results"""
    summary_parts = [
        f"Survey completed with {total_respondents} digital twin respondents."
    ]
    
    if isinstance(consolidated_report, dict):
        if 'key_findings' in consolidated_report:
            summary_parts.append(f"Key findings: {consolidated_report['key_findings']}")
        if 'patterns' in consolidated_report:
            summary_parts.append(f"Common patterns identified: {len(consolidated_report['patterns'])}")
        if 'insights' in consolidated_report:
            summary_parts.append(f"Generated {len(consolidated_report['insights'])} insights")
    
    return " ".join(summary_parts)


def process_image_survey(image_path: str, initial_questions: str = None) -> Dict[str, Any]:
    """
    Process an image-based survey
    
    Args:
        image_path: Path to the image file
        initial_questions: Optional initial survey questions about the image
    
    Returns:
        Survey results
    """
    # Read and encode image
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    
    # Create image description for survey
    image_description = f"Image survey based on provided image. "
    if initial_questions:
        image_description += f"Focus areas: {initial_questions}"
    else:
        image_description += "General feedback on visual elements, appeal, and effectiveness."
    
    return run(survey_input=image_description, is_image=True)


def optimize():
    """Placeholder for future optimization using DSPy optimizers"""
    # This would be implemented similar to DigitalTwinCreatorAgent
    # when training data is available
    print("Optimization not yet implemented. Training data needed.")
    pass


# Example usage patterns for the agent
example_survey_questions = """
1. What is your preferred method of receiving insurance information?
2. How important is online self-service for managing your policies?
3. What factors are most important when choosing an insurance provider?
4. How comfortable are you with AI-assisted insurance recommendations?
5. What additional services would you value from your insurance provider?
"""

example_image_survey = """
Review this marketing image for our new insurance product.
- Is the messaging clear and compelling?
- Does the visual design appeal to you?
- Would this motivate you to learn more about the product?
- What improvements would you suggest?
"""