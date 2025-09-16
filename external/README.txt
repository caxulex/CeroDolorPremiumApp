Coral MCP Setup (scaffold)
==========================

This directory holds local clones of Coral MCP components.

Defaults
--------
By default, this script will clone the following public repositories:
- Server: https://github.com/modelcontextprotocol/servers.git (reference servers)
- Studio: https://github.com/modelcontextprotocol/inspector.git (web inspector)
- Agents: https://github.com/lastmile-ai/mcp-agent.git (Python/Node agent examples)

Usage examples:

1) Clone repos (with defaults):

  pwsh -File scripts/setup_coral_repos.ps1

   Or clone specific forks/branches by overriding URLs:

  pwsh -File scripts/setup_coral_repos.ps1 `
    -CoralServerUrl https://github.com/<org>/coral-server.git `
    -CoralStudioUrl https://github.com/<org>/coral-studio.git `
    -AgentsExamplesUrl https://github.com/<org>/coral-agents-examples.git

2) Install dependencies (Node + optional Python):

  pwsh -File scripts/setup_coral_repos.ps1 -Install -NodePm npm -Python "C:\\Path\\to\\python.exe"

4) Clone Coral-Protocol tutorial branches:

  pwsh -File scripts/setup_coral_repos.ps1 -UseCoralProtocol -Branch stabletutorial

3) Start services and agents (provide your start commands):

  pwsh -File scripts/run_coral_services.ps1 `
    -ServerDir .\\external\\coral-server -ServerStartCmd "npm run start" `
    -StudioDir .\\external\\coral-studio -StudioStartCmd "npm run dev" `
    -AgentsDir .\\external\\coral-agents-examples -AgentsStartCmd @("python agent_aip.py","python agent_asd.py","python agent_aiper.py")

Notes:
- Commands above are examples. Use the actual commands provided by each repo.
- These scripts are non-invasive and do not affect tests/CI.

Toolchain Versions
------------------
Timestamp: 2025-09-16T08:06:36.6705299-05:00

pwsh: PowerShell 7.5.3
