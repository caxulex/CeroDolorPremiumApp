from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    app_name: str = "CeroDolor Orchestrator API"
    environment: str = "dev"
    use_network: bool = False

    # Mistral
    mistral_api_key: str | None = None
    mistral_base_url: str = "https://api.mistral.ai"
    mistral_agent_invoke_path: str = "/v1/agents/{agent_id}/invoke"
    mistral_health_path: str = "/v1/health"

    # Agent IDs
    agent_investigator_id: str | None = None
    agent_clinician_id: str | None = None
    agent_patient_interface_id: str | None = None
    agent_clinician_report_id: str | None = None
    agent_personalized_intervention_id: str | None = None
    agent_data_synthesis_id: str | None = None

    # ElevenLabs
    elevenlabs_api_key: str | None = None
    elevenlabs_base_url: str = "https://api.elevenlabs.io"
    elevenlabs_default_voice: str = "demo_female"

    # Solana
    solana_rpc_url: str | None = None


settings = Settings()
