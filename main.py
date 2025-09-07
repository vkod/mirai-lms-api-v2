from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from agent_dojo.tools.file_utils import get_persona_photographs_directory
from fastapi.middleware.cors import CORSMiddleware
from agent_dojo.agents.PersonaDigitalTwinAgent import PersonaDigitalTwinAgent
from agent_dojo.agents.DigitalTwinCreatorAgent import DigitalTwinCreatorAgent
from agent_dojo.agent_management import get_agents_list, get_agent
from agent_dojo.agents.PersonaImageGenerationAgent import PersonaImageGenerationAgent
import os

app = FastAPI(title="Mirai LMS API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Mirai LMS API is running"}

#API to trigger optimizing of the PersonaDigitalTwinAgent
@app.post("/optimize_personal_digital_twin_agent")
async def optimize_personal_digital_twin_agent(background_tasks: BackgroundTasks):
    background_tasks.add_task(PersonaDigitalTwinAgent.optimize)
    return {"message": "optimizing started in the background"}

#API to run  PersonaDigitalTwinAgent
@app.post("/run_personal_digital_twin_agent")
def run_personal_digital_twin_agent(data, existing_digital_twin=""):
   return PersonaDigitalTwinAgent.run(data, existing_digital_twin=existing_digital_twin )

#API to trigger optimizing of the DigitalTwinCreatorAgent
@app.post("/optimize_digital_twin_agent")
async def optimize_digital_twin_agent(background_tasks: BackgroundTasks):
    background_tasks.add_task(DigitalTwinCreatorAgent.optimize)
    return {"message": "optimizing started in the background"}

#API to run  DigitalTwinCreatorAgent
@app.post("/run_digital_twin_agent")
def run_digital_twin_agent(data, existing_digital_twin=""):
   return DigitalTwinCreatorAgent.run(data, existing_digital_twin=existing_digital_twin )

#API to return list of agents
@app.get("/agent_list")
async def agent_list():
    return get_agents_list()

#API to return list of agents
@app.get("/agent")
async def agent(id: str):
    return get_agent(id)

#API to return list of SP
@app.get("/get_synthetic_personas")
async def get_synthetic_personas_route():
    from digital_twins.digital_twin_management import get_synthetic_personas
    return get_synthetic_personas()

#API to return SP
@app.get("/get_synthetic_persona")
async def get_synthetic_persona_route(id: str):
    from digital_twins.digital_twin_management import get_synthetic_persona
    return get_synthetic_persona(id)

@app.post("/generate_persona_image")
def generate_persona_image(persona: str):
   return PersonaImageGenerationAgent.run(persona )


# API to return persona image by image_id
@app.get("/persona_image_thumbnail/{image_id}")
async def get_persona_image_thumbnail(image_id: str):
    image_dir = get_persona_photographs_directory()
    image_path = os.path.join(image_dir, f"{image_id}_icon.png")
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image_path)

# API to return persona image by image_id
@app.get("/persona_image_medium/{image_id}")
async def get_persona_image_thumbnail(image_id: str):
    image_dir = get_persona_photographs_directory()
    image_path = os.path.join(image_dir, f"{image_id}_medium.png")
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image_path)

# API to return persona image by image_id
@app.get("/persona_image/{image_id}")
async def get_persona_image_thumbnail(image_id: str):
    image_dir = get_persona_photographs_directory()
    image_path = os.path.join(image_dir, f"{image_id}.png")
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image_path)




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)