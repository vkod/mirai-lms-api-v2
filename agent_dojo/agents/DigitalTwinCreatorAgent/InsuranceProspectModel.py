from dataclasses import dataclass, field


@dataclass
class PersonalInformation:
    age: str = "Unknown"
    gender: str = "Unknown"
    occupation: str = "Unknown"
    lead_status: str = "Unknown"


@dataclass
class DemographicInformation:
    location: str = "Unknown"
    education: str = "Unknown"
    marital_status: str = "Unknown"


@dataclass
class FinancialInformation:
    annual_income: str = "Unknown"

@dataclass
class InsuranceHistory:
    current_policies: str = "Unknown"
    current_needs: str = "Unknown"
    claims_history: str = "Unknown"

@dataclass
class InsuranceProspect:
    personal_information: PersonalInformation
    demographic_information: DemographicInformation
    financial_information: FinancialInformation
    insurance_history: InsuranceHistory
    lead_classification: str = "Cold"
    persona_summary:str="Unknown"
