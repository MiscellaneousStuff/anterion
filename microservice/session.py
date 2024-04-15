from dotenv import load_dotenv
load_dotenv()

import os

from fastapi import WebSocketDisconnect
from openai import OpenAI
client = OpenAI()

import subprocess

def gpt(txt, version="gpt4"):
    model = "gpt-4-turbo-preview" if version == "gpt4" else "gpt-3.5-turbo"
    try:
        # Perform OpenAI API call
        response = client.chat.completions.create(
            messages=[
                {"role": "user", "content": txt}
            ],
            model=model,
            temperature=0.2,
        )
        return response.choices[0].message.content
    except:
        return ""


class Messages:
    def __init__(self):
        self.messages = []

    def store_msg(self, msg: str, role: str):
        self.messages.append({
            "role": "user",
            "content": msg
        })

    def store_user_msg(self, msg: str):
        self.store_msg(msg, "user")

    def store_agent_msg(self, msg: str):
        self.store_msg(msg, "agent")


class Session:
    def __init__(self, websocket):
        self.websocket = websocket
        self.swe_agent_process = None
        self.messages = Messages()

    async def send_error(self, message):
        """Sends an error message to the client.

        Args:
            message: The error message to send.
        """
        await self.send({"error": True, "message": message})

    async def send_message(self, message):
        """Sends a message to the client.

        Args:
            message: The message to send.
        """
        await self.send({"message": message})

    async def send(self, data):
        """Sends data to the client.

        Args:
            data: The data to send.
        """
        
        if self.websocket is None:
            return
        try:
            await self.websocket.send_json(data)
        except Exception as e:
            print("Error sending data to client", e)

    async def start_listening(self):
        """Starts listening for messages from the client."""
        try:
            while True:
                try:
                    data = await self.websocket.receive_json()
                except ValueError:
                    await self.send_error("Invalid JSON")
                    continue

                action = data.get("action", None)
                print("INCOMING ACTION:", action)
                if action is None:
                    await self.send_error("Invalid event")
                    continue
                if action == "initialize":
                    await self.create_controller(data)
                elif action == "start":
                    await self.start_task(data)
                # elif action == "chat":
                #     print("RECEIVED A MESSAGE FROM THE USER, WHICH WASN'T START OR INIT!!", action)
                # else:
                #     if self.controller is None:
                #         await self.send_error("No agent started. Please wait a second...")
                #     elif action == "chat":
                #         self.controller.add_history(NullAction(), UserMessageObservation(data["message"]))
                #     else:
                #         await self.send_error("I didn't recognize this action:" + action)

        except WebSocketDisconnect as e:
            print("Client websocket disconnected", e)
            self.disconnect()

    async def create_controller(self, start_event=None):
        """Creates an AgentController instance.

        Args:
            start_event: The start event data (optional).
        """
        await self.send({"action": "initialize", "message": "Control loop started."})

    async def start_task(self, start_event):
        # 1. Tell user we start solving task
        # print("START EVENT:", start_event)
        args = start_event["args"]
        task = args["task"]

        task_as_issue = task
        # task_as_issue = gpt(f"Convert the following task into a GitHub issue style description, with a step-by-step plan for how to solve it. DO NOT PERFORM ANY EXTRA ACTIONS WHICH HAVE NOT BEEN EXPLICILTLY REQUESTED BY THE USER, SUCH AS ANY INTERACTION WITH GIT SUCH AS CREATING NEW REPOS. Keep to two sentences at most: {task}.")
        # task_as_issue = task_as_issue.replace("'", "")
        await self.send_message(f"Now solving task: {task_as_issue}")

        issue_as_run_name = gpt(f"Convert the following requested automatic programmer task into a few word description filename formatted into a way which can easily be saved as a directory name across Windows, macOS and Linux based OS's: {task}. For example, if the required task was: write a hello world script in py, then the output would be hello_world_script. ONLY RETURN THE FILENAME, DO NOT RETURN ANY PREAMBLE.")

        # 2. Initialise SWE-agent to start resolving user issue
        host_path = os.environ["DOCKER_HOST_VOLUME_PATH"]
        container_path = os.environ["DOCKER_CONTAINER_VOLUME_PATH"]
        container_name = "test"

        org_args = \
            f"""{os.environ['PYTHON_PATH']} run.py
            --model_name {os.environ["SWE_AGENT_MODEL_NAME"]}
            --issue ISSUE_GOES_HERE
            --config_file config/default_from_url.yaml
            --per_instance_cost_limit {os.environ["SWE_AGENT_PER_INSTANCE_COST_LIMIT"]}
            --run_name '{issue_as_run_name}'
            --timeout {os.environ["SWE_AGENT_TIMEOUT"]}
            --host_path {host_path}
            --container_path {container_path}
            --container_name {container_name}""".split("\n")
        org_args = " ".join([ln.strip() for ln in org_args])

        args = org_args.split(" ")
        args = [arg.replace("ISSUE_GOES_HERE", f"'{task_as_issue}'") for arg in args]
        # print("RUNNING CMD:", org_args)

        print(">>> args:", args)

        self.swe_agent_process = subprocess.Popen(
            args, cwd=os.environ["SWE_AGENT_PATH"])
        # self.swe_agent_process = subprocess.run(org_args, shell=True, cwd=os.environ["SWE_AGENT_PATH"])

    def on_agent_event(self): #, event: Observation | Action):
        """Callback function for agent events.

        Args:
            event: The agent event (Observation or Action).
        """
        # if isinstance(event, NullAction):
        #     return
        # if isinstance(event, NullObservation):
        #     return
        # event_dict = event.to_dict()
        # asyncio.create_task(self.send(event_dict), name="send event in callback")
        return
    
    def disconnect(self):
        self.websocket = None
        # if self.agent_task:
        #     self.agent_task.cancel()
        # if self.controller is not None:
        #     self.controller.command_manager.shell.close()