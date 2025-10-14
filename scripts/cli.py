#!/usr/bin/env python
"""
FBA-Bench CLI
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import click
import os
import requests

@click.group()
def cli():
    """FBA-Bench CLI

    fba run test - Launch test setup
    fba run full - Launch full setup
    fba stop test - Stop test setup
    """
    pass

@cli.group()
def run():
    """Run commands"""
    pass

@run.command()
def test():
    """Launch the test setup (lightweight for single-user testing)."""
    mode = 'test'
    env_path = Path(".env")
    if not env_path.exists():
        click.echo(f"🔧 Configuring for {mode} mode...")
        try:
            subprocess.run(["bash", "./scripts/oneclick-configure.sh", "--" + mode], check=True)
            click.echo("✅ Configuration complete.")
        except subprocess.CalledProcessError as e:
            click.secho(f"❌ Configuration failed: {e}", fg="red")
            sys.exit(1)

    click.echo(f"🚀 Launching {mode} mode (local API + frontend; Redis via Docker)...")
    try:
        # Fast path: run API and Frontend locally, Redis in Docker
        env = os.environ.copy()
        env["PYTHON_BIN"] = sys.executable
        subprocess.run(["bash", "./scripts/start-local.sh"], check=True, env=env)
        click.echo("✅ Launch command executed.")
    except subprocess.CalledProcessError as e:
        click.secho(f"❌ Failed to start local services: {e}", fg="red")
        sys.exit(1)

    click.echo("⏳ Waiting 10 seconds for services to start...")
    time.sleep(10)

    health_url = "http://localhost:8000/api/v1/health"
    browser_url = "http://localhost:5173"

    click.echo(f"🔍 Checking health at {health_url}...")
    max_retries = 12
    healthy = False
    for attempt in range(max_retries):
        try:
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                healthy = True
                break
        except requests.RequestException:
            pass
        if attempt < max_retries - 1:
            click.echo(f"  ⏳ Not ready yet (attempt {attempt + 1}/{max_retries}), waiting 5s...")
            time.sleep(5)

    if not healthy:
        click.secho("❌ Health check failed after 60 seconds. Services may not be ready.", fg="red")
        click.echo("You can still try accessing the browser URL manually.")
    else:
        click.echo("✅ Services are healthy!")

    click.echo(f"🌐 Opening browser at {browser_url}...")
    webbrowser.open(browser_url)

    click.echo(
        f"""
✅ Started frontend (localhost:5173), backend/API (Uvicorn on 8000), Redis (Docker).

- Access at: {browser_url}

- Health endpoint: {health_url}

- To stop: fba stop test
        """
    )

@run.command()
def full():
    """Launch the full setup (for researchers with ClearML and observability)."""
    mode = 'full'
    env_path = Path(".env")
    if not env_path.exists():
        click.echo(f"🔧 Configuring for {mode} mode...")
        try:
            subprocess.run(["bash", "./scripts/oneclick-configure.sh", "--" + mode], check=True)
            click.echo("✅ Configuration complete.")
        except subprocess.CalledProcessError as e:
            click.secho(f"❌ Configuration failed: {e}", fg="red")
            sys.exit(1)

    click.echo(f"🚀 Launching {mode} mode...")
    try:
        subprocess.run(["bash", "./scripts/oneclick-launch.sh", "--" + mode], check=True)
        click.echo("✅ Launch complete.")
    except subprocess.CalledProcessError as e:
        click.secho(f"❌ Failed to start Docker services: {e}; check logs with docker compose logs", fg="red")
        sys.exit(1)

    click.echo("⏳ Waiting 10 seconds for services to start...")
    time.sleep(10)

    health_url = "http://localhost:80/health"
    browser_url = "http://localhost:80"

    click.echo(f"🔍 Checking health at {health_url}...")
    max_retries = 12
    healthy = False
    for attempt in range(max_retries):
        try:
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                healthy = True
                break
        except requests.RequestException:
            pass
        if attempt < max_retries - 1:
            click.echo(f"  ⏳ Not ready yet (attempt {attempt + 1}/{max_retries}), waiting 5s...")
            time.sleep(5)

    if not healthy:
        click.secho("❌ Health check failed after 60 seconds. Services may not be ready.", fg="red")
        click.echo("You can still try accessing the browser URL manually.")
    else:
        click.echo("✅ Services are healthy!")

    click.echo(f"🌐 Opening browser at {browser_url}...")
    webbrowser.open(browser_url)

    click.echo(
        f"""
✅ Started full setup: frontend/API (Nginx on 80), Docker services (Postgres, Redis, ClearML, observability).

- Access at: {browser_url}

- Health endpoint: {health_url}

- To stop: fba stop full
        """
    )

@cli.command()
@click.argument('mode', type=click.Choice(['test', 'full']))
def stop(mode):
    """Stop the test or full setup."""
    try:
        if mode == "test":
            subprocess.run(["bash", "./scripts/stop-local.sh"], check=True)
        else:
            subprocess.run(["bash", "./scripts/oneclick-stop.sh", "--" + mode], check=True)
        click.echo(f"✅ Stopped the {mode} setup, including frontend, backend, API, and related services.")
    except subprocess.CalledProcessError as e:
        click.secho(f"❌ Failed to stop {mode} setup: {e}; check docker ps", fg="red")
        sys.exit(1)
    except Exception as e:
        click.secho(f"Unexpected error stopping {mode} setup: {e}", fg="red")
        sys.exit(1)

if __name__ == "__main__":
    cli()
