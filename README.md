# Google Cloud Skill Registry Integration for AGY

An integration and CLI tool for the **Google Cloud Skill Registry** (Vertex AI Agent Platform). This repository acts as a native **Antigravity (AGY)** plugin containing the `skill_registry_agent` subagent to manage modular skills.

## Quick Start

### 1. Installation
```bash
git clone https://github.com/estherwasatester/agy-skill-registry.git
cd agy-skill-registry
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Authentication
```bash
gcloud auth login
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT="your-google-cloud-project-id"
```

### 3. CLI Usage
```bash
# List all registered skills
python3 skill_registry_cli.py list

# Search for skills semantically
python3 skill_registry_cli.py search "firestore"

# Pull a skill to local directory
python3 skill_registry_cli.py pull "sample-skill"

# Push a local skill (with a SKILL.md) to Google Cloud
python3 skill_registry_cli.py push "./my-skill"

# Execute a natural language query with the ADK Agent (uses official google-adk framework)
python3 skill_registry_cli.py run "Search skills for any firebase tools and tell me what you find"
```

## ADK Agent Integration

The `run` subcommand initializes the official `google-adk` framework:
- Instantiates a `GCPSkillRegistry` to connect to Vertex AI.
- Mounts a `SkillToolset` connected to the registry, giving the agent built-in semantic lookup and dynamic skill loading capabilities (`search_skills`, `load_skill`).
- Uses `google.adk.Agent` with `Runner` to drive the conversational flow.

This repository is also pre-configured as a native AGY plugin via `plugin.json` and `skill_registry_agent_config.json`. When added to an AGY workspace, the `skill_registry_agent` becomes available to your primary agent.

For more details on utilizing and sharing the subagent, see [AGENTS.md](file:///home/estherlloyd/agy/skills/AGENTS.md).

