#!/usr/bin/env bash
set -euo pipefail

echo "API:"   && curl -fsS http://localhost:8008/debug.ping && echo
echo "Files:" && curl -fsS http://localhost:8081/ | head -n1
echo "Web  :" && curl -fsS http://localhost:8080/ | head -n1

echo "OK."
