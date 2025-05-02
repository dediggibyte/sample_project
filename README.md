# My Databricks Project

This project demonstrates packaging a simple Python library (`mylibrary`) and deploying it along with a Databricks notebook job using Databricks Asset Bundles (DABs) and GitHub Actions.

## Structure

* `/mylibrary`: Source code for the Python library.
* `/notebooks`: Databricks notebooks used in jobs.
* `pyproject.toml`: Defines the Python package and build requirements.
* `databricks.yml`: Configures the Databricks Asset Bundle, including artifacts and jobs.
* `.github/workflows/deploy.yml`: GitHub Actions workflow for automated deployment.

## Deployment

Changes pushed to the `main` branch will automatically trigger the GitHub Actions workflow, which builds the Python wheel and deploys the bundle (including the job definition) to the configured Databricks workspace (dev target).

## Setup

1.  Configure GitHub Secrets:
    * `DATABRICKS_HOST`: Your workspace URL (e.g., `https://<your-workspace-instance>.databricks.net`).
    * `DATABRICKS_TOKEN`: A Databricks Personal Access Token (PAT) or a token for a Service Principal.