# Mapeo de las APIs de los Socios al Dominio del Manejo del Dolor

Este documento prioriza integraciones que maximizan impacto funcional y puntuación del hackathon, alineadas al dominio de CeroDolorApp.

## Principios
- Priorizar impacto en accesibilidad, compromiso, y calidad clínica.
- Integraciones env-guardadas: sin red por defecto, activables con variables de entorno.
- Simulación offline para TDD y CI verde (sin dependencias externas).

## ElevenLabs (IA de Voz) – Prioridad Alta
- Justificación: Voz como pilar de accesibilidad y acompañamiento empático.
- Casos:
  - STT: Registro de síntomas manos libres.
  - TTS: Feedback empático (tono calmado, guía de ejercicios de respiración/relajación).
- Adaptador:
  - `backend/src/integrations/elevenlabs.py` con `ElevenLabsClient`.
  - Env: `ELEVENLABS_API_KEY`, `ELEVENLABS_TTS_VOICE_ID`, `ELEVENLABS_BASE_URL`, `USE_NETWORK`.
- Pruebas: `tests/unit/test_integrations_offline.py` (simulado offline), sin red.

## Mistral AI (LLM) – Prioridad Alta
- Justificación: “Cerebro” cognitivo multi‑idioma con razonamiento avanzado.
- Casos:
  - Comprensión de narrativas del paciente (extracción estructurada).
  - Síntesis de datos clínicos.
  - Recomendaciones personalizadas.
- Adaptador:
  - `backend/src/integrations/mistral.py` con `MistralClient`.
  - Env: `MISTRAL_API_KEY`, `MISTRAL_BASE_URL`, `USE_NETWORK`.
- Pruebas: `tests/unit/test_integrations_offline.py` (simulado offline).

## AI/ML API (Gateway multi‑modelo) – Prioridad Media
- Justificación: Capa de nicho para sentimiento, visión, etc., complementaria al LLM.
- Casos:
  - Sentiment sobre diarios de voz/texto.
  - Postura (visión) para ergonomía básica.
- Adaptador:
  - `backend/src/integrations/aiml_api.py` con `AIMLClient`.
  - Env: `AIML_API_KEY`, `AIML_BASE_URL`, `USE_NETWORK`.
- Pruebas: `tests/unit/test_integrations_offline.py` (simulado offline).

## Activación por Entorno
- Por defecto: `USE_NETWORK=false` → simulación determinista; CI estable.
- Producción/demos reales: setear claves y `USE_NETWORK=true`.

## Enrutamiento en el MAS (futuro inmediato)
- Integrar `ElevenLabsClient` en AIP para STT/TTS.
- Integrar `MistralClient` en ASD/AIPer para análisis y recomendaciones.
- Mantener contratos JSON Schema y validación en cada salto.

## Seguridad y Costos
- Evitar exponer claves en el repositorio.
- Habilitar límites de uso y timeouts.

## Próximos Pasos
- Conectar estos adaptadores al flujo real (flags/DI) bajo variables de entorno.
- Añadir pruebas de integración con stubs locales o servicios de prueba cuando estén disponibles.
