# Vertex AI Skill Registry Integration for Google Antigravity (AGY)

A premium, professional integration and command-line toolset for the **Google Cloud Skill Registry** (Vertex AI Agent Platform). This repository allows you to package, search, list, pull, and publish modular agent skills both locally and in Google Cloud. It comes pre-packaged as a native **Antigravity (AGY) SDK Plugin**, containing the specialized `skill_registry_agent` subagent.

---

## 🚀 Key Features

*   **Integrated AGY Subagent**: Fully defined subagent schema in `plugin.json` and `skill_registry_agent_config.json` that automates search/listing/publishing tasks dynamically inside user conversations.
*   **Semantic Search (`search`)**: Vector-based semantic query search to find relevant agent skills in the cloud.
*   **Skill Listing (`list`)**: Real-time listing of registered custom skills.
*   **Skill Pulling (`pull`)**: Downloads registered skills from the registry, auto-decodes the `zipped_filesystem` base64 payload, and extracts files locally.
*   **Skill Publishing (`push`)**: Scans local directories for metadata (using YAML frontmatter in `SKILL.md`), compresses the files, and pushes the package to Google Cloud.
*   **Automated mTLS Handling**: Embedded environment-level overrides to bypass PKCS#12 DECODER/mTLS client-certificate issues on internal corporate networks (like Google's gLinux).

---

## 📁 Repository Structure

```
agy-skill-registry/
├── Agents.md                      # Detailed guide to subagent usage & sharing
├── README.md                      # Main overview and setup guide
├── plugin.json                    # AGY Native Plugin manifest
├── skill_registry_agent_config.json # Programmatic AGY subagent configuration
├── skill_registry_cli.py          # Core Python SDK CLI interface
└── requirements.txt               # Manifest of required dependencies
```

---

## 🛠️ Getting Started

### 1. Prerequisites
*   Python 3.10+
*   Google Cloud SDK (`gcloud` CLI)
*   Access to a Google Cloud project with the Vertex AI Agent Platform API enabled.
*   Active Application Default Credentials (ADC) or internal `gcert` LOAS credentials.

### 2. Local Installation
Clone the repository and prepare your virtual environment:

```bash
# Clone the repository
git clone https://github.com/estherwasatester/agy-skill-registry.git
cd agy-skill-registry

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install requirements
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Authentication (ADC Setup)
To authenticate your local workstation with Google Cloud and allow the script/subagent to make API calls, run:

```bash
# Log in to Google Cloud with your user account
gcloud auth login

# Generate local Application Default Credentials (ADC)
gcloud auth application-default login
```

This ensures that the underlying `google-cloud-aiplatform` Vertex SDK can securely and automatically authorize all search, pull, and push API calls.

### 4. Setting Your GCP Project ID
Before running the CLI or starting AGY, export your target Google Cloud Project ID:

```bash
export ANTIGRAVITY_PROJECT_ID="your-gcp-project-id"
```


---

## 💻 CLI Usage

You can use the core Python tool directly from your terminal:

```bash
# List all registered skills
python3 skill_registry_cli.py list

# Run a semantic search query for relevant skills
python3 skill_registry_cli.py search "firestore integration"

# Retrieve and extract a skill locally (to the current workspace)
python3 skill_registry_cli.py pull "sample-math-skill"

# Publish a new local skill directory to Google Cloud
python3 skill_registry_cli.py push "./my-local-skill"
```

---

## 🤖 Using & Sharing the AGY Subagent

This repository is built natively as a shareable AGY plugin. 

### How other AGY users can import this plugin:
1.  **Clone the Repo**: Simply clone this repository to their development machine.
2.  **Plugin Auto-Discovery**: AGY reads the `plugin.json` configuration and automatically adds the `skill_registry_agent` to the local agent's roster.
3.  **Prompt & Delegate**: From that point on, other developers can talk directly to their agent to query or push skills.

For a deep dive into the subagent's architecture, programmatic activation, and how to share it across multiple environments, refer to [Agents.md](file:///home/estherlloyd/agy/skills/Agents.md).

---

## 🛡️ License and Contributions
Developed for developers utilizing the Google Antigravity SDK. Pull requests, enhancements, and custom skill designs are welcome!
