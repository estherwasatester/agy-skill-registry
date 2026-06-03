# Skill Registry Agent: Shared AGY Subagent

This document explains the architecture of the `skill_registry_agent` subagent, how it interfaces with the **Google Cloud Skill Registry** (Vertex AI Agent Platform), and how you can use and share it with other **Antigravity (AGY)** users.

---

## 1. Subagent Overview

The `skill_registry_agent` is a native, pre-configured AGY subagent. When activated or imported, it acts as an intelligent intermediary that automates the lifecycle of modular AI skills.

### Key Capabilities
- **Search & Discovery**: Performs semantic vector searches on Google Cloud to locate existing skills.
- **Lifecycle Management**: Automatically lists, pulls, and pushes skills to the central Cloud Registry.
- **Dynamic Decoding**: Extracts downloaded `.zip` filesystem payloads from the cloud registry into fully formed, local skill folders inside your active workspace.
- **Local Packaging**: Scans local skill folders for YAML frontmatter in `SKILL.md`, compiles them, and registers them.

---

## 2. Shared Configuration Structure

To allow seamless sharing among AGY developers, the subagent is declared and parameterized using two key configuration files in the root of the repository:

### A. The Plugin Manifest (`plugin.json`)
This manifest tells the AGY system that this repository is a native AGY plugin and contains a subagent named `skill_registry_agent`:

```json
{
  "name": "agy-skill-registry",
  "version": "1.0.0",
  "description": "Antigravity plugin to interface with the Google Cloud Skill Registry (Vertex AI SDK) to search, retrieve, and publish modular skills.",
  "author": "estherwasatester",
  "engines": {
    "antigravity": "^1.0.0"
  },
  "agents": [
    {
      "name": "skill_registry_agent",
      "config": "skill_registry_agent_config.json"
    }
  ],
  "skills": []
}
```

### B. The Agent Configuration Schema (`skill_registry_agent_config.json`)
This file defines the subagent's runtime behavior, system prompt, and authorized tools. It uses **fully relative paths** to ensure it runs out-of-the-box on anyone's machine:

```json
{
  "name": "skill_registry_agent",
  "role": "Skill Registry Specialist",
  "description": "Specialized ADK agent that interfaces with the Google Cloud Skill Registry to search, retrieve (pull), and publish (push) modular agent skills.",
  "enable_write_tools": true,
  "enable_mcp_tools": true,
  "enable_subagent_tools": true,
  "system_prompt": "You are the Skill Registry Agent, a highly specialized ADK subagent designed to manage modular skills using the Google Cloud Skill Registry (Vertex AI SDK).\n\n..."
}
```

---

## 3. How to Use the Subagent in Conversation

Once imported, you do not need to call the CLI tools yourself. You can instruct your primary AGY assistant to delegate tasks to the `skill_registry_agent`.

### Prompt Examples
> "Please ask the skill registry agent to search for any skills related to 'authentication'."

> "Using the skill registry agent, download the 'firestore-skill' to my local workspace."

> "Can you check if we have any active security skills registered in our Google Cloud project?"

---

## 4. Sharing with Other AGY Users

Because this plugin is fully modularized and contains no hardcoded local paths, sharing it is incredibly simple.

### Option A: Direct Repository Clone
Other AGY developers can clone this repository directly into their active workspace or plugin directory:

```bash
# Clone the repository
git clone https://github.com/estherwasatester/agy-skill-registry.git
```

Upon cloning, AGY's automatic plugin discovery engine reads `plugin.json` and immediately registers the `skill_registry_agent` as an available subagent type in their workspace environment.

### Option B: Package and Import in AGY Configuration
If developers want to use it across multiple different projects, they can register it as an active global plugin by referencing its path in their main AGY profile or global `antigravity.json` configuration:

```json
"plugins": [
  "/path/to/cloned/agy-skill-registry"
]
```

### Option C: Programmatic Activation
If another AGY subagent or custom script needs to spin up this specialist programmatically, they can declare it dynamically:

```python
from google_antigravity_sdk import AgentManger

# Initialize the manager
manager = AgentManger()

# Invoke the subagent programmatically
response = manager.invoke_subagent(
    type_name="skill_registry_agent",
    role="Skill Registry Specialist",
    prompt="List all skills registered in our Google Cloud Registry."
)
print(response)
```

---

## 5. Security & Credentials
The `skill_registry_agent` inherits the calling user's local credentials. Other developers will need:
1. Standard Google Cloud ADC (`gcloud auth application-default login`) or active internal `gcert` LOAS credentials.
2. Direct access permissions (IAM Reader/Writer roles) on their target Vertex AI Agent Platform Project.
3. Their project ID specified via the local environment variable:
   ```bash
   export ANTIGRAVITY_PROJECT_ID="your-target-project-id"
   ```
