import dspy
import os
from dspy.teleprompt import BootstrapFewShotWithRandomSearch
from openai import OpenAI
import base64
import uuid
from agent_dojo.tools.file_utils import get_persona_photographs_directory

from PIL import Image


class PersonaSummarization(dspy.Signature):
    """Create an prompt to create a realistic photograph of the persona provided by capturing all relevant details to represent the person"""
    persona: str = dspy.InputField()
    image_generation_prompt: str = dspy.OutputField()

class PersonaImageGenerationAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        self.create_image_generation_prompt= dspy.Predict(PersonaSummarization)

    def forward(self, persona):
        output= self.create_image_generation_prompt(persona=persona)
        image_id= str(uuid.uuid4())
        output.image_id=_image_generation_tool(image_id,output.image_generation_prompt)
        return output   

def run(persona: str):
    prog=PersonaImageGenerationAgent()
    with dspy.context(lm=dspy.LM('openai/gpt-4.1-mini')):
        output= prog(persona=persona)
        return output.image_id

def _image_generation_tool(image_id: str, prompt: str) -> bytes:
    client = OpenAI() 

    response = client.responses.create(
        model="gpt-4.1",
        input=prompt,
        tools=[{"type": "image_generation"}],
    )

    # Save the image to a file
    image_data = [
        output.result
        for output in response.output
        if output.type == "image_generation_call"
    ]

    if image_data:
        image_base64 = image_data[0]
        file_name=os.path.join(get_persona_photographs_directory(), f"{image_id}.png")
        with open(file_name, "wb") as f:
            f.write(base64.b64decode(image_base64))

        resize_persona_image(file_name)



def resize_persona_image(image_path, output_dir=None):
    """
    Resizes the input image to two sizes: icon (64x64) and medium (512x512).
    Saves the resized images in the output_dir (default: same as image_path).
    Returns the paths to the resized images.
    """
    if output_dir is None:
        output_dir = os.path.dirname(image_path)
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    ext = os.path.splitext(image_path)[1]

    sizes = {
        "icon": (64, 64),
        "medium": (512, 512)
    }
    output_paths = {}

    with Image.open(image_path) as img:
        for label, size in sizes.items():
            resized_img = img.copy()
            resized_img.thumbnail(size, Image.Resampling.LANCZOS)
            out_path = os.path.join(output_dir, f"{base_name}_{label}{ext}")
            resized_img.save(out_path)
            output_paths[label] = out_path

    return output_paths
