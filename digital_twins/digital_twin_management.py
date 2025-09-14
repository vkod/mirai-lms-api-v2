

import asyncio
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.async_helper import run_async

from storage.digital_twin_storage import ScalableDigitalTwinStorage
from storage.digital_twin_search import DigitalTwinSearch
from storage.persona_image_storage import PersonaImageStorage

# Initialize storage instances
digital_twin_storage = ScalableDigitalTwinStorage()
digital_twin_search = DigitalTwinSearch()
persona_image_storage = PersonaImageStorage()

def _extract_persona_summary_from_markdown(markdown_content: str) -> str:
    """Extract the persona summary section from markdown content"""
    if not markdown_content:
        return "No summary available"
    
    lines = markdown_content.split('\n')
    in_summary = False
    summary_lines = []
    
    for line in lines:
        # Check if we're entering the Persona Summary section
        if 'Persona Summary' in line or 'persona summary' in line.lower():
            in_summary = True
            continue
        
        # Check if we're leaving the summary section (next heading)
        if in_summary and line.strip().startswith('#'):
            break
        
        # Collect summary lines
        if in_summary and line.strip():
            summary_lines.append(line.strip())
    
    return ' '.join(summary_lines) if summary_lines else "No summary available"

@dataclass
class SyntheticPersona:
    """
    A data class representing a synthetic persona of a Lead with comprehensive profile information.
    """
    # Lead Identifier
    lead_id: str

    # Lead Classification
    lead_classification: str  # hot, cold, or warm

    # Persona Summary
    persona_summary: str
    profile_image_url: str  # URL to the lead's photograph

    # Personal Information
    full_name: str
    age: str
    marital_status: str
    dependents: str
    gender: str
    life_stages: str

    # Demographic Information
    occupation: str
    education_level: str

    # Financial Information
    annual_income: str
    employment_information: str

    # Insurance History
    insurance_history:str

    # Behavioral Signals & Preferences
    behaioral_signals: str

    # Engagement & Opportunities
    interaction_history: str
    next_best_actions: str

    markdown: str = ""  # Optional markdown representation of the persona


# Async wrapper functions for storage operations
async def save_digital_twin(lead_id: str, markdown_content: str, classification: Optional[str] = None) -> Dict[str, Any]:
    """Save a digital twin to Azure storage"""
    return await digital_twin_storage.save_digital_twin(lead_id, markdown_content, classification)

async def get_digital_twin(lead_id: str) -> Optional[str]:
    """Get a digital twin from Azure storage"""
    return await digital_twin_storage.get_digital_twin(lead_id)

async def search_digital_twins(query: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Search digital twins using Azure AI Search or Cosmos DB"""
    return digital_twin_search.search_twins(query, filters)

async def save_persona_image(lead_id: str, image_bytes: bytes) -> Dict[str, str]:
    """Save persona images to Azure Blob Storage"""
    return await persona_image_storage.save_persona_image(lead_id, image_bytes)

async def get_persona_image(lead_id: str, size: str = "full") -> Optional[bytes]:
    """Get persona image from Azure Blob Storage"""
    return await persona_image_storage.get_persona_image(lead_id, size)

#Return a list of synthetic personas from database.
async def get_synthetic_personas() -> List[SyntheticPersona]:
    """
    Returns a list of synthetic personas from Azure storage or mock data.
    """
    # Try to get from Azure storage first
    try:
        twins = await digital_twin_storage.list_digital_twins(limit=100)
        
        if twins:
            personas = []
            for twin in twins:
                twin_meta = twin.get('metadata', {})
                lead_id = twin.get('id')
                
               
                # Extract data from insurance prospect structure in metadata
                personal_info = twin_meta.get('personal_information', {})
                demographic_info = twin_meta.get('demographic_information', {})
                financial_info = twin_meta.get('financial_information', {})
                insurance_hist = twin_meta.get('insurance_history', {})
                
                # Get persona summary from metadata only (no markdown fetch)
                persona_summary = twin_meta.get('persona_summary', 'No summary available')
                
                # Determine life stage based on age and marital status
                age_str = personal_info.get('age', 'Unknown')
                marital_status = demographic_info.get('marital_status', 'Unknown')
                life_stages = 'Unknown'
                if age_str != 'Unknown':
                    try:
                        age_val = int(age_str) if age_str.isdigit() else int(age_str.split()[0]) if ' ' in age_str else 0
                        if age_val < 30:
                            life_stages = 'Early Career' if marital_status == 'Single' else 'Young Family'
                        elif age_val < 50:
                            life_stages = 'Mid-Career' if marital_status == 'Single' else 'Established Family'
                        elif age_val < 65:
                            life_stages = 'Pre-retirement'
                        else:
                            life_stages = 'Retired'
                    except:
                        pass
                
                # Format insurance history information
                insurance_history_str = 'Unknown'
                if insurance_hist:
                    policies = insurance_hist.get('current_policies', 'Unknown')
                    needs = insurance_hist.get('current_needs', '')
                    claims = insurance_hist.get('claims_history', 'Unknown')
                    insurance_history_parts = []
                    if policies != 'Unknown':
                        insurance_history_parts.append(f"Current policies: {policies}")
                    if needs and needs != 'Unknown':
                        insurance_history_parts.append(f"Needs: {needs}")
                    if claims != 'Unknown':
                        insurance_history_parts.append(f"Claims: {claims}")
                    if insurance_history_parts:
                        insurance_history_str = ", ".join(insurance_history_parts)
                
                persona = SyntheticPersona(
                    lead_id=lead_id,
                    lead_classification=twin_meta.get('lead_classification', 'unknown'),
                    persona_summary=persona_summary,
                    profile_image_url="",
                    full_name="Unknown",
                    age=personal_info.get('age', 'Unknown'),
                    marital_status=demographic_info.get('marital_status', 'Unknown'),
                    dependents='Unknown',
                    gender=personal_info.get('gender', 'Unknown'),
                    life_stages=life_stages,
                    occupation=personal_info.get('occupation', 'Unknown'),
                    education_level=demographic_info.get('education', 'Unknown'),
                    annual_income=financial_info.get('annual_income', 'Unknown'),
                    employment_information=f"{personal_info.get('occupation', 'Unknown')} - {personal_info.get('lead_status', 'Unknown')} lead",
                    insurance_history=insurance_history_str,
                    behaioral_signals='Unknown',
                    interaction_history='Unknown',
                    next_best_actions='Unknown',
                    markdown=""  # No markdown content fetched for performance
                )
                personas.append(persona)
            return personas
    except Exception as e:
        print(f"Error fetching from Azure storage: {e}")
    
    # Fall back to mock data
    import random
    classifications = ["hot", "cold", "warm"]
    mock_personas = [
        SyntheticPersona(
            lead_id="c82e9186-babb-465e-bc5f-77483fec5678",
            lead_classification=random.choice(classifications),
            persona_summary="Tech-savvy millennial professional seeking comprehensive insurance coverage",
            profile_image_url="https://example.com/profiles/lead001.jpg",
            full_name="Unknown",
            age="32",
            marital_status="Married",
            dependents="2 children",
            gender="Female",
            life_stages="Young Family",
            occupation="Software Engineer",
            education_level="Master's Degree",
            annual_income="120,000",
            employment_information="Full-time at Tech Corp, 5 years tenure",
            insurance_history="Current auto and home insurance, no claims in past 5 years",
            behaioral_signals="Researches thoroughly online, prefers digital communication",
            interaction_history="3 website visits, downloaded retirement planning guide",
            next_best_actions="Schedule virtual consultation for life insurance"
        ),
        SyntheticPersona(
            lead_id="0fbe7adf-5887-4329-b10a-4d87dc1fb13e",
            lead_classification=random.choice(classifications),
            persona_summary="Recently retired professional looking to adjust insurance portfolio",
            profile_image_url="https://example.com/profiles/lead002.jpg",
            full_name="Unknown",
            age="65",
            marital_status="Married",
            dependents="None, 2 adult children",
            gender="Male",
            life_stages="Retired",
            occupation="Retired Financial Advisor",
            education_level="Bachelor's Degree",
            annual_income="85,000",
            employment_information="Retired, pension and investment income",
            insurance_history="Multiple policies, loyal customer for 20 years",
            behaioral_signals="Prefers phone calls, traditional approach to decision making",
            interaction_history="Recent retirement review meeting, interested in estate planning",
            next_best_actions="Follow up about estate planning services"
        ),
        SyntheticPersona(
            lead_id="LEAD003",
            lead_classification=random.choice(classifications),
            persona_summary="Young entrepreneur seeking business and personal coverage",
            profile_image_url="https://example.com/profiles/lead003.jpg",
            full_name="Unknown",
            age="28",
            marital_status="Single",
            dependents="None",
            gender="Non-binary",
            life_stages="Career Starter",
            occupation="Small Business Owner",
            education_level="Bachelor's Degree",
            annual_income="75,000",
            employment_information="Owner of digital marketing agency, 2 years in business",
            insurance_history="Basic health insurance, seeking business coverage",
            behaioral_signals="Active on social media, quick decision maker",
            interaction_history="Requested business insurance quote online",
            next_best_actions="Present combined personal/business insurance packages"
        ),
        SyntheticPersona(
            lead_id="LEAD004",
            lead_classification=random.choice(classifications),
            persona_summary="Mid-career professional interested in family protection",
            profile_image_url="https://example.com/profiles/lead004.jpg",
            full_name="Unknown",
            age="45",
            marital_status="Divorced",
            dependents="1 child",
            gender="Female",
            life_stages="Single Parent",
            occupation="Healthcare Administrator",
            education_level="PhD",
            annual_income="95,000",
            employment_information="Hospital administration, 12 years experience",
            insurance_history="Life and health insurance, considering additional coverage",
            behaioral_signals="Detail-oriented, cautious decision maker",
            interaction_history="Attended webinar on family protection plans",
            next_best_actions="Schedule consultation for education savings plan"
        ),
        SyntheticPersona(
            lead_id="LEAD005",
            lead_classification=random.choice(classifications),
            persona_summary="Recent graduate starting career in finance",
            profile_image_url="https://example.com/profiles/lead005.jpg",
            full_name="Unknown",
            age="23",
            marital_status="Single",
            dependents="None",
            gender="Male",
            life_stages="Early Career",
            occupation="Junior Financial Analyst",
            education_level="Bachelor's Degree",
            annual_income="55,000",
            employment_information="First job at investment firm",
            insurance_history="Basic health insurance through employer",
            behaioral_signals="Tech-savvy, price-conscious, research-oriented",
            interaction_history="Downloaded financial planning app",
            next_best_actions="Share entry-level investment products information"
        ),
        SyntheticPersona(
            lead_id="LEAD006",
            lead_classification=random.choice(classifications),
            persona_summary="Established business owner looking for succession planning",
            profile_image_url="https://example.com/profiles/lead006.jpg",
            full_name="Unknown",
            age="58",
            marital_status="Married",
            dependents="3 adult children",
            gender="Male",
            life_stages="Pre-retirement",
            occupation="Business Owner",
            education_level="Master's in Business",
            annual_income="250,000",
            employment_information="Owner of manufacturing company, 25 years in business",
            insurance_history="Comprehensive business and personal insurance portfolio",
            behaioral_signals="Values personal relationships, traditional approach",
            interaction_history="Met with advisor for business valuation",
            next_best_actions="Present succession planning options"
        )
    ]
    return mock_personas


async def get_synthetic_persona(id: str) -> SyntheticPersona:
    """Get a specific synthetic persona by ID"""
    # Try to get from Azure storage first
    try:
        # Get metadata and content
        twin_meta = await digital_twin_storage.get_digital_twin_metadata(id)
        if twin_meta:
            # Check if image exists
            image_url = f"/persona_image/{id}"
            
            # Get the markdown content
            markdown_content = await digital_twin_storage.get_digital_twin(id) or ""
            
            # Extract data from insurance prospect structure in metadata
            personal_info = twin_meta.get('personal_information', {})
            demographic_info = twin_meta.get('demographic_information', {})
            financial_info = twin_meta.get('financial_information', {})
            insurance_hist = twin_meta.get('insurance_history', {})
            
            # Get persona summary from metadata or extract from markdown
            persona_summary = twin_meta.get('persona_summary', '')
            if not persona_summary or persona_summary == 'Unknown':
                persona_summary = _extract_persona_summary_from_markdown(markdown_content)
            
            # Determine life stage based on age and marital status
            age_str = personal_info.get('age', 'Unknown')
            marital_status = demographic_info.get('marital_status', 'Unknown')
            life_stages = 'Unknown'
            if age_str != 'Unknown':
                try:
                    age_val = int(age_str) if age_str.isdigit() else int(age_str.split()[0]) if ' ' in age_str else 0
                    if age_val < 30:
                        life_stages = 'Early Career' if marital_status == 'Single' else 'Young Family'
                    elif age_val < 50:
                        life_stages = 'Mid-Career' if marital_status == 'Single' else 'Established Family'
                    elif age_val < 65:
                        life_stages = 'Pre-retirement'
                    else:
                        life_stages = 'Retired'
                except:
                    pass
            
            # Format insurance history information
            insurance_history_str = 'Unknown'
            if insurance_hist:
                policies = insurance_hist.get('current_policies', 'Unknown')
                needs = insurance_hist.get('current_needs', '')
                claims = insurance_hist.get('claims_history', 'Unknown')
                insurance_history_parts = []
                if policies != 'Unknown':
                    insurance_history_parts.append(f"Current policies: {policies}")
                if needs and needs != 'Unknown':
                    insurance_history_parts.append(f"Needs: {needs}")
                if claims != 'Unknown':
                    insurance_history_parts.append(f"Claims: {claims}")
                if insurance_history_parts:
                    insurance_history_str = ", ".join(insurance_history_parts)
            
            return SyntheticPersona(
                lead_id=id,
                lead_classification=twin_meta.get('lead_classification', 'unknown'),
                persona_summary=persona_summary,
                profile_image_url=image_url,
                full_name="Unknown",
                age=personal_info.get('age', 'Unknown'),
                marital_status=demographic_info.get('marital_status', 'Unknown'),
                dependents='Unknown',
                gender=personal_info.get('gender', 'Unknown'),
                life_stages=life_stages,
                occupation=personal_info.get('occupation', 'Unknown'),
                education_level=demographic_info.get('education', 'Unknown'),
                annual_income=financial_info.get('annual_income', 'Unknown'),
                employment_information=f"{personal_info.get('occupation', 'Unknown')} - {personal_info.get('lead_status', 'Unknown')} lead",
                insurance_history=insurance_history_str,
                behaioral_signals='Unknown',
                interaction_history='Unknown',
                next_best_actions='Unknown',
                markdown=markdown_content
            )
    except Exception as e:
        print(f"Error fetching from Azure storage: {e}")
    
    # Fall back to mock data search
    personas = await get_synthetic_personas()
    for persona in personas:
        if persona.lead_id == id:
            return persona
    return None