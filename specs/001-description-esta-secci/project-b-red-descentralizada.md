# Proyecto B: Red de Cuidado Descentralizada

Un concepto multi-agente y multi-interesado para habilitar colaboración segura y ética sobre datos de pacientes, aprovechando Coral (MCP) y Web3 (Crossmint/Solana) con enfoque offline-first para CI estable.

## Agentes
- AP (Agente del Paciente): nodo soberano; gestiona permisos y billetera (Crossmint).
- AC (Agente del Clínico): solicita acceso mediante contratos; no accede directo a datos.
- AI (Agente Investigador): difunde consultas anonimizadas; ejecuta micropagos (Solana).

## Contratos (JSON Schema)
- `research_query.json`: especifica criterios, campos y compensación.
- `data_offer.json`: oferta de datos del paciente con hash anonimizado.
- `anonymized_data_bundle.json`: paquete de datos anonimizados que cumple la oferta.
- `micropayment_receipt.json`: recibo de micropago (destino, monto, firma).
- `audit_log_entry.json`: entrada de auditoría de acciones clave.

## Flujo offline-first
1. AI prepara `ResearchQuery` y la difunde.
2. AP evalúa criterios localmente. Si coincide y preferencias lo permiten, crea wallet (offline), calcula hash, minta NFT de datos (offline) y prepara `DataOffer`.
3. AP empaqueta `AnonymizedDataBundle` y otorga consentimiento con micropago simulado; genera `MicropaymentReceipt`.
4. Todo queda registrado en `audit/*.jsonl`.

## Servicios y CLIs
- Servicio: `backend/src/services/research_network_service.py` con `evaluate_query_against_patient()` y `fulfill_query_offline()`.
- CLIs:
  - AP: `python backend/src/agents/patient_agent.py --patient-id P --profile profile.json --query query.json --data data.json`
  - AC: `python backend/src/agents/clinician_agent.py --request request.json`
  - AI: `python backend/src/agents/investigator_agent.py --query query.json`

## Notas
- Adapters habilitados con `USE_ADAPTERS=true`; `USE_NETWORK=false` por defecto.
- Integra Crossmint/Solana reales cuando se habilite `USE_NETWORK=true` y claves/vínculos válidos.
- Mantén y extiende tests con validaciones de esquema y casos negativos.
