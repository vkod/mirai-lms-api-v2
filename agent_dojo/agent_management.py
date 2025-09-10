


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

#Function to create a list of agents and return
def get_agents_list() -> List[Agent]:
    digitalTwinAgent = Agent(
        id= "digital_twin_agent",
        name="Digital Twin Agent",
        version="1.0",
        goal="""Create an imaginary persona based on data provided and update the digital twin with data as much as possible.If existing_digital_twin information is provided, update it with new or changed information based on clear signals in data""",
        inputs=[
            AgentInputType(input_desc="Website traffic data", input_type="textarea", name="data"),
            AgentInputType(input_desc="Existing Digital twin if any", input_type="textarea", name="existing_digital_twin")
        ],
        outputs=["Updated/New Digital twin"],
        metrics={"Data processed": 100, "Digital twins created": 78, "Digital twins updated": 23, "Cost this month": 20000},
        endpoint_for_testing="test_digital_twin_agent"
    )
    leadImageGenerationAgent = Agent(
        id= "lead_image_generation_agent",
        name="Image generation Agent",
        version="1.0",
        goal="Generate image of digital twin based on persona",
        inputs=[
            AgentInputType(input_desc="Digital Twin profile", input_type="textarea", name="digital_twin_profile")
        ],
        outputs=["Digital Twin image"],
        metrics={"Photos generated": 34, "Cost this month": 20000},
        endpoint_for_testing="lead_image_generation_agent"
    )
    return [digitalTwinAgent,leadImageGenerationAgent]


def get_agent(id: str) -> Agent:
     #Return agent by id
    agents = get_agents_list()
    for agent in agents:
        if agent.id == id:
            return agent
    return None