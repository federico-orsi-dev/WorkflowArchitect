# 🛠️ WorkflowArchitect: Strategic Roadmap

WorkflowArchitect is an agentic workflow orchestrator. Future development focuses on deepening the integration between AI planning and Git execution.

## Phase 1: Tooling & Execution
- [ ] **Local Execution Sandbox**: Run the agentic plans in a Dockerized sandbox to safely test code changes before proposing them.
- [ ] **Git Interaction Layer**: Automated `git commit`, `git push`, and **GitHub PR creation** directly from the UI.

## Phase 2: Collaboration
- [ ] **Shared Workflows**: Allow teams to share "JSON Guard" templates and workflow definitions via a central repository.
- [ ] **Real-time Collaboration**: Multi-user editing of the same agentic plan using WebSockets/CRDTs.

## Phase 3: Agentic Intelligence
- [ ] **Self-Correction (Self-Healing)**: Allow the agent to read terminal error logs and automatically propose a second, corrected version of the plan.
- [ ] **Plugin System**: Build a community-driven plugin architecture to add new "Tools" to the agent (e.g., Jira integration, AWS deployment).

## Phase 4: Infrastructure
- [ ] **Cloud Persistence**: Move from `localStorage` to a hosted database (PostgreSQL) for cross-device synchronization and persistent state.
