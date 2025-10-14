# Architecture Overview

FBA Bench is a multi-service application designed to simulate an e-commerce environment. Here’s a breakdown of the key components:

- **Frontend**: A React-based web application that provides the user interface for interacting with the simulation. (Located in the `frontend/` directory).

- **Backend (API)**: A Python FastAPI application that serves as the main entry point for the frontend, handling API requests and orchestrating the simulation. (Main file: `api_server.py`).

- **Database (PostgreSQL)**: The primary data store for the application, used for persisting simulation state, user data, and experiment results.

- **Cache (Redis)**: Used for caching frequently accessed data and for message passing between services.

- **ML Experiment Tracking (ClearML)**: An optional service for tracking and managing machine learning experiments.

- **Monitoring (Prometheus & Grafana)**: For collecting and visualizing metrics from the various services.