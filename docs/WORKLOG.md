# Worklog

## 2026-02-07

### Scope
- Completed migration hardening to GPT-only backend.
- Removed residual defects and aligned runtime dependencies.
- Added model configurability and upgraded default target model.

### Changes
- `main.py`
  - Removed unused Firebase credentials import.
  - Removed duplicate exception handler in `/classify/` endpoint.
- `requirements.txt`
  - Added `firebase-admin` (required by auth token verification).
- `gpt_service.py`
  - Added `OPENAI_VISION_MODEL` env-driven model selection.
  - Default model set to `gpt-5.1`.
  - Updated face classification call to return strict JSON (`classification`, `confidence`).
  - Removed logprobs-based confidence extraction path and normalized confidence parsing.

### Commands + Results
- `python3 -m py_compile main.py gpt_service.py` -> passed.
- `python3 - <<'PY' import fastapi, openai, firebase_admin; print('backend imports ok') PY` -> passed.

### OpenAI Model Research Notes
- Official OpenAI model docs indicate `gpt-5.1` as the latest flagship recommendation for coding/agentic tasks.
- OpenAI image/vision guide lists GPT-5 family models as image-input capable.
- Model selection remains configurable through `OPENAI_VISION_MODEL` for cost/perf tradeoffs (`gpt-5.1`, `gpt-5`, `gpt-5-mini`).

### Sources
- https://platform.openai.com/docs/models/gpt-5.1
- https://platform.openai.com/docs/guides/images-vision
- https://platform.openai.com/docs/models
