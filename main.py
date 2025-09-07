from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from agent_dojo.agents.PersonaDigitalTwinAgent import PersonaDigitalTwinAgent
from agent_dojo.agents.DigitalTwinCreatorAgent import DigitalTwinCreatorAgent
from agent_dojo.agent_management import get_agents_list

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)