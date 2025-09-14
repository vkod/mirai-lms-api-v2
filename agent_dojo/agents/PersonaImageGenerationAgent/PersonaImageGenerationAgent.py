import dspy
import os
import sys
from openai import OpenAI
import base64
from agent_dojo.tools.file_utils import get_persona_photographs_directory


# Add parent directories to path for storage imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from agent_dojo.tools.lmtools import log_lm_execution_cost
from storage.persona_image_storage import PersonaImageStorage
from utils.async_helper import run_async

model_for_execution=dspy.LM('openai/gpt-4.1-mini')

class PersonaSummarization(dspy.Signature):
    """Create an prompt to create a realistic photograph of the persona provided by capturing all relevant details to represent the person"""
    persona: str = dspy.InputField()
    image_generation_prompt: str = dspy.OutputField()

class PersonaImageGenerationAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        self.create_image_generation_prompt= dspy.Predict(PersonaSummarization)

    def forward(self, persona, lead_id=None):
        output= self.create_image_generation_prompt(persona=persona)
        return _image_generation_tool_gpt(lead_id,output.image_generation_prompt)

def run(persona: str, lead_id: str = None):
    prog=PersonaImageGenerationAgent()

    lm=model_for_execution
    with dspy.context(lm=lm):
        prog(persona=persona, lead_id=lead_id)
        execution_cost=log_lm_execution_cost(lm,"DigitalTwinCreatorAgent")

        return {
            "generated_image_id": lead_id,
            "execution_cost": execution_cost
        }



def _image_generation_tool_gpt(image_id: str, prompt: str) -> bytes:
    client = OpenAI() 

    img = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        n=1,
        size="1024x1024",
        quality="medium",
        output_format="jpeg"
    )

    image_bytes = base64.b64decode(img.data[0].b64_json)
    file_name=os.path.join(get_persona_photographs_directory(), f"{image_id}.jpeg")
    with open(file_name, "wb") as f:
        f.write(image_bytes)

    _save_persona_images(file_name,image_id)


def _image_generation_tool(image_id: str, prompt: str) -> bytes:
    client = OpenAI() 

    img = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        n=1,
        size="1024x1024",
        quality="standard",
        response_format="b64_json" ,
        output_format="jpeg"
    )

    image_bytes = base64.b64decode(img.data[0].b64_json)
    file_name=os.path.join(get_persona_photographs_directory(), f"{image_id}.jpeg")
    with open(file_name, "wb") as f:
        f.write(image_bytes)
        _save_persona_images(file_name,image_id)



def _save_persona_images(image_path, lead_id):
    """
    Save persona images to Azure Storage in multiple sizes.
    """
    # Read the full-size image
    with open(image_path, 'rb') as f:
        full_image_bytes = f.read()
    
    # Save to Azure Storage
    try:
        storage = PersonaImageStorage()
        
        # Save all sizes to Azure storage
        azure_urls = run_async(
            storage.save_persona_image(lead_id, full_image_bytes)
        )
        
        #Delete the file for clean up
        os.remove(image_path)

        print(f"Persona images saved to Azure storage for lead_id: {lead_id}")
        print(f"Azure URLs: {azure_urls}")
        
    except Exception as e:
        print(f"Warning: Could not save to Azure storage: {e}")
    
