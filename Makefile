RUN_SCRIPT := ./run.sh
DOTENV_LOCAL ?= ./config/.env.local
DOTENV_PROD ?= ./config/.env.local

.PHONY: dev dev-local

dev:
	$(RUN_SCRIPT) --dotenv $(DOTENV_PROD)

## Run the MCP server with environment variables loaded from DOTENV_LOCAL
## (e.g. GENIUSAI_SERVER_URL to point at a non-default geniusai-server instance).
## Usage: make dev-local [DOTENV_LOCAL=<env_file>]
dev-local:
	$(RUN_SCRIPT) --dotenv $(DOTENV_LOCAL)
