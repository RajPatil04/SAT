# System Configuration Reference

## Environment Variables (`backend/.env`)

| Variable Name | Default Value | Description |
|---|---|---|
| `APP_ENV` | `development` | Environment mode (`development`, `production`) |
| `MODEL_TIMEOUT` | `180` | Model execution timeout in seconds |
| `ENABLE_MOCK_FALLBACK_FOR_TESTS` | `true` | When true, unconfigured endpoints utilize clearly-marked MOCK specialist adapters |
| `GEOCHAT_API_URL` | *empty* | Live hosting endpoint for GeoChat-7B |
| `GEOCHAT_API_TYPE` | `gradio` | API protocol (`gradio`, `rest`, `local`) |
| `GEOCHAT_API_ENDPOINT` | `predict` | Target endpoint function / path |
| `CHANGE_MODEL_API_URL` | *empty* | Live hosting endpoint for ChangeStar |
| `CHANGE_MODEL_API_TYPE` | `gradio` | API protocol |
| `CHANGE_MODEL_API_ENDPOINT`| `predict` | Target endpoint function / path |
| `CROMA_API_URL` | *empty* | Live hosting endpoint for CROMA Optical-SAR |
| `CROMA_API_TYPE` | `gradio` | API protocol |
| `CROMA_API_ENDPOINT` | `predict` | Target endpoint function / path |
| `GROUNDING_API_URL` | *empty* | Live hosting endpoint for Grounding specialist |
| `DATABASE_URL` | `sqlite:///./satquery.db` | SQLAlchemy database connection string |
| `EXPERIMENT_LOGGING` | `true` | Persist experiment trials to SQLite |

## Frontend Environment (`frontend/.env`)

| Variable Name | Default Value | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Target FastAPI server address. Zero model URLs permitted. |
