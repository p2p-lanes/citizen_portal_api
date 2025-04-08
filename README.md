# EdgeOS API

This repository contains the code for the **EdgeOS API**, a FastAPI-based application that interacts with a PostgreSQL database. It also includes a **NocoDB** service for database management through an intuitive UI. The setup is containerized using Docker Compose for easy deployment.


## Features
- **FastAPI** for building RESTful APIs.
- **PostgreSQL** for relational database storage.
- **NocoDB** as a no-code interface for managing the database.
- Docker Compose for simplified multi-container deployment.


## Project Purpose

[**TODO:** Add a brief description of what the EdgeOS API does, the problem it solves, or its main goal.]


## Requirements
- [Docker](https://www.docker.com/get-started) installed on your machine.
- [Docker Compose](https://docs.docker.com/compose/) installed.


## Environment Variables
Create a `.env` file in the root directory with the following content:

```env
ENVIRONMENT=development # Or testing, production

DB_USERNAME=myuser
DB_PASSWORD=secret
DB_HOST=postgres # Should match the service name in docker-compose.yml
DB_PORT=5432
NOCO_DB_NAME=noco_db
DB_NAME=edgeos_db

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


## Configuring NocoDB

For detailed steps on connecting NocoDB to the PostgreSQL database, please refer to the [NocoDB Setup Guide](docs/nocodb_setup.md).


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


## Stopping the Application
To stop and remove all running containers, run:

```bash
docker compose down
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

[**TODO:** Add license information here. Consider adding a `LICENSE` file to the repository (e.g., MIT, Apache 2.0).]
