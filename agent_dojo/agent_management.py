


from dataclasses import dataclass
from typing import Dict, List, Any, Literal

@dataclass
class AgentInputType:
    """
    A class representing the input type for an agent.
    """
    input_desc: str
    input_type: Literal["textbox","textarea","file"]
    name: str
    sample_data: List[str] = None
@dataclass
class AgentOutputType:
    """
    A class representing the output type for an agent.
    """
    output_desc: str
    output_type: Literal["markdown","textarea","image_id"]
    name: str

@dataclass
class Agent:
    """
    A data class representing an AI agent with its core attributes and metrics.
    """
    id: str
    name: str
    version: str
    goal: str
    inputs: List[AgentInputType]
    outputs: List[str]
    metrics: Dict[str, float]
    endpoint_for_testing: str = ""
    
    def __post_init__(self):
        """
        Validates the agent's attributes after initialization.
        """
        if not self.name:
            raise ValueError("Agent name cannot be empty")
        if not self.goal:
            raise ValueError("Agent goal cannot be empty")



digital_twin_sample_data_1="""{"user_id": "U317", "session_id": "S317", "page_views": [{"url": "/home", "timestamp": "2025-09-13T02:22:10Z"}, {"url": "/products/education-plan/grandparent-gifter", "timestamp": "2025-09-13T02:23:05Z"}, {"url": "/tools/education-calculator?child_age=1&gift_mode=monthly&target_amount=6000000", "timestamp": "2025-09-13T02:24:48Z"}, {"url": "/articles/gifting-education-plans-tax-considerations", "timestamp": "2025-09-13T02:26:20Z"}], "actions": [{"action": "calculator_used", "timestamp": "2025-09-13T02:24:48Z"}, {"action": "cta_clicked", "label": "download_gift_certificate_pdf", "timestamp": "2025-09-13T02:25:40Z"}], "referrer": "facebook.com/familyfinancejp", "device": "desktop/windows", "location": "Fukuoka, Japan", "metadata": {"user_agent": "Windows Edge", "browser": "Edge", "os": "Windows 11", "device_type": "desktop", "screen": "1920x1080", "viewport": "1903x969", "language": "ja-JP", "timezone": "Asia/Tokyo", "dnt": true, "ad_blocker": false, "cookies_enabled": true, "consent": {"analytics": true, "marketing": true, "personalization": true}, "utm_source": "facebook", "utm_medium": "paid_social", "utm_campaign": "grandparent_gifter_q3", "utm_content": "video1", "utm_term": null, "fbclid": "FB317", "referrer_domain": "facebook.com", "referrer_path": "/familyfinancejp", "ip_country": "Japan", "geo_city": "Fukuoka", "session_start": "2025-09-13T02:22:10Z", "session_end": "2025-09-13T02:26:35Z", "session_duration_sec": 265, "pages_count": 4, "tracking_id": "trk_317gp", "device_fingerprint": "dfp_317ed", "entry_page": "/home", "exit_page": "/articles/gifting-education-plans-tax-considerations", "avg_scroll_depth": "83%", "internal_searches": ["gift tax limit", "auto top-up for birthdays"]}}"""
digital_twin_sample_data_2="""{"user_id": "U316", "session_id": "S316", "page_views": [{"url": "/home", "timestamp": "2025-09-12T13:30:45Z"}, {"url": "/solutions/sandwich-generation-bundle", "timestamp": "2025-09-12T13:31:38Z"}, {"url": "/tools/coverage-needs?age=48&dependents_children=2&dependents_parents=2&mortgage=38000000", "timestamp": "2025-09-12T13:33:05Z"}, {"url": "/riders/caregiver-support", "timestamp": "2025-09-12T13:34:40Z"}], "actions": [{"action": "calculator_used", "timestamp": "2025-09-12T13:33:05Z"}], "referrer": "google.com/search?q=sandwich+generation+insurance+japan", "device": "mobile/android", "location": "Saitama, Japan", "metadata": {"user_agent": "Android Chrome", "browser": "Chrome", "os": "Android", "device_type": "mobile", "screen": "1080x2400", "viewport": "412x915", "language": "ja-JP", "timezone": "Asia/Tokyo", "dnt": false, "ad_blocker": false, "cookies_enabled": true, "consent": {"analytics": true, "marketing": true, "personalization": true}, "utm_source": "google", "utm_medium": "organic", "utm_campaign": "sandwich_bundle", "utm_content": null, "utm_term": "sandwich generation insurance japan", "referrer_domain": "google.com", "referrer_path": "/search", "ip_country": "Japan", "geo_city": "Saitama", "session_start": "2025-09-12T13:30:45Z", "session_end": "2025-09-12T13:35:02Z", "session_duration_sec": 257, "pages_count": 4, "tracking_id": "trk_316sg", "device_fingerprint": "dfp_316sn", "entry_page": "/home", "exit_page": "/riders/caregiver-support", "avg_scroll_depth": "87%", "internal_searches": ["parent care rider", "family income benefit"]}}"""

#Function to create a list of agents and return
def get_agents_list() -> List[Agent]:
    digitalTwinAgent = Agent(
        id= "digital_twin_agent",
        name="Digital Twin Agent",
        version="1.0",
        goal="""Create an imaginary persona based on data provided and update the digital twin with data as much as possible.If existing_digital_twin information is provided, update it with new or changed information based on clear signals in data""",
        inputs=[
            AgentInputType(input_desc="Website traffic data", input_type="textarea", name="data", sample_data=[digital_twin_sample_data_1,digital_twin_sample_data_2]),
            AgentInputType(input_desc="Existing Digital twin if any", input_type="textarea", name="existing_digital_twin")
        ],
        outputs=[AgentOutputType(output_desc="Updated/New Digital twin", output_type="markdown", name="digital_twin"),
                 AgentOutputType(output_desc="Execution cost", output_type="label", name="execution_cost")],
        metrics={"Data processed": 100, "Digital twins created": 78, "Digital twins updated": 23, "Cost this month": "$100"},
        endpoint_for_testing="test_digital_twin_agent",
        
    )


    leadImageGenerationAgent = Agent(
        id= "lead_image_generation_agent",
        name="Image generation Agent",
        version="1.0",
        goal="Generate image of digital twin based on persona",
        inputs=[
            AgentInputType(input_desc="Digital Twin profile", input_type="textarea", name="persona")
        ],
        outputs=[AgentOutputType(output_desc="Generated image", output_type="image_id", name="generated_image_id"),
                 AgentOutputType(output_desc="Execution cost", output_type="label", name="execution_cost")],
        metrics={"Photos generated": 34, "Cost this month": "$50"},
        endpoint_for_testing="test_lead_image_generation_agent"
    )
    syntheticPersonChatAgent = Agent(
        id= "synthetic_person_chat_agent",
        name="Prospect Digital Twin Agent",
        version="1.0",
        goal="Assumes persona of the 'persona' provided. Answer insurance agent's questions.",
        inputs=[
            AgentInputType(input_desc="Persona profile", input_type="textarea", name="persona", sample_data=[persona_chat_agent_sample_data_1,persona_chat_agent_sample_data_2]),
            AgentInputType(input_desc="Question from insurance agent", input_type="textbox", name="question")
        ],
        outputs=[AgentOutputType(output_desc="Answer", output_type="textarea", name="answer")],
        metrics={"Questions answered": 150,  "Cost this month": "$10"},
        endpoint_for_testing="test_synthetic_person_chat_agent"
    )
     #Return list of agents
    return [digitalTwinAgent,leadImageGenerationAgent, syntheticPersonChatAgent]


def get_agent(id: str) -> Agent:
     #Return agent by id
    agents = get_agents_list()
    for agent in agents:
        if agent.id == id:
            return agent
    return None


persona_chat_agent_sample_data_1="""# Persona Summary
A young dual-income couple in their early 30s residing in Tokyo, Japan, with a focus on balancing finances and securing flexible, family-oriented insurance solutions. The user is proactive in comparing insurance plans and budgeting for premiums, reflecting a moderate financial awareness and responsibility.

# Personal Information
- User Age: 33
- Spouse Age: 34
- Location: Tokyo, Japan
- Device: iPad tablet
- Language: English (Preference for English UI)
- Tech Savviness: Comfortable using online tools and calculators for financial planning

# Demographic Information
- Household: Dual-income couple
- Urban resident
- Budget-conscious

# Financial Information
- Monthly insurance budget: Approximately ¥12,000
- Financial goal: Balance insurance spending with two incomes

# Insurance Needs
- Interested in term life insurance (Term Life Plus, Flex Term plans)
- Health insurance with family coverage (Family Floater Health, Health Plus)
- Prefers flexible premium options
- Values financial planning content focused on dual-income families"""

persona_chat_agent_sample_data_2="""# Persona Summary
A financially conscious individual from Sapporo, Japan, focused on planning and saving systematically for university education expenses. They actively seek optimal saving and insurance products to secure guaranteed returns for a long-term goal.

# Personal Information
- Location: Sapporo, Japan
- Language: Japanese (ja-JP)
- Device: Desktop (Windows 11, Edge browser)

# Demographic Information
- Likely a parent or guardian with children approaching school age
- Age range estimated 30-50 years (based on behavior and goal)

# Financial Information
- Goal: University education savings
- Target amount: 8,000,000 JPY within 10 years
- Monthly savings plan: 40,000 JPY/month
- Interested in endowment insurance products with guaranteed returns
- Shows preference for structured savings plans with maturity benefits

# Insurance Needs
- Education endowment insurance plan
- Products offering guaranteed returns for education savings
- Potential need for life insurance combined with endowment benefits for children’s future security"""