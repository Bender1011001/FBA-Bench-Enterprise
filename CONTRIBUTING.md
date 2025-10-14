# Contributing to FBA-Bench Enterprise

We appreciate your interest in contributing to FBA-Bench Enterprise! To ensure a smooth and consistent development process, please follow these guidelines.

## Prerequisites

Before you begin, ensure you have the following installed on your system:
*   **Python**: Version 3.12 or higher.
*   **Node.js**: Version 20.x or higher.
*   **npm**: Or Yarn, for managing Node.js packages.
*   **Git**: For version control.
*   **Docker**: For containerized development and testing.

## Setup

1.  **Fork the Repository**: Fork the main FBA-Bench Enterprise repository to your GitHub account.
2.  **Clone Your Fork**: Clone your forked repository locally:
    ```bash
    git clone https://github.com/YOUR_USERNAME/FBA-Bench-Enterprise.git
    cd FBA-Bench-Enterprise
    ```
    Replace `YOUR_USERNAME` with your GitHub username.
3.  **Set Upstream Remote**: Add the original repository as an upstream remote to keep your fork updated:
    ```bash
    git remote add upstream https://github.com/original_owner/FBA-Bench-Enterprise.git
    ```
    Replace `original_owner` with the actual owner of the repository.
4.  **Create a Virtual Environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.\.venv\Scripts\activate`
    ```
5.  **Install Backend Dependencies**:
    ```bash
    pip install -r requirements.txt
    pip install -e . # Install editable mode
    ```
6.  **Install Frontend Dependencies**: Navigate to each frontend directory (`frontend/`, `web/`) and install dependencies:
    ```bash
    cd frontend
    npm ci # or yarn install
    cd ..

    cd web
    npm ci # or yarn install
    cd ..
    ```
7.  **Set Up Environment Variables**: Copy the example environment file and populate it with your settings:
    ```bash
    cp .env.example .env
    # Edit .env with your specific configurations, especially SECRET_KEY and database URL.
    ```

## Running Tests

### Backend Tests
Run all backend tests using pytest:
```bash
pytest
```
For more detailed output or specific files/markers, refer to pytest documentation.

### Frontend Tests
Run tests for each frontend application:
```bash
cd frontend
npm run test --if-present -- --run
cd ..

cd web
npm run test --if-present -- --run
cd ..
```
Ensure you have run `npm ci` in each frontend directory first.

## Coding Standards

We strive for a clean, maintainable, and readable codebase. Please adhere to the following standards:

*   **Linting**: Use `ruff` for linting. It automatically formats code according to `black` and `isort` standards.
    ```bash
    ruff check .
    ruff format .
    ```
*   **Type Checking**: Use `mypy` for static type checking.
    ```bash
    mypy .
    ```
Code that does not pass linting or type checking may be rejected.

## Commit Message Style

Please follow the Conventional Commits specification for your commit messages. This helps in automatically generating changelogs and understanding the nature of changes.
Example: `feat: Add user authentication endpoint`

## Pull Request (PR) Checklist

Before submitting a Pull Request, please ensure:
*   [ ] Your code adheres to all coding standards (linting, type checking).
*   [ ] All tests (backend and frontend) are passing.
*   [ ] Your changes address the intended issue or feature.
*   [ ] Your commit messages are clear and follow conventional commits.
*   [ ] You have updated or added relevant documentation.
*   [ ] You have reviewed your own changes for clarity and correctness.