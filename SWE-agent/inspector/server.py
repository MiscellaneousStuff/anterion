import http.server
import json
import os
import socketserver
import traceback
import yaml

from pathlib import Path
from argparse import ArgumentParser
from functools import partial


def append_exit(content):
    last_entry = content["history"][-1]
    if last_entry["role"] == "system":
        return content
    
    exit_status = content.get("info", {}).get("exit_status", None)

    if exit_status is None:
        return content

    if exit_status.startswith("submitted"):
        if "submission" in content["info"]:
            submission = content["info"]["submission"]
            content["history"].append({
                "role": "model_patch",
                "content": submission,
            })
        # else submission should be in history already
        else:
            raise ValueError("No submission in history or info")
    # elif content.get("info", {}).get("exit_status", None) is not None:
    #     content["history"].append({
    #         "role": "system",
    #         "content": f"Exited - {content['info']['exit_status']}",
    #     })
    return content


def append_patch(instance_id, content, patches, patch_type):
    if content.get("info", {}).get("exit_status", None) is not None:
        if instance_id in patches:
            content["history"].append({
                "role": f"{patch_type} Patch",
                "content": patches[instance_id],
            })
    return content


def append_results(traj_path, instance_id, content, results, results_file, scorecards, scorecards_file):
    stats = []
    model_stats = {}
    if traj_path.exists():
        data = json.loads(traj_path.read_text())
        info = data.get("info", {})
        model_stats = info.get("model_stats", {})
    instance_cost = model_stats.get("instance_cost", None)
    instance_cost = f'{instance_cost:.2f}' if instance_cost is not None else 'N/A'
    tokens_sent = model_stats.get("tokens_sent", None)
    tokens_sent = f'{tokens_sent:,}' if tokens_sent is not None else 'N/A'
    tokens_received = model_stats.get("tokens_received", None)
    tokens_received = f'{tokens_received:,}' if tokens_received is not None else 'N/A'
    api_calls = model_stats.get("api_calls", None)
    api_calls = f'{api_calls:,}' if api_calls is not None else 'N/A'
    stats.append(f"**** Run Stats ****")
    stats.append(f"Instance Cost: ${instance_cost}")
    stats.append(f"Tokens Sent: {tokens_sent}")
    stats.append(f"Tokens Received: {tokens_received}")
    stats.append(f"API Calls: {api_calls}\n")
    status = []
    if results is None:
        status.append("Evaluation results not found")
    elif "not_generated" in results and "generated" in results and "applied" in results and "resolved" in results:
        is_generated = instance_id in results["generated"]
        is_applied = instance_id in results["applied"]
        is_resolved = instance_id in results["resolved"]

        status.append("**** Statuses ****")
        status.append(
            f"  {'✅' if is_generated else '❌'} Generated (The agent was {'' if is_generated else 'not '}"
            "able to generate a pull request to address this issue)")
        status.append(
            f"  {'✅' if is_applied else '❌'} Applied (The pull request was {'' if is_applied else 'not '}"
            "successfully applied to the repo during eval)")
        status.append(
            f"  {'✅' if is_resolved else '❌'} Resolved (The pull request {'' if is_resolved else 'not '}"
            "successfully resolved the issue during eval)")
    else:
        status.append("Results format not recognized")

    if scorecards is not None:
        scorecard = [x for x in scorecards if x["instance_id"] == instance_id][0]
        if "test_results" in scorecard and "failure" in scorecard["test_results"] and (
            len(scorecard["test_results"]["failure"]["FAIL_TO_PASS"]) > 0 or
            len(scorecard["test_results"]["failure"]["PASS_TO_PASS"]) > 0
        ):
            tests_failing = [
                f"  - {x}" for x in scorecard["test_results"]["failure"]["FAIL_TO_PASS"]
            ] + [
                f"  - {x}" for x in scorecard["test_results"]["failure"]["PASS_TO_PASS"]
            ]
            status.extend(["", "**** Test Results ****", "🧪 Tests Failed"] + tests_failing[:7])
            if len(tests_failing) > 7:
                status.append(f"  ... and {len(tests_failing) - 7} more")
            status.append("")

    if status == []:
        status.append("Instance not found in results")
    else:
        status.append("---------------------------")
        status.append("Note that the evaluation results here may not be accurate or up to date, since they are computed separately from the agent run itself.")
        results_relative = results_file.resolve().relative_to(Path(__file__).resolve().parent.parent)
        status.append(f"Check {results_relative} for the most accurate evaluation results.")
        status.append("")
        status.append(f"Instance ID: {instance_id}")
        status.append("Based on results:")
        status.append(json.dumps(results, indent=4))
    eval_report = {
        "role": "Evaluation Report",
        "content": "\n".join([*stats, *status]),
    }
    content["history"].insert(0, eval_report)
    content["history"].append(eval_report)
    return content


def load_content(file_name, gold_patches, test_patches):
    with open(file_name) as infile:
        content = json.load(infile)
    results_file = Path(file_name).parent / "results.json"
    results = None
    if results_file.exists():
        with open(results_file) as infile:
            results = json.load(infile)

    scorecards_file = Path(file_name).parent / "scorecards.json"
    scorecards = None
    if scorecards_file.exists():
        with open(scorecards_file) as infile:
            scorecards = json.load(infile)

    content = append_exit(content)  # accomodate new and old format
    content = append_patch(Path(file_name).stem, content, gold_patches, "Gold")
    content = append_patch(Path(file_name).stem, content, test_patches, "Test")
    content = append_results(
        Path(file_name),
        Path(file_name).stem,
        content,
        results,
        results_file,
        scorecards,
        scorecards_file,
    )
    return content


def load_results(traj_path):
    results_file = Path(traj_path).parent / "results.json"
    if results_file.exists():
        with open(results_file) as infile:
            return json.load(infile)
    return None


def get_status(traj_path):
    results = load_results(traj_path)
    instance_id = Path(traj_path).stem
    if results is None:
        return "❓"
    elif "not_generated" in results and "generated" in results and "applied" in results and "resolved" in results:
        if instance_id in results["not_generated"]:
            return "❓"
        if instance_id in results["generated"]:
            if instance_id in results["resolved"]:
                return "✅"
            else:
                return "❌"
    return "❓"


class Handler(http.server.SimpleHTTPRequestHandler):
    file_mod_times = {}  # Dictionary to keep track of file modification times

    def __init__(self, *args, **kwargs):
        self.gold_patches = {}
        self.test_patches = {}
        if "gold_patches" in kwargs:
            self.gold_patches = kwargs.pop("gold_patches")
        if "test_patches" in kwargs:
            self.test_patches = kwargs.pop("test_patches")
        self.traj_dir = kwargs.pop('directory', '.')  # Extract directory
        super().__init__(*args, **kwargs)

    def serve_directory_info(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"directory": self.traj_dir}).encode())

    def serve_file_content(self, file_path):
        try:
            content = load_content(
                Path(self.traj_dir) / file_path,
                self.gold_patches,
                self.test_patches,
            )
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(json.dumps(content).encode())
        except FileNotFoundError:
            self.send_error(404, f"File {file_path} not found")

    def do_GET(self):
        if self.path == '/directory_info':
            self.serve_directory_info()
        elif self.path.startswith('/files'):
            self.handle_files_request()
        elif self.path.startswith('/trajectory/'):
            file_path = self.path[len('/trajectory/'):]
            self.serve_file_content(file_path)
        elif self.path.startswith('/check_update'):
            self.check_for_updates()
        else:
            super().do_GET()

    def handle_files_request(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        files = sorted(
            [
                str(file.relative_to(Path(self.traj_dir))) + " " * 4 + get_status(file)
                for file in Path(self.traj_dir).glob('**/*.traj')
            ],
            key=lambda x: str(Path(self.traj_dir) / x), reverse=True
        )
        self.wfile.write(json.dumps(files).encode())

    def check_for_updates(self):
        current_mod_times = {str(file): os.path.getmtime(file) for file in Path(self.traj_dir).glob('**/*.traj')}
        if current_mod_times != Handler.file_mod_times:
            Handler.file_mod_times = current_mod_times
            self.send_response(200)  # Send response that there's an update
        else:
            self.send_response(204)  # Send no content response if no update
        self.end_headers()

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()


def main(data_path, directory, port):
    data = []
    if data_path is not None:
        if data_path.endswith(".jsonl"):
            data = [json.loads(x) for x in open(data_path).readlines()]
        elif data_path.endswith(".json"):
            data = json.load(open(data_path))
    elif "args.yaml" in os.listdir(directory):
        args = yaml.safe_load(open(os.path.join(directory, "args.yaml")))
        if "environment" in args and "data_path" in args["environment"]:
            data_path = os.path.join(
                Path(__file__).parent, "..",
                args["environment"]["data_path"]
            )
            if os.path.exists(data_path):
                data = json.load(open(data_path, "r"))

    gold_patches = {
        d["instance_id"]: d["patch"]
        if "patch" in d else None for d in data
    }
    test_patches = {
        d["instance_id"]: d["test_patch"]
        if "test_patch" in d else None for d in data
    }

    handler_with_directory = partial(
        Handler,
        directory=directory,
        gold_patches=gold_patches,
        test_patches=test_patches,
    )
    try:
        with socketserver.TCPServer(("", port), handler_with_directory) as httpd:
            print(f"Serving at http://localhost:{port}")
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 48:
            print(f"ERROR: Port ({port}) is already in use. Try another port with the --port flag.")
        else:
            raise e


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--data_path", type=str, help="Path to dataset that was used for the trajectories")
    parser.add_argument("--directory", type=str, help="Directory to serve", default="./trajectories", nargs='?')
    parser.add_argument("--port", type=int, help="Port to serve", default=8000)
    args = parser.parse_args()
    main(**vars(args))
