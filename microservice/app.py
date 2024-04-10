# from opendevin.server.session import Session
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
# import agenthub # noqa F401 (we import this to get the agents registered)
# import litellm 
# from opendevin.agent import Agent
# from opendevin import config
from typing import Dict

from session import *

from pydantic import BaseModel

# Define a Pydantic model that represents the expected structure of your JSON body
class Message(BaseModel):
    session_id: str
    message: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: Dict[str, Session] = {}

# This endpoint receives events from the client (i.e. the browser)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session = Session(websocket)
    sessions["test"] = session
    print("sessions:", sessions)
    # # TODO: should this use asyncio instead of await?
    await session.start_listening()
    # return None

@app.post("/agent-send-text")
async def agent_send_text(message: Message):
    print("SENDING TEXT?!?!?!??!?!??!?!?:", message.message)
    # print(f"ATTEMPTING TO SEND: {message.message} to {message.session_id}")
    # await sessions[message.session_id].send_message(message.message)
    # await sessions[message.session_id].send({
    #     "action": "think",
    #     "message": message.message
    # })
    await sessions[message.session_id].send({
        "observation": "chat",
        "content": message.message,
        "extras": {},
        "message": message.message,
    })

@app.post("/agent-cli-obs")
async def agent_cli_obs(message: Message):
    print("SENDING OBS?!?!?!??!?!??!?!?:", message.message)
    await sessions[message.session_id].send({
        "observation": "run",
        "content": message.message,
        "extras": {},
        "message": "",
    })

@app.post("/agent-cli-act")
async def agent_cli_act(message: Message):
    print("SENDING ACT?!?!?!??!?!??!?!?:", message.message)
    await sessions[message.session_id].send({
        "action": "run",
        "args": {
            "command": message.message
        },
        "message": ""
    })

@app.get("/litellm-models")
async def get_litellm_models():
    """
    Get all models supported by LiteLLM.
    """
    return [] # litellm.model_list

@app.get("/litellm-agents")
async def get_litellm_agents():
    """
    Get all agents supported by LiteLLM.
    """
    return [] # Agent.listAgents()

@app.get("/default-model")
def read_default_model():
    return [] # config.get_or_error("LLM_MODEL")