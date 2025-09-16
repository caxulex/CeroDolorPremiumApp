# Ángulo Web3: Crossmint y Solana

Este documento describe cómo integrar un flujo ético de datos usando una **Billetera de Datos de Salud** controlada por el paciente, **mercado de datos ético**, y **micropagos** en Solana. Se basa en adaptadores offline-first para mantener a CI estable.

## Ideas clave
- Identidad y propiedad: los datos anonimizados del paciente se representan como un activo digital (NFT/token).
- Consentimiento verificable: el paciente autoriza granularmente el uso de datos.
- Valor compartido: los investigadores pagan micropagos en Solana cuando acceden a los datos.

## Adaptadores (offline-first)
- `CrossmintClient` (`backend/src/integrations/crossmint.py`): crea billeteras, acuña NFTs y transfiere tokens.
- `SolanaClient` (`backend/src/integrations/solana.py`): envía micropagos simulados.
- Todos están controlados por `USE_ADAPTERS` y `USE_NETWORK`.

## Servicios
- `data_wallet_service.py`: orquesta creación de billetera, acuñación del asset de datos y consentimiento + micropago.

## Contratos JSON
- `specs/.../contracts/data_access_request.json`
- `specs/.../contracts/consent_grant.json`

## Variables de entorno
- `USE_ADAPTERS=true`: Activa adaptadores con simulación determinista.
- `USE_NETWORK=true`: Permite llamadas reales (cuando están implementadas) y sólo si hay API keys.
- Crossmint: `CROSSMINT_API_KEY`, `CROSSMINT_BASE_URL`, `CROSSMINT_COLLECTION_ID`
- Solana: `SOLANA_RPC_URL`, `SOLANA_PAYER_SECRET`

## Ejecutar en modo offline (PowerShell)
```pwsh
& .\.venv\Scripts\Activate.ps1
$env:USE_ADAPTERS = 'true'
$env:USE_NETWORK = 'false'
Remove-Item Env:\CROSSMINT_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:\SOLANA_RPC_URL -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m pytest -q -k web3
```

## Evolución a modo real (HTTP)
- Implementar requests HTTP dentro de los adaptadores cuando sea necesario.
- Añadir tests de integración con `USE_NETWORK=true` y claves presentes; omitir por defecto en CI.
- Mantener rutas offline para reproducibilidad y estabilidad.
