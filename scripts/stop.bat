@echo off
REM Foolproof shutdown script for fba-bench

echo Stopping FBA Bench...
docker-compose -f docker-compose-simple.yml down