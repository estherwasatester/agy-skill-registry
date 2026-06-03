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
export ANTIGRAVITY_PROJECT_ID="your-gcp-project-id"
```

### 3. CLI Usage
```bash
# List all registered skills
python3 skill_registry_cli.py list

# Search for skills
python3 skill_registry_cli.py search "firestore"

# Pull a skill to local directory
python3 skill_registry_cli.py pull "sample-skill"

# Push a local skill (with a SKILL.md) to Google Cloud
python3 skill_registry_cli.py push "./my-skill"
```

## AGY Subagent Integration

This repository is pre-configured as a native AGY plugin via `plugin.json` and `skill_registry_agent_config.json`. When added to an AGY workspace, the `skill_registry_agent` becomes available to your primary agent.

For more details on utilizing and sharing the subagent, see [AGENTS.md](file:///home/estherlloyd/agy/skills/AGENTS.md).
