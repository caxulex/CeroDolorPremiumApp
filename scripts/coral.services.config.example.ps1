# Example configuration for run_coral_services.ps1
# Copy to coral.services.config.ps1 and edit paths/commands per your repos.

$ServerDir = "C:\\Users\\caxul\\CeroDolorPreminumApp\\external\\coral-server"
$ServerStartCmd = "npm run start"

$StudioDir = "C:\\Users\\caxul\\CeroDolorPreminumApp\\external\\coral-studio"
$StudioStartCmd = "npm run dev"

$AgentsDir = "C:\\Users\\caxul\\CeroDolorPreminumApp\\external\\coral-agents-examples"
$AgentsStartCmd = @(
  "python agent_aip.py",
  "python agent_asd.py",
  "python agent_aiper.py"
)

# To run with this config:
# pwsh -NoProfile -ExecutionPolicy Bypass -Command \
#   ".\\scripts\\run_coral_services.ps1 -ServerDir '$ServerDir' -ServerStartCmd '$ServerStartCmd' -StudioDir '$StudioDir' -StudioStartCmd '$StudioStartCmd' -AgentsDir '$AgentsDir' -AgentsStartCmd $AgentsStartCmd"
