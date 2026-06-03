# Vertex AI Skill Registry Integration

A professional command-line wrapper and AGY subagent integration for the new **Google Cloud Skill Registry** (Gemini Enterprise Agent Platform) using the `google-cloud-aiplatform` Vertex AI SDK.

This repository provides an automated workflow to package, register, discover, and retrieve agent-based modular skills locally and on Google Cloud.

## Features

- **Semantic Search (`search`)**: Vector-based semantic query search to find relevant agent skills.
- **Skill Listing (`list`)**: Query and list all custom registered skills.
- **Skill Pulling (`pull`)**: Retrieve any registered skill, automatically decode the `zipped_filesystem` base64 payload, and extract the package structure locally.
- **Skill Publishing (`push`)**: Parse a local directory (discovering YAML frontmatter metadata from `SKILL.md`), zip the package, and upload/register it in Google Cloud.
- **Automatic mTLS Handling**: Integrated environment-level overrides to bypass PKCS#12 DECODER issues in Google's internal development networks (gLinux).

---

## Getting Started

### 1. Prerequisites
- Python 3.10+
- Access to a Google Cloud project with the Vertex AI (Agent Platform) API enabled.
- Active Google Cloud credentials (`gcert` or standard ADC).

### 2. Local Setup
Clone this repository and create a Python virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. CLI Usage

Run the CLI wrapper `skill_registry_cli.py` inside your environment:

```bash
# List all registered skills
python3 skill_registry_cli.py list --project <your-project-id>

# Run a semantic search query
python3 skill_registry_cli.py search "firebase" --project <your-project-id>

# Download and pull a skill to your workspace
python3 skill_registry_cli.py pull "sample-math-skill" --project <your-project-id>

# Publish a new local skill from folder
python3 skill_registry_cli.py push "./sample-math-skill" --project <your-project-id>
```

---

## Subagent Integration
If you are developing inside an Antigravity (AGY) SDK workspace, you can define and invoke a specialized subagent to manage your skills interactively in conversation.

### Subagent Prompt Guide
```markdown
- "List the current registered skills in my registry."
- "Search the registry for 'database' skills."
- "Pull down 'firestore-skill' to my skills folder."
- "Publish my local skill at './custom-skill' to Google Cloud."
```
