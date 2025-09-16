import os


def _suggest_with_mistral(patient_id: str) -> str | None:
    suggestion: str | None = None
    use_adapters = os.getenv("USE_ADAPTERS", "false").lower() == "true"
    if use_adapters:
        try:
            from integrations.mistral import MistralClient, MistralConfig  # type: ignore[import-not-found]  # noqa: I001
            client = MistralClient(MistralConfig(api_key=os.getenv("MISTRAL_API_KEY")))  # type: ignore[misc]
            msg = (
                "Eres un coach de empatía para dolor crónico. Sugiere una intervención breve, segura y práctica "
                f"para el paciente {patient_id}. Responde en 1 frase."
            )
            resp = client.chat([{"role": "user", "content": msg}])
            choice = (resp.get("choices", [{}]) or [{}])[0]
            message = choice.get("message", {}) if isinstance(choice, dict) else {}
            content = message.get("content") if isinstance(message, dict) else None
            if isinstance(content, str):
                suggestion = content.strip()
        except Exception:  # noqa: BLE001
            suggestion = None

    if suggestion is None:
        use_mistral = os.getenv("USE_MISTRAL")
        api_key = os.getenv("MISTRAL_API_KEY")
        if use_mistral and api_key:
            try:
                from mistralai import Mistral  # type: ignore[import-not-found]
                client = Mistral(api_key=api_key)
                prompt = (
                    "Eres un coach de empatía para dolor crónico. Sugiere una intervención breve, "
                    f"segura y práctica para el paciente {patient_id}. Responde en 1 frase."
                )
                resp = client.chat.complete(
                    model="mistral-small-latest",
                    messages=[{"role": "user", "content": prompt}],
                )
                content2 = (
                    getattr(resp.choices[0].message, "content", None)
                    if getattr(resp, "choices", None)
                    else None
                )
                if content2 and isinstance(content2, str):
                    suggestion = content2.strip()
            except Exception:  # noqa: BLE001
                suggestion = None

    return suggestion


def generate_intervention(patient_id: str) -> str:
    suggestion = _suggest_with_mistral(patient_id)
    if suggestion:
        return suggestion
    _ = patient_id
    return "Try a 5-minute guided breathing exercise."
