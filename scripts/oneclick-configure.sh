#!/usr/bin/env bash
set -euo pipefail

# Determine repo root (parent of scripts directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"

# Function to set an env var in .env (remove existing, append new)
set_env_var() {
  local key="$1"
  local value="$2"
  sed -i "/^${key}=/d" "$ENV_FILE"
  echo "${key}=${value}" >> "$ENV_FILE"
}

# Argument parsing
MODE="test"
while [[ $# -gt 0 ]]; do
  case $1 in
    --full)
      MODE="full"
      shift
      ;;
    --test)
      MODE="test"
      shift
      ;;
    --help)
      echo "Usage: $0 [--full | --test]"
      echo "  --test  Configure for test setup (default, SQLite, basic auth bypass)"
      echo "  --full  Configure for full stack (Postgres, ClearML, production auth)"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage."
      exit 1
      ;;
  esac
done

echo "==> One-time configuration: creating/updating $ENV_FILE for $MODE mode"

# Copy .env.example if .env doesn't exist
if [ ! -f "$ENV_FILE" ]; then
  cp "$REPO_ROOT/.env.example" "$ENV_FILE"
  echo "==> Copied .env.example to $ENV_FILE"
fi

if [ "$MODE" = "test" ]; then
  echo "Configuring for test setup..."

  # Prompt for LLM API keys (optional)
  read -r -p "OpenAI API Key (optional): " OPENAI_API_KEY
  OPENAI_API_KEY="${OPENAI_API_KEY:-}"
  read -r -p "Anthropic API Key (optional): " ANTHROPIC_API_KEY
  ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}"
  read -r -p "Google API Key (optional): " GOOGLE_API_KEY
  GOOGLE_API_KEY="${GOOGLE_API_KEY:-}"
  read -r -p "Cohere API Key (optional): " COHERE_API_KEY
  COHERE_API_KEY="${COHERE_API_KEY:-}"
  read -r -p "OpenRouter API Key (optional): " OPENROUTER_API_KEY
  OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}"

  # Set core vars for test
  REDIS_PASSWORD="ChangeMe_Redis_#u9YxQn7pLz!"
  set_env_var "REDIS_PASSWORD" "$REDIS_PASSWORD"
  set_env_var "DATABASE_URL" "sqlite+aiosqlite:///./fba_bench.db"
  set_env_var "FBA_BENCH_REDIS_URL" "redis://:${REDIS_PASSWORD}@redis:6379/0"
  set_env_var "AUTH_ENABLED" "false"
  set_env_var "AUTH_TEST_BYPASS" "true"
  set_env_var "FBA_CORS_ALLOW_ORIGINS" "http://localhost:8080,http://localhost:5173"
  set_env_var "GF_SECURITY_ADMIN_USER" "admin"
  set_env_var "GF_SECURITY_ADMIN_PASSWORD" "admin"

  # Set API keys if provided
  if [ -n "$OPENAI_API_KEY" ]; then
    set_env_var "OPENAI_API_KEY" "$OPENAI_API_KEY"
  fi
  if [ -n "$ANTHROPIC_API_KEY" ]; then
    set_env_var "ANTHROPIC_API_KEY" "$ANTHROPIC_API_KEY"
  fi
  if [ -n "$GOOGLE_API_KEY" ]; then
    set_env_var "GOOGLE_API_KEY" "$GOOGLE_API_KEY"
  fi
  if [ -n "$COHERE_API_KEY" ]; then
    set_env_var "COHERE_API_KEY" "$COHERE_API_KEY"
  fi
  if [ -n "$OPENROUTER_API_KEY" ]; then
    set_env_var "OPENROUTER_API_KEY" "$OPENROUTER_API_KEY"
  fi

elif [ "$MODE" = "full" ]; then
  echo "Configuring for full stack..."

  # Prompt for LLM API keys (optional)
  read -r -p "OpenAI API Key (optional): " OPENAI_API_KEY
  OPENAI_API_KEY="${OPENAI_API_KEY:-}"
  read -r -p "Anthropic API Key (optional): " ANTHROPIC_API_KEY
  ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}"
  read -r -p "Google API Key (optional): " GOOGLE_API_KEY
  GOOGLE_API_KEY="${GOOGLE_API_KEY:-}"
  read -r -p "Cohere API Key (optional): " COHERE_API_KEY
  COHERE_API_KEY="${COHERE_API_KEY:-}"
  read -r -p "OpenRouter API Key (optional): " OPENROUTER_API_KEY
  OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}"

  # Prompt for Postgres
  POSTGRES_USER="fba"
  POSTGRES_DB="fba_bench"
  read -r -p "Postgres Password (default: ChangeMe_Postgres_#X9m!7Pa): " POSTGRES_PASSWORD
  POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-ChangeMe_Postgres_#X9m!7Pa}"
  set_env_var "POSTGRES_USER" "$POSTGRES_USER"
  set_env_var "POSTGRES_PASSWORD" "$POSTGRES_PASSWORD"
  set_env_var "POSTGRES_DB" "$POSTGRES_DB"
  set_env_var "DATABASE_URL" "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}"

  # Prompt for Redis
  read -r -p "Redis Password (default: ChangeMe_Redis_#u9YxQn7pLz!): " REDIS_PASSWORD
  REDIS_PASSWORD="${REDIS_PASSWORD:-ChangeMe_Redis_#u9YxQn7pLz!}"
  set_env_var "REDIS_PASSWORD" "$REDIS_PASSWORD"
  set_env_var "FBA_BENCH_REDIS_URL" "redis://:${REDIS_PASSWORD}@redis:6379/0"

  # Prompt for Mongo (ClearML)
  MONGO_INITDB_ROOT_USERNAME="clearml"
  read -r -p "Mongo Root Password (default: ChangeMe_Mongo_Root_#Wb3f2tQ2sQd!): " MONGO_INITDB_ROOT_PASSWORD
  MONGO_INITDB_ROOT_PASSWORD="${MONGO_INITDB_ROOT_PASSWORD:-ChangeMe_Mongo_Root_#Wb3f2tQ2sQd!}"
  set_env_var "MONGO_INITDB_ROOT_USERNAME" "$MONGO_INITDB_ROOT_USERNAME"
  set_env_var "MONGO_INITDB_ROOT_PASSWORD" "$MONGO_INITDB_ROOT_PASSWORD"

  # Prompt for ClearML
  read -r -p "ClearML API Access Key (optional): " CLEARML_API_ACCESS_KEY
  CLEARML_API_ACCESS_KEY="${CLEARML_API_ACCESS_KEY:-}"
  read -r -p "ClearML API Secret Key (optional): " CLEARML_API_SECRET_KEY
  CLEARML_API_SECRET_KEY="${CLEARML_API_SECRET_KEY:-}"

  # Prompt for Grafana
  read -r -p "Grafana Admin User (default: admin): " GRAFANA_ADMIN_USER
  GRAFANA_ADMIN_USER="${GRAFANA_ADMIN_USER:-admin}"
  read -r -p "Grafana Admin Password (default: admin, use strong password): " GRAFANA_ADMIN_PASSWORD
  GRAFANA_ADMIN_PASSWORD="${GRAFANA_ADMIN_PASSWORD:-admin}"
  set_env_var "GF_SECURITY_ADMIN_USER" "$GRAFANA_ADMIN_USER"
  set_env_var "GF_SECURITY_ADMIN_PASSWORD" "$GRAFANA_ADMIN_PASSWORD"

  # Set production vars
  set_env_var "ENVIRONMENT" "production"
  set_env_var "AUTH_ENABLED" "true"
  set_env_var "AUTH_TEST_BYPASS" "false"
  set_env_var "FBA_CORS_ALLOW_ORIGINS" "https://app.fba.example.com,https://console.fba.example.com"
  set_env_var "API_RATE_LIMIT" "100/minute"

  # Set API keys if provided
  if [ -n "$OPENAI_API_KEY" ]; then
    set_env_var "OPENAI_API_KEY" "$OPENAI_API_KEY"
  fi
  if [ -n "$ANTHROPIC_API_KEY" ]; then
    set_env_var "ANTHROPIC_API_KEY" "$ANTHROPIC_API_KEY"
  fi
  if [ -n "$GOOGLE_API_KEY" ]; then
    set_env_var "GOOGLE_API_KEY" "$GOOGLE_API_KEY"
  fi
  if [ -n "$COHERE_API_KEY" ]; then
    set_env_var "COHERE_API_KEY" "$COHERE_API_KEY"
  fi
  if [ -n "$OPENROUTER_API_KEY" ]; then
    set_env_var "OPENROUTER_API_KEY" "$OPENROUTER_API_KEY"
  fi
  if [ -n "$CLEARML_API_ACCESS_KEY" ]; then
    set_env_var "CLEARML_API_ACCESS_KEY" "$CLEARML_API_ACCESS_KEY"
  fi
  if [ -n "$CLEARML_API_SECRET_KEY" ]; then
    set_env_var "CLEARML_API_SECRET_KEY" "$CLEARML_API_SECRET_KEY"
  fi

else
  echo "Invalid mode: $MODE"
  exit 1
fi

echo "==> Updated $ENV_FILE for $MODE setup. Review and customize as needed (e.g., AUTH_JWT_PUBLIC_KEY)."
