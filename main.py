import dspy
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from agent_dojo.tools.file_utils import get_persona_photographs_directory
from fastapi.middleware.cors import CORSMiddleware
from agent_dojo.agents.DigitalTwinCreatorAgent import DigitalTwinCreatorAgent
from agent_dojo.agent_management import get_agents_list, get_agent
from agent_dojo.agents.PersonaImageGenerationAgent import PersonaImageGenerationAgent
from agent_dojo.agents.SyntheticPersonChatAgent import SyntheticPersonChatAgent
import os

app = FastAPI(title="Mirai LMS API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pydantic import BaseModel

class QuestionPayload(BaseModel):
    question: str

class DigitalTwinInputPayload(BaseModel):
    data: str
    existing_digital_twin: str = ""

@app.get("/")
async def root():
    return {"message": "Mirai LMS API is running"}

#API to trigger optimizing of the DigitalTwinCreatorAgent
@app.post("/optimize_digital_twin_agent")
async def optimize_digital_twin_agent(background_tasks: BackgroundTasks):
    background_tasks.add_task(DigitalTwinCreatorAgent.optimize)
    return {"message": "optimizing started in the background"}

@app.post("/optimize_synthetic_persona_chat_agent")
async def optimize_synthetic_persona_chat_agent(background_tasks: BackgroundTasks):
    background_tasks.add_task(SyntheticPersonChatAgent.optimize)
    return {"message": "optimizing started in the background"}



#API to run  DigitalTwinCreatorAgent
@app.post("/run_digital_twin_agent")
def run_digital_twin_agent(data, existing_digital_twin=""):
   return DigitalTwinCreatorAgent.run(data, existing_digital_twin=existing_digital_twin )

#API to run  DigitalTwinCreatorAgent
@app.post("/test_digital_twin_agent")
def test_digital_twin_agent(payload: DigitalTwinInputPayload):
   return DigitalTwinCreatorAgent.run(payload.data, existing_digital_twin=payload.existing_digital_twin)

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

@app.post("/test_lead_image_generation_agent")
def test_lead_image_generation_agent(persona: str):
   return PersonaImageGenerationAgent.run(persona )


history=dspy.History(messages=[])

@app.post("/chat_with_synthetic_persona/{lead_id}")
def chat_with_synthetic_persona(lead_id: str, payload: QuestionPayload):
    persona = PERSONA
    answer = SyntheticPersonChatAgent.run(payload.question, history, persona)
    history.messages.append({"question": payload.question, "answer": answer})
    return answer


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

PERSONA="""Persona Summary
- User U005 is likely a new parent (inferred) living in Sydney, Australia, actively seeking term life insurance to protect their spouse and child.
- They are exploring coverage options focused on family needs, including education planning, and have demonstrated clear purchase intent by starting a quote.

Personal Information
- User ID: U005
- Age: Unknown
- Gender: Unknown
- Marital Status: Married/Partnered (inferred)
- Dependents: 1 (inferred)
- Smoker Status: Unknown
- Location: Sydney, Australia
- Language: en-AU
- Timezone: Australia/Sydney

Demographic Information
- Occupation: Unknown
- Education Level: Unknown
- Household Size: Unknown

Financial Information
- Annual Income: Unknown
- Assets: Unknown
- Liabilities: Unknown
- Currency: AUD

Insurance History & Current Behavior
- Current Policies: Unknown
- Product Interests: Term life insurance with beneficiaries spouse and child (inferred)
- Beneficiaries: Spouse, child (inferred)
- Coverage Preferences: Interested in coverage planning including education goal
- Term Preference: Unknown
- Quick Quote Parameters: None explicitly provided
- Recent Actions: quote_started
- Notable Pages Viewed: New baby checklist, term life product page with beneficiaries, coverage planner tool focused on dependents and education goal

Behavioral Signals & Preferences
- Device: Smartphone (iPhone)
- OS: iOS 17
- Browser: Mobile Safari
- Screen and Viewport: 1170x2532 / 414x896
- Primary Channel/Referrer: Instagram (cpc campaign \"new_baby_term\")
- Session Metrics: Start – 2025-07-10T08:30:10Z; End – 2025-07-10T08:33:41Z; Duration – 211 sec; Pages – 4
- Language Preference: en-AU
- Tech/Privacy: DNT false; No ad blocker; Cookies enabled

Marketing & Consent
- Consent: Analytics: Yes; Marketing: Yes; Personalization: Yes
- Contactability: No email captured – user not currently contactable

Engagement & Opportunities
- Funnel Stage: Consideration/Intent (quote started)
- Messaging Preferences: Family-focused coverage, education planning, benefits for spouse and child
- Recommended Next Actions: Prompt user to complete and save quote, provide tailored term life comparisons emphasizing family and education benefits
- Conversion Potential: High given purchase intent and targeted new parent campaign"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)