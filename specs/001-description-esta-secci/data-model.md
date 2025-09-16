# Data Model

## Entities

### Patient
- **id**: string (unique identifier, e.g., UUID)
- **name**: string (patient's name)
- **pain_history**: list of PainRecord objects

**Validation Rules**:
- id: required, unique
- name: required, non-empty string

**Relationships**:
- One-to-many with PainRecord

### PainRecord
- **date**: datetime (ISO format)
- **pain_level**: int (1-10 scale)
- **description**: string (qualitative pain description)
- **mood**: string (current mood state)
- **sleep**: string (sleep quality description)

**Validation Rules**:
- date: required, valid datetime
- pain_level: required, integer 1-10
- description: optional, string
- mood: optional, string
- sleep: optional, string

**Relationships**:
- Many-to-one with Patient

### Clinician
- **id**: string (unique identifier)
- **name**: string (clinician's name)
- **patients**: list of Patient ids

**Validation Rules**:
- id: required, unique
- name: required, non-empty string
- patients: list of valid Patient ids

**Relationships**:
- Many-to-many with Patient

### Agent
- **type**: enum (AIP, ASD, AIPer, AIC)
- **state**: dict (current context and memory)

**Validation Rules**:
- type: required, one of [AIP, ASD, AIPer, AIC]
- state: dict, optional

**State Transitions**:
- AIP: idle → listening → processing → responding → idle
- ASD: idle → analyzing → insights_generated → idle
- AIPer: idle → evaluating_patterns → recommending → idle
- AIC: idle → aggregating → summary_ready → idle