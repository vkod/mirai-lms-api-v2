


from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class Agent:
    """
    A data class representing an AI agent with its core attributes and metrics.
    """
    name: str
    goal: str
    inputs: List[str]
    outputs: List[str]
    metrics: Dict[str, float]
    
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
        name="Digital Twin Agent",
        goal="""Create an imaginary persona based on data provided and update the digital twin with data as much as possible.If existing_digital_twin information is provided, update it with new or changed information based on clear signals in data""",
        inputs={"Website traffic data","Existing Digital twin if any"},
        outputs={"Updated/New Digital twin"},
        metrics={"Data processed": 100, "Digital twins created": 78, "Digital twins updated": 23, "Cost this month": 20000}
    )
    leadImageGenerationAgent = Agent(
        name="Image generation Agent",
        goal="Generate image of digital twin based on persona",
        inputs={"Digital Twin profile"},
        outputs={"Digital Twin image"},
        metrics={"Photos generated": 34, "Cost this month": 20000}
    )
    return [digitalTwinAgent,leadImageGenerationAgent]