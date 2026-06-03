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

def handle_list(args):
    """Lists all skills in the registry."""
    client = get_client(args.project, args.location)
    print("Listing skills in registry...")
    try:
        # client.skills.list() lists all skills
        skills = client.skills.list()
        skills_list = list(skills)
        print(f"\nFound {len(skills_list)} skill(s) in registry:\n")
        for i, s in enumerate(skills_list):
            print(f"[{i+1}] ID / Name: {s.name}")
            print(f"    Display Name: {s.display_name}")
            print(f"    Description: {s.description}")
            print(f"    State: {s.state}")
            print("-" * 50)
    except Exception as e:
        print(f"ERROR: Failed to list skills: {e}", file=sys.stderr)
        sys.exit(1)

def handle_pull(args):
    """Retrieves and extracts a skill's filesystem."""
    client = get_client(args.project, args.location)
    skill_name = args.skill_name

    # Determine destination directory
    dest_dir = args.dest
    if not dest_dir:
        dest_dir = os.path.join(os.getcwd(), skill_name)

    print(f"Pulling skill '{skill_name}' from registry...")
    try:
        skill = client.skills.get(name=skill_name)
    except Exception as e:
        print(f"ERROR: Failed to retrieve skill from registry: {e}", file=sys.stderr)
        sys.exit(1)

    if not skill.zipped_filesystem:
        print(f"ERROR: Skill '{skill_name}' has no zipped filesystem payload.", file=sys.stderr)
        sys.exit(1)

    print(f"Extracting zipped filesystem to: {dest_dir}...")
    try:
        os.makedirs(dest_dir, exist_ok=True)
        zip_data = base64.b64decode(skill.zipped_filesystem)
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_ref:
            zip_ref.extractall(dest_dir)
        print(f"SUCCESS: Skill '{skill_name}' successfully extracted to '{dest_dir}'.")
    except Exception as e:
        print(f"ERROR: Extraction failed: {e}", file=sys.stderr)
        sys.exit(1)

def handle_push(args):
    """Packages and publishes a local skill to the Skill Registry."""
    client = get_client(args.project, args.location)
    local_path = os.path.abspath(args.local_path)

    if not os.path.exists(local_path):
        print(f"ERROR: Local path '{local_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # Resolve display_name and description from SKILL.md if present
    md_name, md_desc = None, None
    for filename in ["SKILL.md", "skill.md"]:
        filepath = os.path.join(local_path, filename)
        if os.path.exists(filepath):
            md_name, md_desc = parse_skill_md(filepath)
            break

    display_name = args.display_name or md_name or os.path.basename(local_path) or "Untitled Skill"
    description = args.description or md_desc or "Skill published from local workspace."

    skill_id = args.skill_id
    if not skill_id:
        base_id = clean_id(md_name or os.path.basename(local_path) or "skill")
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        skill_id = f"{base_id}-{ts}"
    else:
        skill_id = clean_id(skill_id)

    print(f"Pushing local skill package from '{local_path}'...")
    print(f"  ID / Name:    {skill_id}")
    print(f"  Display Name: {display_name}")
    print(f"  Description:  {description}")

    try:
        skill = client.skills.create(
            display_name=display_name,
            description=description,
            config={
                "skill_id": skill_id,
                "local_path": local_path
            }
        )
        print("SUCCESS: Skill published successfully!")
        print(f"  Name:  {skill.name}")
        print(f"  State: {skill.state}")
    except Exception as e:
        print(f"ERROR: Publication failed: {e}", file=sys.stderr)
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

    args = parser.parse_args()

    if args.command == "search":
        handle_search(args)
    elif args.command == "list":
        handle_list(args)
    elif args.command == "pull":
        handle_pull(args)
    elif args.command == "push":
        handle_push(args)

if __name__ == "__main__":
    main()
