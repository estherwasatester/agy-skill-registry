#!/usr/bin/env python3
"""
CLI wrapper for the Google Cloud Skill Registry (Vertex AI SDK).
Allows searching, pulling, pushing, and listing agent skills in a Google Cloud project.
"""

import os
import sys
import base64
import io
import zipfile
import argparse
import re
from datetime import datetime
import yaml

# Disable context-aware client certs to bypass mTLS DECODER routine format issues in python environments
os.environ["CLOUDSDK_CONTEXT_AWARE_USE_CLIENT_CERTIFICATE"] = "false"
os.environ["GOOGLE_API_USE_CLIENT_CERTIFICATE"] = "false"

import vertexai

def get_client(project=None, location=None):
    """Initializes and returns a Vertex AI Client."""
    # Find Google Cloud Project ID
    project_id = project or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
    if not project_id:
        # Try to read active gcloud config as a fallback
        try:
            import subprocess
            res = subprocess.run(
                ["gcloud", "config", "get-value", "project"],
                capture_output=True,
                text=True,
                check=False
            )
            if res.returncode == 0 and res.stdout.strip():
                project_id = res.stdout.strip()
        except Exception:
            pass

    if not project_id:
        print("ERROR: Google Cloud Project ID not set. Set GOOGLE_CLOUD_PROJECT or pass --project.", file=sys.stderr)
        sys.exit(1)

    location_id = location or os.getenv("GOOGLE_CLOUD_LOCATION") or "us-central1"

    # Initialize vertexai
    vertexai.init(project=project_id, location=location_id)
    return vertexai.Client(project=project_id, location=location_id)

def parse_skill_md(filepath: str) -> tuple[str, str]:
    """Parses SKILL.md file to get the skill name and description."""
    name = "Untitled Skill"
    description = "No description provided."
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            if content.startswith("---"):
                end_idx = content.find("---", 3)
                if end_idx != -1:
                    yaml_part = content[3:end_idx]
                    try:
                        data = yaml.safe_load(yaml_part)
                        if data:
                            name = data.get("name", name)
                            description = data.get("description", description)
                    except yaml.YAMLError as yaml_e:
                        print(f"Warning parsing frontmatter YAML: {yaml_e}", file=sys.stderr)
                        match_name = re.search(r"^name:\s*(.+)$", yaml_part, re.M)
                        if match_name:
                            name = match_name.group(1).strip()
                        match_desc = re.search(r"^description:\s*(?:>-\s*)?(.+)$", yaml_part, re.M)
                        if match_desc:
                            description = match_desc.group(1).strip()
    except IOError as e:
        print(f"Failed to parse {filepath}: {e}", file=sys.stderr)
    return name, description

def clean_id(name: str) -> str:
    """Cleans a name to make it suitable as a skill ID (lowercase, alphanumeric, dashes)."""
    val = name.lower()
    val = re.sub(r"[^a-z0-9\-]", "-", val)
    val = re.sub(r"-+", "-", val)
    return val.strip("-")

def handle_search(args):
    """Searches for skills matching the query."""
    client = get_client(args.project, args.location)
    query = args.query
    top_k = args.top_k or 5

    print(f"Searching Skill Registry for: '{query}' (top_k={top_k})...")
    try:
        response = client.skills.retrieve(
            query=query,
            config={"top_k": top_k}
        )
        skills = response.retrieved_skills or []
        print(f"\nFound {len(skills)} matching skill(s):\n")
        for i, retrieved in enumerate(skills):
            print(f"[{i+1}] ID / Name: {retrieved.skill_name}")
            print(f"    Description: {retrieved.description}")
            print("-" * 50)
    except Exception as e:
        print(f"ERROR: Retrieval failed: {e}", file=sys.stderr)
        sys.exit(1)

def list_skills_in_registry(project: str = None, location: str = None) -> str:
    """Lists all modular agent skills currently registered in the GCP Skill Registry.

    Args:
        project: Optional GCP Project ID override.
        location: Optional GCP Location override (default: us-central1).

    Returns:
        A string summarizing all registered skills with their IDs, display names, and descriptions.
    """
    try:
        client = get_client(project, location)
        skills = client.skills.list()
        skills_list = list(skills)
        if not skills_list:
            return "No registered skills found in the registry."
        
        out = [f"Found {len(skills_list)} skill(s) in registry:\n"]
        for i, s in enumerate(skills_list):
            out.append(f"[{i+1}] ID / Name: {s.name}")
            out.append(f"    Display Name: {s.display_name}")
            out.append(f"    Description: {s.description}")
            out.append(f"    State: {s.state}")
            out.append("-" * 50)
        return "\n".join(out)
    except Exception as e:
        return f"ERROR: Failed to list skills: {e}"

def pull_skill_from_registry(skill_name: str, dest_dir: str = "", project: str = None, location: str = None) -> str:
    """Downloads a registered skill by name/ID from the GCP Skill Registry and extracts its files locally.

    Args:
        skill_name: The unique ID or name of the registered skill in the registry.
        dest_dir: Optional local path to extract the skill files to. Defaults to a subfolder named after the skill.
        project: Optional GCP Project ID override.
        location: Optional GCP Location override.

    Returns:
        A success or error status message.
    """
    try:
        client = get_client(project, location)
        
        # Determine destination directory
        dest = dest_dir
        if not dest:
            dest = os.path.join(os.getcwd(), skill_name)

        skill = client.skills.get(name=skill_name)
        if not skill.zipped_filesystem:
            return f"ERROR: Skill '{skill_name}' has no zipped filesystem payload."

        os.makedirs(dest, exist_ok=True)
        zip_data = base64.b64decode(skill.zipped_filesystem)
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_ref:
            zip_ref.extractall(dest)
        return f"SUCCESS: Skill '{skill_name}' successfully retrieved and extracted to: '{dest}'."
    except Exception as e:
        return f"ERROR: Failed to pull skill: {e}"

def push_local_skill_to_registry(local_path: str, display_name: str = "", description: str = "", skill_id: str = "", project: str = None, location: str = None) -> str:
    """Packages a local skill directory (must contain a SKILL.md file) and publishes it to the GCP Skill Registry.

    Args:
        local_path: Local path to the directory containing the skill package.
        display_name: Optional custom display name of the skill. If omitted, parsed from SKILL.md.
        description: Optional custom description of what the skill does. If omitted, parsed from SKILL.md.
        skill_id: Optional custom skill ID (will be cleaned to lowercase/dashes). If omitted, generated from folder name.
        project: Optional GCP Project ID override.
        location: Optional GCP Location override.

    Returns:
        A success message containing the published skill details, or an error message.
    """
    try:
        client = get_client(project, location)
        abs_local_path = os.path.abspath(local_path)

        if not os.path.exists(abs_local_path):
            return f"ERROR: Local path '{local_path}' does not exist."

        # Resolve display_name and description from SKILL.md if present
        md_name, md_desc = None, None
        for filename in ["SKILL.md", "skill.md"]:
            filepath = os.path.join(abs_local_path, filename)
            if os.path.exists(filepath):
                md_name, md_desc = parse_skill_md(filepath)
                break

        resolved_display_name = display_name or md_name or os.path.basename(abs_local_path) or "Untitled Skill"
        resolved_description = description or md_desc or "Skill published from local workspace."

        resolved_skill_id = skill_id
        if not resolved_skill_id:
            base_id = clean_id(md_name or os.path.basename(abs_local_path) or "skill")
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            resolved_skill_id = f"{base_id}-{ts}"
        else:
            resolved_skill_id = clean_id(resolved_skill_id)

        skill = client.skills.create(
            display_name=resolved_display_name,
            description=resolved_description,
            config={
                "skill_id": resolved_skill_id,
                "local_path": abs_local_path
            }
        )
        return f"SUCCESS: Local skill successfully published!\n  Resource Name: {skill.name}\n  Skill ID:      {resolved_skill_id}\n  State:         {skill.state}"
    except Exception as e:
        return f"ERROR: Publication failed: {e}"

def handle_list(args):
    """Lists all skills in the registry."""
    print("Listing skills in registry...")
    res = list_skills_in_registry(args.project, args.location)
    print(res)

def handle_pull(args):
    """Retrieves and extracts a skill's filesystem."""
    print(f"Pulling skill '{args.skill_name}' from registry...")
    res = pull_skill_from_registry(args.skill_name, args.dest, args.project, args.location)
    print(res)

def handle_push(args):
    """Packages and publishes a local skill to the Skill Registry."""
    print(f"Pushing local skill package from '{args.local_path}'...")
    res = push_local_skill_to_registry(
        args.local_path, args.display_name, args.description, args.skill_id, args.project, args.location
    )
    print(res)

def handle_run(args):
    """Executes an ADK Agent turn using the GCP Skill Registry and ADK Runner."""
    import asyncio
    asyncio.run(async_handle_run(args))

async def async_handle_run(args):
    from functools import cached_property
    try:
        from google.adk import Agent, Runner
        from google.adk.models import Gemini
        from google.adk.integrations.skill_registry.gcp_skill_registry import GCPSkillRegistry
        from google.adk.tools.skill_toolset import SkillToolset
        from google.genai import Client, types
        from google.adk.sessions.in_memory_session_service import InMemorySessionService
    except ImportError as e:
        print(f"ERROR: Failed to import Google ADK: {e}", file=sys.stderr)
        print("Please ensure you have installed the requirements: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)

    project_id = args.project or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
    if not project_id:
        # Try to read active gcloud config as a fallback
        try:
            import subprocess
            res = subprocess.run(
                ["gcloud", "config", "get-value", "project"],
                capture_output=True,
                text=True,
                check=False
            )
            if res.returncode == 0 and res.stdout.strip():
                project_id = res.stdout.strip()
        except Exception:
            pass

    if not project_id:
        print("ERROR: Google Cloud Project ID not set. Set GOOGLE_CLOUD_PROJECT or pass --project.", file=sys.stderr)
        sys.exit(1)

    location_id = args.location or os.getenv("GOOGLE_CLOUD_LOCATION") or "us-central1"

    print(f"Initializing GCPSkillRegistry on project '{project_id}' in '{location_id}'...")
    registry = GCPSkillRegistry(project_id=project_id, location=location_id)
    skill_toolset = SkillToolset(skills=[], registry=registry)

    # Dynamic closures to act as python tools for the ADK Agent, capturing the resolved project & location context
    def list_remote_skills() -> str:
        """Lists all modular agent skills currently registered in the GCP Skill Registry.

        Returns:
            A string summarizing all registered skill IDs, names, display names, and descriptions.
        """
        return list_skills_in_registry(project=project_id, location=location_id)

    def download_and_extract_skill(skill_id: str, destination_folder: str = "") -> str:
        """Downloads a registered skill by name/ID from the GCP Skill Registry and extracts its files locally.

        Args:
            skill_id: The unique ID or name of the registered skill in the registry.
            destination_folder: Optional local folder path to extract files. Defaults to a folder named after the skill.

        Returns:
            A status or success message with extraction details.
        """
        return pull_skill_from_registry(
            skill_name=skill_id, dest_dir=destination_folder, project=project_id, location=location_id
        )

    def publish_and_register_skill(local_folder: str, display_name: str = "", description: str = "", skill_id: str = "") -> str:
        """Packages and publishes a local skill directory (must contain a SKILL.md file) to the GCP Skill Registry.

        Args:
            local_folder: Local directory path containing the skill package.
            display_name: Optional custom display name of the skill.
            description: Optional custom description of what the skill does.
            skill_id: Optional custom skill ID (lowercase, dashes).

        Returns:
            A success message containing the published skill details.
        """
        return push_local_skill_to_registry(
            local_path=local_folder,
            display_name=display_name,
            description=description,
            skill_id=skill_id,
            project=project_id,
            location=location_id
        )

    # Dynamic subclass to ensure we use Vertex AI client with explicit project & location
    class GCPVertexGemini(Gemini):
        @cached_property
        def api_client(self) -> Client:
            return Client(vertexai=True, project=project_id, location=location_id)

    print(f"Assembling ADK Agent using model '{args.model}'...")
    agent = Agent(
        model=GCPVertexGemini(model=args.model),
        name="cli_skill_assistant",
        description="A CLI agent that automatically discovers, lists, downloads, and publishes registered skills",
        instruction=(
            "You are a helpful skill registry assistant. You have full access to discover, search, load, "
            "list, pull, and push skills to/from your Google Cloud Skill Registry.\n"
            "If the user asks to list skills, use 'list_remote_skills'.\n"
            "If the user asks to pull/download a skill, use 'download_and_extract_skill'.\n"
            "If the user asks to publish/push/register a skill, use 'publish_and_register_skill'.\n"
            "If the user asks to perform other remote actions or search for capabilities, "
            "use 'search_skills' and 'load_skill'."
        ),
        tools=[skill_toolset, list_remote_skills, download_and_extract_skill, publish_and_register_skill]
    )

    session_service = InMemorySessionService()
    runner = Runner(
        session_service=session_service,
        agent=agent,
        app_name="cli_skill_registry_app",
        auto_create_session=True
    )

    new_message = types.Content(
        parts=[types.Part.from_text(text=args.prompt)]
    )

    print(f"\nExecuting agent turn. Prompt: '{args.prompt}'\n" + "="*60)
    
    try:
        async for event in runner.run_async(
            user_id="cli_user",
            session_id="cli_session",
            new_message=new_message
        ):
            # Print response parts/text as they arrive
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text, end="", flush=True)
            elif event.output:
                print(event.output, end="", flush=True)
        print("\n" + "="*60 + "\nExecution completed successfully!")
    except Exception as e:
        print(f"\nERROR: Agent execution failed: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Skill Registry CLI Utility")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Registry commands")

    # Global options for all commands
    for sub in [subparsers]:
        # Add a parent parser to share arguments nicely
        pass

    # Search command
    parser_search = subparsers.add_parser("search", help="Perform semantic search on skills")
    parser_search.add_argument("query", help="Semantic query string (e.g. 'firebase')")
    parser_search.add_argument("--top_k", type=int, default=5, help="Number of results to return")
    parser_search.add_argument("--project", help="GCP Project ID")
    parser_search.add_argument("--location", help="GCP Location (default: us-central1)")

    # List command
    parser_list = subparsers.add_parser("list", help="List all registered skills")
    parser_list.add_argument("--project", help="GCP Project ID")
    parser_list.add_argument("--location", help="GCP Location (default: us-central1)")

    # Pull command
    parser_pull = subparsers.add_parser("pull", help="Download and extract a skill")
    parser_pull.add_argument("skill_name", help="Registered skill ID/name to retrieve")
    parser_pull.add_argument("--dest", help="Destination folder (defaults to current folder/<skill_name>)")
    parser_pull.add_argument("--project", help="GCP Project ID")
    parser_pull.add_argument("--location", help="GCP Location (default: us-central1)")

    # Push command
    parser_push = subparsers.add_parser("push", help="Publish a local skill package")
    parser_push.add_argument("local_path", help="Local directory containing the skill package (must have SKILL.md)")
    parser_push.add_argument("--display_name", help="Override skill display name")
    parser_push.add_argument("--description", help="Override skill description")
    parser_push.add_argument("--skill_id", help="Override skill ID/name in registry")
    parser_push.add_argument("--project", help="GCP Project ID")
    parser_push.add_argument("--location", help="GCP Location (default: us-central1)")

    # Run command
    parser_run = subparsers.add_parser("run", help="Run an ADK Agent turn with Skill Registry integration")
    parser_run.add_argument("prompt", help="Natural language query/instruction for the agent")
    parser_run.add_argument("--model", default="gemini-2.5-flash", help="Gemini model name (default: gemini-2.5-flash)")
    parser_run.add_argument("--project", help="GCP Project ID")
    parser_run.add_argument("--location", help="GCP Location (default: us-central1)")

    args = parser.parse_args()

    if args.command == "search":
        handle_search(args)
    elif args.command == "list":
        handle_list(args)
    elif args.command == "pull":
        handle_pull(args)
    elif args.command == "push":
        handle_push(args)
    elif args.command == "run":
        handle_run(args)

if __name__ == "__main__":
    main()

