#!/bin/bash
# Foolproof shutdown script for fba-bench

echo "Stopping FBA Bench..."
# Call the project's own shutdown script
./scripts/stop-local.sh