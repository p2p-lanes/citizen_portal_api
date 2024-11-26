# Citizen Portal API

This repository contains the code for the **Citizen Portal API**, a FastAPI-based application that interacts with a PostgreSQL database. It also includes a **NocoDB** service for database management through an intuitive UI. The setup is containerized using Docker Compose for easy deployment.


## Features
- **FastAPI** for building RESTful APIs.
- **PostgreSQL** for relational database storage.
- **NocoDB** as a no-code interface for managing the database.
- Docker Compose for simplified multi-container deployment.


## Requirements
- [Docker](https://www.docker.com/get-started) installed on your machine.
- [Docker Compose](https://docs.docker.com/compose/) installed.


## Environment Variables
Create a `.env` file in the root directory with the following content:

```env
DB_USERNAME=myuser
DB_PASSWORD=secret
DB_HOST=postgres
DB_PORT=5432
NOCO_DB_NAME=noco_db
DB_NAME=citizen_portal
SECRET_KEY=your_secret_key
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


## Configuring NocoDB to Connect to the Database
Follow these steps to connect NocoDB to your PostgreSQL database:

1. **Open NocoDB** in your browser by navigating to http://localhost:8080.

2. **Sign Up** with an email and password. This email will act as the Super Admin account.

3. Go to **"Integrations"** -> **PostgreSQL**, and fill in the connection details:

    - **Connection Name**: Enter a name for this connection (e.g., `Citizen Portal DB`). This is simply a label to identify the connection in NocoDB.
    - **Host Address**: `postgres` (This matches the `DB_HOST` value in your `.env` file, which corresponds to the service name defined in the Docker Compose file.)
    - **Port Number**: `5432` (This matches the `DB_PORT` value in your `.env` file.)
    - **Username**: `myuser` (Replace this with the `DB_USERNAME` value from your `.env` file.)
    - **Password**: `secret` (This matches the `DB_PASSWORD` value in your `.env` file.)
    - **Database Name**: `citizen_portal` (This matches the `DB_NAME` value in your `.env` file.)
    - **Schema Name**: `public` (Keep this as `public` unless you are using a different schema.)

4. Click on **"Test Connection"** to verify the provided details. If the test is successful, click **"Create Connection"** to save it.

5. Next, go to **"Create Base"** and assign a name for the Base.

6. Navigate to **"Connect External Data"**, and select the PostgreSQL connection you created earlier.

7. Click on **"Test Connection"** to confirm the setup, then click **"Add Source"** to complete the process.

Your database is now connected to NocoDB, and you can start managing your data through the NocoDB interface.


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
