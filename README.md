# EdgeOS API

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Environment Variables](#environment-variables)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Documentation](#documentation)
- [Local Development](#local-development)
- [Stopping the Application](#stopping-the-application)
- [Troubleshooting](#troubleshooting)
- [License](#license)

This repository contains the code for the **EdgeOS API**, a FastAPI-based application that interacts with a PostgreSQL database. It also includes a **NocoDB** service for database management through an intuitive UI. The setup is containerized using Docker Compose for easy deployment.


## Features
- **FastAPI** for building RESTful APIs.
- **PostgreSQL** for relational database storage.
- **NocoDB** as a no-code interface for managing the database.
- Docker Compose for simplified multi-container deployment.


## Related Projects

- **EdgeOS Frontend**: [https://github.com/p2p-lanes/EdgeOS](https://github.com/p2p-lanes/EdgeOS)


## Requirements
- [Docker](https://www.docker.com/get-started) installed on your machine.
- [Docker Compose](https://docs.docker.com/compose/) installed.


## Environment Variables
Create a `.env` file in the root directory with the following content:

```env
ENVIRONMENT=develop # Or testing, production

DB_USERNAME=myuser
DB_PASSWORD=secret
DB_HOST=postgres # Should match the service name in docker-compose.yml
DB_PORT=5432
DB_NAME=edgeos_db
NOCO_DB_NAME=noco_db

BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

NOCODB_URL=...
NOCODB_TOKEN=...
NOCODB_WEBHOOK_SECRET=...

SECRET_KEY=your_super_secret_and_long_random_key # Generate a strong random key
COUPON_API_KEY=your_coupon_api_key # Generate a strong random key
ATTENDEES_API_KEY=your_attendees_api_key # Generate a strong random key
GROUPS_API_KEY=your_groups_api_key # Generate a strong random key

POSTMARK_API_TOKEN=your_postmark_api_token
EMAIL_FROM_ADDRESS=...
EMAIL_FROM_NAME=...
EMAIL_REPLY_TO=...
SIMPLEFI_API_URL=https://api.simplefi.tech
```


## Running the Application
Follow these steps to run the application:

1. Clone the repository.

2. Ensure your `.env` file is correctly configured as shown above.

3. Build and run the application with Docker Compose:

    ```bash
    docker compose up -d
    ```

    This will:

    - Start the **PostgreSQL** service.
    - Start the **NocoDB** service.
    - Build and start the **API** service.

4. Access the services:

    - **API**: http://localhost:8000
    - **NocoDB**: http://localhost:8080

### API Documentation

Once the API is running, you can access the automatically generated documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to explore and interact with the available API endpoints.


## Documentation

- [Full Documentation Index](docs/index.md)
- [Architecture Overview](docs/architecture.md): System architecture, components, and data flow diagrams.
- [Email Management System](docs/email_management.md): Comprehensive documentation of the email system, including templates, scheduling, and automated processes.
- [NocoDB Setup Guide](docs/nocodb_setup.md): Guide for connecting NocoDB to the PostgreSQL database.
- [NocoDB Webhooks](docs/nocodb_webhooks.md): Documentation on NocoDB webhook integration and event handling.
- [Status Calculation](docs/status_calculation.md): Explanation of the status calculation algorithms and business logic.


## Local Development

If you want to run the API locally for development purposes without Docker:

1.  **Ensure Python 3.x is installed.**
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set up environment variables:** You can either:
    *   Set the variables directly in your shell (less convenient).
    *   Use a `.env` file and a library like `python-dotenv` (if not already used in `main.py`) to load them. Ensure your local `.env` points to a locally running PostgreSQL instance if you're not using the Docker one.
5.  **Run the FastAPI development server:**
    ```bash
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```
    (Assuming your FastAPI instance is named `app` in `main.py`)

This will start the API on `http://localhost:8000` and automatically reload when you save code changes.


## Populating the Database with Demo Data

To quickly populate the database with demo data (including a sample PopUpCity, citizens, and applications), you can use the provided script:

**Using Docker Compose:**

```bash
docker compose exec api python scripts/populate_demo_data.py
```

**Or, if running locally:**

```bash
python scripts/populate_demo_data.py
```

The script will prompt for confirmation before making changes. It loads data from the `scripts/popup_city.json`, `scripts/email_templates.csv`, and `scripts/citizen_applications.csv` files. Make sure these files are present and properly configured before running the script.


## Stopping the Application
To stop and remove all running containers, run:

```bash
docker compose down
```


## Connecting to the Database with psql

You can connect to the PostgreSQL database using the `psql` command-line tool. Make sure you have `psql` installed on your machine.

Use the following command (replace values as needed, or use those from your `.env` file):

```bash
psql -h localhost -p 5432 -U myuser -d edgeos_db
```

- `-h`: Hostname (use `localhost` if running locally, or `postgres` if inside the Docker network)
- `-p`: Port (default is `5432`)
- `-U`: Username (from your `.env`, e.g., `myuser`)
- `-d`: Database name (from your `.env`, e.g., `edgeos_db`)

You will be prompted for the password (from your `.env`, e.g., `secret`).

If you are running the command from inside the API or NocoDB container, use `postgres` as the host:

```bash
docker compose exec postgres psql -U myuser -d edgeos_db
```


## Notes
- The API service includes a health check endpoint at `/`.
- NocoDB allows you to manage the database through a web interface.


## Troubleshooting
If the API or NocoDB does not start:

1. Check the logs:
    ```bash
    docker compose logs <service-name>
    ```
    Replace `<service-name>` with api, postgres, or nocodb.

2. Ensure your `.env` file is correctly configured and all environment variables are set.

Make sure no other services are running on ports `8000`, `8080`, or `5432`.


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
