from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import subprocess
import sys
import os
import json
import re
from dotenv import load_dotenv
from typing import Annotated, Literal
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from langchain_together import ChatTogether
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from git import Repo
from langchain_core.messages import SystemMessage, HumanMessage
import uuid
import threading
import queue
import time

load_dotenv()

app = Flask(__name__)
CORS(app)

llm = ChatTogether(
    model="mistralai/Mixtral-8x7B-Instruct-v0.1",
    temperature=0.7,
    max_tokens=512
)

class State(TypedDict):
    repo_path : str
    files : dict[str,str]
    commits: list[str] = []
    file_list: list[str] = []
    current_idx : int = 0
    modified_path : str = ""
    new_content : str = ""
    next : str = ""
    modified_files : list[str] = []

# Global queue for streaming output
output_queue = queue.Queue()

def repo_load_context(state:State, n_commits = 5):
    path = state["repo_path"]
    repo = Repo(path)
    file_paths = repo.git.ls_files().split("\n")
    files = {}
    for p in file_paths:
        abs_path = os.path.join(repo.working_tree_dir, p)
        try:
            with open(abs_path,"r",encoding="utf-8") as f:
                files[p] = f.read()
        except UnicodeDecodeError:
            continue
    commits = [f"{c.hexsha[:7]}: {c.message.strip()}" for c in repo.iter_commits("HEAD", max_count=n_commits)]

    return {
        **state,
        "files": files,
        "commits": commits,
        "file_list": list(files.keys()),
        "current_idx": 0,
    }

def extract_json_from_response(text: str):
    match = re.search(r"\[\s*\{.*\}\s*\]", text, re.DOTALL)
    if match:
        return match.group(0)
    else:
        raise ValueError("No JSON array found in model response")

def action_lister(state:State, prompt:str):
    files = state["files"]
    commits = state["commits"]

    files_summary = "\n".join([f"{k}: {len(v)} chars" for k, v in files.items()])
    commits_summary = "\n".join(commits)

    system_prompt = f"""
        You are an AI software engineer. A user gave you this task: "{prompt}"

        Based on the current repo files and recent commits, list which files you'll need to modify or create and what you will do.
        Only include tracked or to-be-created editable files (.py, .js, .ts, etc).
        If you need to create new files, list them in the plan too.

        Summarize your plan and give step-by-step actions.

        Recent Commits:
        {commits_summary}

        Files in repo:
        {files_summary}

        Please provide the plan as a JSON list of objects with "file" and "action" keys, for example:

        [
          {{"file": "src/components/NavBar.tsx", "action": "Add login/logout button"}},
          {{"file": "src/components/ui/dialog.tsx", "action": "Create login modal dialog"}}
        ]
    """

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=prompt),
    ]

    response = llm.invoke(messages)

    return {
        **state,
        "plan": response.content,
        "next": "rewrite_files"
    }

def rewrite_files(state: State):
    files = state["files"]
    plan = json.loads(state["plan"])
    idx = state["current_idx"]

    if idx >= len(plan):
        return {**state, "next": END}

    entry = plan[idx]
    path = entry["file"]
    content = files.get(path, "")  # Empty means new file

    # Skip non-editable file types
    if not path.endswith((".ts", ".tsx", ".js", ".jsx", ".py")):
        return {
            **state,
            "current_idx": idx + 1,
            "next": "rewrite_files"
        }

    if content.strip() == "":
        # New file
        system_prompt = f"""
You are creating a **new file** for this project based on the following plan.

--- PLAN ITEM ---
File: {path}
Action: {entry["action"]}

Generate the full file content.
        """
    else:
        # Modify existing file
        system_prompt = f"""
You are modifying the following file in response to the given plan item.

Do not change anything unrelated. Do not reformat the whole file. Only implement the action needed.

--- PLAN ITEM ---
File: {path}
Action: {entry["action"]}

--- FILE CONTENT BEFORE ---
{content}
        """

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="Return the full file content. If no changes are needed, just say 'NO_CHANGE'.")
    ]

    response = llm.invoke(messages)

    if response.content.strip().upper() == "NO_CHANGE":
        print(f"⏭️ Skipped: {path}")
    else:
        new_content = response.content.strip()
        state["files"][path] = new_content
        state["modified_path"] = path
        state["new_content"] = new_content
        if path not in state["modified_files"]:
            state["modified_files"].append(path)
        print(f"✅ Modified or created: {path}")

    return {
        **state,
        "current_idx": idx + 1,
        "next": "rewrite_files"
    }

def commit_to_git(state: State):
    branch_name = f"feature--{uuid.uuid4().hex[:6]}"
    repo_path = state["repo_path"]

    modified_files = state.get("modified_files", [])

    if not modified_files:
        print("No modified files to commit.")
        return {**state, "next": END}

    subprocess.run(["git", "checkout", "-b", branch_name], cwd=repo_path, check=True)

    for path in modified_files:
        abs_path = os.path.join(repo_path, path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(state["files"][path])

    subprocess.run(["git", "add"] + modified_files, cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "featurea added by Ishaan's Cursor"], cwd=repo_path, check=True)
    subprocess.run(["git", "push", "-u", "origin", branch_name], cwd=repo_path, check=True)

    print(f"✅ Changes committed and pushed to branch: {branch_name}")

    return {**state, "committed_branch": branch_name, "next": END}

def stream_print(*args, **kwargs):
    """Custom print function that streams output to the queue"""
    message = ' '.join(map(str, args))
    output_queue.put(message)
    # Don't call builtins.print here to avoid recursion

def execute_workflow(prompt: str):
    """Execute the workflow in a separate thread"""
    try:
        # Store original print function
        import builtins
        original_print = builtins.print
        
        # Replace print function
        builtins.print = stream_print
        
        # Initialize state
        state = {
            "repo_path": "/Users/ashish/cosmic-aesthetic-portfolio",
            "files": {},
            "commits": [],
            "file_list": [],
            "current_idx": 0,
            "modified_path": "",
            "new_content": "",
            "next": "",
            "modified_files": []
        }
        
        # Load repo context
        state = repo_load_context(state)
        print("Files loaded:", list(state["files"].keys())[:5])
        print("Commits:", state["commits"])
        
        # Generate action plan
        state = action_lister(state, prompt)
        
        # Extract and parse plan
        try:
            raw_json = extract_json_from_response(state["plan"])
            plan = json.loads(raw_json)
        except Exception as e:
            print("❌ Failed to extract JSON plan:", e)
            output_queue.put("DONE")
            return
        
        state["plan"] = json.dumps(plan)
        print("📋 Plan:", json.dumps(plan, indent=2))
        
        # Execute file modifications
        while state["next"] == "rewrite_files":
            state = rewrite_files(state)
        
        # Commit changes
        state = commit_to_git(state)
        
        print("🎉 Workflow completed successfully!")
        if state.get('committed_branch'):
            branch_name = state['committed_branch']
            github_url = f"https://github.com/ishaan-arora-1/cosmic-aesthetic-portfolio/tree/{branch_name}"
            print(f"Branch: {branch_name}")
            print(f"GitHub: {github_url}")
            print(f"Pull Request: https://github.com/ishaan-arora-1/cosmic-aesthetic-portfolio/pull/new/{branch_name}")
        
        output_queue.put("DONE")
        
    except Exception as e:
        # Use original print for error logging to avoid recursion
        import builtins
        builtins.print = original_print
        print(f"❌ Error: {e}")
        output_queue.put("DONE")
    finally:
        # Restore original print function
        import builtins
        builtins.print = original_print

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/execute', methods=['POST'])
def execute():
    data = request.get_json()
    prompt = data.get('prompt', '')
    
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    
    # Clear the queue
    while not output_queue.empty():
        output_queue.get()
    
    # Start the workflow in a separate thread
    thread = threading.Thread(target=execute_workflow, args=(prompt,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': 'Workflow started'})

@app.route('/stream')
def stream():
    def generate():
        while True:
            try:
                message = output_queue.get(timeout=1)
                if message == "DONE":
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                    break
                else:
                    yield f"data: {json.dumps({'type': 'output', 'message': message})}\n\n"
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, port=5000) 