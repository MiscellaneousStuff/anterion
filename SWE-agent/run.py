import json
import logging
import os
import re
import traceback
import yaml

from dataclasses import dataclass
from getpass import getuser
from pathlib import Path
from rich.logging import RichHandler
from simple_parsing import parse
from simple_parsing.helpers import FrozenSerializable, FlattenedAccess
from sweagent import (
    Agent,
    AgentArguments,
    EnvironmentArguments,
    ModelArguments,
    SWEEnv,
    get_data_path_name,
)
from swebench import KEY_INSTANCE_ID, KEY_MODEL, KEY_PREDICTION
from unidiff import PatchSet

handler = RichHandler(show_time=False, show_path=False)
handler.setLevel(logging.DEBUG)
logger = logging.getLogger("run_dev")
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.propagate = False
logging.getLogger("simple_parsing").setLevel(logging.WARNING)

import requests
import json

def convert_issue_to_instance_id(issue: str) -> str:
    try:
        first_sentence = issue.split(".")[0]
        sanitise_sentence = first_sentence.replace(" ", "-").lower()
        return sanitise_sentence
    except:
        return "generic_issue"

def send_log(txt):
    url = "http://localhost:3000/agent-send-text"
    payload = json.dumps({
        "session_id": "test",
        "message": txt
    })
    headers = {
        'Content-Type': 'application/json'
    }
    _ = requests.request("POST", url, headers=headers, data=payload)

@dataclass(frozen=True)
class ScriptArguments(FlattenedAccess, FrozenSerializable):
    environment: EnvironmentArguments
    agent: AgentArguments
    instance_filter: str = ".*"  # Only run instances that completely match this regex
    skip_existing: bool = True  # Skip instances with existing trajectories
    suffix: str = ""
    issue: str = ""
    run_name: str = ""

    # @property
    # def run_name(self):
    #     """Generate a unique name for this run based on the arguments."""
    #     model_name = args.agent.model.model_name.replace(":", "-")
    #     data_stem = get_data_path_name(args.environment.data_path)
    #     config_stem = Path(args.agent.config_file).stem

    #     temp = args.agent.model.temperature
    #     top_p = args.agent.model.top_p

    #     per_instance_cost_limit = args.agent.model.per_instance_cost_limit
    #     install_env = args.environment.install_environment

    #     return (
    #         f"{model_name}__{data_stem}__{config_stem}__t-{temp:.2f}__p-{top_p:.2f}"
    #         + f"__c-{per_instance_cost_limit:.2f}__install-{int(install_env)}"
    #         + (f"__{self.suffix}" if self.suffix else "")
    #     )
    

def save_arguments(traj_dir, args):
    """Save the arguments to a yaml file to the run's trajectory directory."""
    log_path = traj_dir / "args.yaml"

    if log_path.exists():
        try:
            other_args = args.load_yaml(log_path)
            if (args.dumps_yaml() != other_args.dumps_yaml()):  # check yaml equality instead of object equality
                logger.warning("**************************************************")
                logger.warning("Found existing args.yaml with different arguments!")
                logger.warning("**************************************************")
        except Exception as e:
            logger.warning(f"Failed to load existing args.yaml: {e}")

    with log_path.open("w") as f:
        args.dump_yaml(f)


def should_skip(args, traj_dir, instance_id):
    """Check if we should skip this instance based on the instance filter and skip_existing flag."""
    # Skip instances that don't match the instance filter
    if re.match(args.instance_filter, instance_id) is None:
        logger.info(f"Instance filter not matched. Skipping instance {instance_id}")
        return True

    # If flag is set to False, don't skip
    if not args.skip_existing:
        return False

    # Check if there's an existing trajectory for this instance
    log_path = traj_dir / (instance_id + ".traj")
    if log_path.exists():
        with log_path.open("r") as f:
            data = json.load(f)
        # If the trajectory has no exit status, it's incomplete and we will redo it
        exit_status = data["info"].get("exit_status", None)
        if exit_status == "early_exit" or exit_status is None:
            logger.info(f"Found existing trajectory with no exit status: {log_path}")
            logger.info("Removing incomplete trajectory...")
            os.remove(log_path)
        else:
            logger.info(f"⏭️ Skipping existing trajectory: {log_path}")
            return True
    return False


def save_predictions(traj_dir, instance_id, info):
    output_file = Path(traj_dir) / "all_preds.jsonl"
    model_patch = info["submission"] if "submission" in info else None
    datum = {
        KEY_MODEL: Path(traj_dir).name,
        KEY_INSTANCE_ID: instance_id,
        KEY_PREDICTION: model_patch,
    }
    with open(output_file, "a+") as fp:
        print(json.dumps(datum), file=fp, flush=True)
    logger.info(f"Saved predictions to {output_file}")


def custom_main(args: ScriptArguments):
    logger.info(f"📙 Arguments: {args.dumps_yaml()}")
    agent = Agent("primary", args.agent)

    env = SWEEnv(args.environment)

    traj_dir = Path("trajectories") / Path(getuser()) / args.run_name
    os.makedirs(traj_dir, exist_ok=True)

    save_arguments(traj_dir, args)

    try:
        # Reset environment
        instance_id = convert_issue_to_instance_id(args.issue)
        env.data[0]["instance_id"] = instance_id

        observation, info = env.reset(0)
        # if info is None:
        #     continue
        if info is None:
            exit()

        setup_args = {
            "issue": args.issue,
            "files": [],
            "test_files": [],
            "tests": []
        }
        info = agent.run(
            setup_args=setup_args,
            env=env,
            observation=observation,
            traj_dir=traj_dir,
            return_type="info",
        )
        save_predictions(traj_dir, instance_id, info)

    except KeyboardInterrupt:
        logger.info("Exiting InterCode environment...")
        env.close()
    except Exception as e:
        traceback.print_exc()
        logger.warning(f"❌ Failed on {env.record['instance_id']}: {e}")
        env.reset_container()


if __name__ == "__main__":
    defaults = ScriptArguments(
        suffix="",
        environment=EnvironmentArguments(
            image_name="swe-agent",
            data_path="princeton-nlp/SWE-bench_Lite",
            split="dev",
            verbose=True,
            install_environment=True,
        ),
        skip_existing=True,
        agent=AgentArguments(
            model=ModelArguments(
                model_name="gpt4",
                total_cost_limit=0.0,
                per_instance_cost_limit=2.0,
                temperature=0.2,
                top_p=0.95,
            ),
            config_file="config/default.yaml",
        ),
    )

    # Nicer yaml dumping of multiline strings
    def multiline_representer(dumper, data):
        """configures yaml for dumping multiline strings
        Ref: https://stackoverflow.com/questions/8640959/how-can-i-control-what-scalar-form-pyyaml-uses-for-my-data
        """
        if data.count("\n") > 0:  # check for multiline string
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
        return dumper.represent_scalar("tag:yaml.org,2002:str", data)

    yaml.add_representer(str, multiline_representer)

    args = parse(ScriptArguments, default=defaults, add_config_path_arg=False)

    # print("ARGS:", args)
    
    # main(args)
    custom_main(args)