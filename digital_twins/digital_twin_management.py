

from dataclasses import dataclass
from typing import Dict, List, Any

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


#Return a list of synthetic personas from database.
def get_synthetic_personas() -> List[SyntheticPersona]:
    """
    Returns a mock list of synthetic personas with realistic data.
    """
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


def get_synthetic_persona(id: str) -> SyntheticPersona:
    #Return from get_synthetic_personas
    personas = get_synthetic_personas()
    for persona in personas:
        if persona.lead_id == id:
            return persona
    return None