#!/usr/bin/env python3
"""
Example demonstrating how to build an AI agent utilizing the official
Agent Development Kit (ADK) and its built-in Google Cloud Skill Registry integration.

Prerequisites:
1. Make sure you have google-adk installed in your environment.
2. Authenticate:
   gcloud auth login
   gcloud auth application-default login
3. Export your Google Cloud Project ID:
   export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
"""

import os
import sys
import asyncio

# 1. Bypass mTLS cert decoder issues on internal development workstations (e.g. gLinux)
os.environ["CLOUDSDK_CONTEXT_AWARE_USE_CLIENT_CERTIFICATE"] = "false"
os.environ["GOOGLE_API_USE_CLIENT_CERTIFICATE"] = "false"

try:
    import google.adk
except ImportError:
    print("ERROR: 'google-adk' package not found in this environment.", file=sys.stderr)
    print("Run: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

from google.adk import Agent
from google.adk.integrations.skill_registry.gcp_skill_registry import GCPSkillRegistry
from google.adk.tools.skill_toolset import SkillToolset

async def main():
    # 2. Extract Project ID and Location
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

    if not project_id:
        print("ERROR: GOOGLE_CLOUD_PROJECT environment variable must be set.", file=sys.stderr)
        print("Please run: export GOOGLE_CLOUD_PROJECT=\"your-project-id\"", file=sys.stderr)
        sys.exit(1)

    print(f"Initializing GCPSkillRegistry for project '{project_id}' in '{location}'...")

    # 3. Instantiate the GCP Skill Registry
    registry = GCPSkillRegistry(
        project_id=project_id,
        location=location
    )

    # 4. Construct the SkillToolset connected to your cloud registry
    # This automatically equips the agent with 'search_skills' and 'load_skill' tools
    skill_toolset = SkillToolset(
        skills=[],  # You can also seed this with pre-loaded local skills
        registry=registry
    )

    print("Assembling ADK Agent with the Skill Registry Toolset...")

    # 5. Define your ADK Agent using the mounted Toolset
    agent = Agent(
        model="gemini-2.5-flash",  # Set your preferred Gemini model
        name="skill_assistant",
        description="A specialized assistant that discovers and runs remote capabilities dynamically.",
        instruction=(
            "You are a helpful assistant. If you do not have direct instructions or tools to "
            "perform a requested action (e.g., query database, check formatting, audit code), "
            "use search_skills and load_skill to search and retrieve capabilities from your remote registry."
        ),
        tools=[skill_toolset]
    )

    print("\n--- ADK Agent Assembled Successfully! ---")
    print(f"Agent Name: {agent.name}")
    print(f"Agent Model: {agent.model}")
    print("Mounted Tools:")
    
    # In ADK 2.0+, get_tools is an asynchronous coroutine
    tools = await skill_toolset.get_tools()
    for tool in tools:
        print(f" - {tool.name}: {tool.description}")

    print("\nTo start a conversational turn, execute the agent using the ADK Runner or workflow system.")
    print("Example Python Execution:")
    print("  from google.adk import Runner")
    print("  runner = Runner()")
    print("  response = await runner.run(agent, input=\"Perform firestore operation...\")")
    print("------------------------------------------")

if __name__ == "__main__":
    asyncio.run(main())
