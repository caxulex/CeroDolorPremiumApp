# SECURITY OVERVIEW

Status: Initial hardening pass (local-first prototype evolving toward production readiness)
Last Updated: 2025-09-17

## 1. Data Classification
| Category | Examples | Sensitivity | Notes |
|----------|----------|-------------|-------|
| Pseudonymous Patient Data | Pain levels, mood/sleep entries, transcripts | HIGH | Health-adjacent behavioral data |
| Derived Analytics | Trends, correlations, summaries | HIGH | Can reveal health patterns |
| Audio Artifacts | Transcripts (text) | HIGH | Transcribed voice may contain identifiers |
| Intervention Suggestions | Coaching text | MEDIUM | Low intrinsic sensitivity |
| Exported Session Files | Encrypted JSON (optional) | HIGH | Must protect at rest |
| API Keys | MISTRAL_API_KEY, ELEVENLABS_API_KEY | HIGH | Credential secrets |

## 2. Current Architecture & Trust Boundaries
- UI: Streamlit single-process app (no user auth layer yet).
- Persistence: Local JSON files under `sessions/` directory (one file per patient id).
- Encryption: Optional export encryption using password-derived Fernet (PBKDF2 + SHA256, random salt).
- Memory: In-process cache of session objects.
- Network (optional): External LLM / TTS APIs only when env flags present (`USE_MISTRAL`, `USE_ADAPTERS`).

Boundary Notes:
- No multi-tenant isolation: patient IDs are user-controlled strings; risk of ID guessing.
- No TLS termination logic inside app (relies on deployment environment if exposed over network).

## 3. Threat Model (High-Level)
| Threat | Vector | Impact | Current Mitigation | Gap |
|--------|--------|--------|--------------------|-----|
| Local File Disclosure | Unauthorized host access | Full session exfiltration | None (plaintext JSON) | Introduce at-rest encryption or OS ACL guidance |
| Patient ID Enumeration | Guessable IDs (`sim_patient_1`) | Cross-patient data exposure | None | Need auth + ID randomization |
| API Key Leakage | Env variable exposure, logging | Abuse of paid APIs | Keys not logged intentionally | Add runtime key scanning / secret lint |
| Model Prompt Injection | Malicious transcript content | Corrupted suggestions | Limited heuristics, no HTML injection | Add prompt sanitization policy |
| DoS (Resource Exhaustion) | Flood cycles | Performance degradation | Simple code, no rate limiting | Add per-IP or per-session throttling |
| Persistence Corruption | Partial write / crash | Data loss / parse failure | Atomic write via temp file | Add journaling / backup rotation |
| MITM (API Calls) | Intercept outbound LLM/TTS | Data leakage | Depends on HTTPS libraries | Add certificate pinning option (doc) |
| Weak Export Password | User chooses '1234' | Easy offline crack | PBKDF2 (default rounds) | Enforce min length + iteration tuning |
| Log Sensitive Data | Logging of raw transcripts | Privacy violation | Current logs omit transcript bodies | Add log scrubber / classification |
| Supply Chain Attack | Malicious dependency | Code execution | Minimal deps & pinned dev reqs | Add `pip hash` / SBOM / dependabot |

## 4. Immediate Recommendations (Short-Term)
1. Enforce password policy for encrypted exports (length >= 10, reject weak patterns).
2. Add patient ID normalization + random suffix on creation to reduce enumeration predictability.
3. Introduce a lightweight auth token (even single shared secret) if exposed beyond localhost.
4. Add SECRET SCAN: pre-commit hook (detect API key patterns) + CI job.
5. Mask environment secrets in any debug output.
6. Add optional in-memory redaction of transcript before logging (hash or length only).
7. Provide script to rotate API keys safely (doc in README).

## 5. Medium-Term Roadmap
| Item | Description | Priority |
|------|-------------|----------|
| Auth Layer | Per-user session + JWT or signed cookie | High |
| Role Separation | Distinguish patient vs clinician views | High |
| At-Rest Encryption | Encrypt session JSON transparently (derived key per patient) | High |
| Integrity Protection | HMAC over event records to detect tampering | Medium |
| Rate Limiting | Sliding window per patient / IP | Medium |
| SBOM Generation | CycloneDX output in CI | Medium |
| Secrets Manager Integration | Load API keys from OS keyring or cloud secret store | Medium |
| Structured Logging Classifier | Tag events with PII / PHI flags for routing | Medium |
| Backup & Retention Policy | Automatic rolling snapshots + retention purge | Low |
| Audit Trail | Immutable append-only log (WORM) for compliance | Low |

## 6. Export Encryption Details
- Algorithm: Fernet (AES128 + HMAC) via `cryptography` library (if installed) or fallback? (Future: ensure dependency pinned).
- Key Derivation: PBKDF2HMAC(SHA256) with random 16-byte salt, iterations (future: raise to >= 390k for 2025 baseline, currently unspecified—document & parameterize).
- Format: `{ "enc": true, "salt": <b64>, "token": <fernet> }`.
- Risks: Weak passwords remain brute-forceable; advise length >= 14 and mix of classes.

## 7. Logging & Observability
- Current: Lightweight custom wrapper (`logging_utils`) supporting JSON mode.
- To Add: Field-level redaction list (`SENSITIVE_FIELDS = ["transcript_text", "raw_audio"]`).
- Consider: Correlation id per request/cycle.

## 8. Privacy Considerations
- Avoid storing raw audio (only transcript). If audio stored later, evaluate encoding + encryption.
- Provide user data deletion path: simple script to purge a patient session file.
- Add consent event auditing (persist acceptance timestamps).

## 9. Secure Development Practices
- Pin production dependencies (create `requirements-lock.txt`).
- Enable Dependabot or equivalent.
- Add static analysis (Bandit) optional stage in CI.
- Add `ruff` rules extension for security (S prefix) once noise evaluated.

## 10. Deployment Guidance (Initial)
- Run behind reverse proxy (nginx / caddy) enforcing HTTPS.
- Set environment variables via secrets manager or OS config, not `.env` committed.
- Restrict filesystem permissions: `sessions/` readable only by service user.
- Use container with non-root user (future Dockerfile).

## 11. Incident Response (Draft)
1. Detect anomaly (error spikes / unauthorized access suspicion).
2. Freeze exports; capture hash of session files.
3. Rotate API keys immediately.
4. Patch / deploy fixed version.
5. Retrospective: root cause + mitigation recorded.

## 12. Open Questions
- Will multi-user SaaS be in-scope? (Changes auth & tenancy model.)
- Regulatory alignment (GDPR / HIPAA) needed? Trigger data retention & DSR processes.
- Voice data retention policy? (Currently not persisted as audio.)

## 13. Quick Checklist (Current Gaps)
- [ ] Auth boundary
- [ ] Randomized patient identifiers
- [ ] Password strength enforcement
- [ ] Secret scanning in CI
- [ ] Session encryption at rest
- [ ] Rate limiting
- [ ] Dependency lock file
- [ ] Bandit security scan
- [ ] PBKDF2 iteration parameter exposed

---
For security issues, DO NOT open a public issue. Contact the maintainers privately.
