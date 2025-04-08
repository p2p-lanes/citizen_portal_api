# Configuring NocoDB to Connect to the Database

Follow these steps to connect NocoDB to your PostgreSQL database:

1.  **Open NocoDB** in your browser by navigating to http://localhost:8080.

2.  **Sign Up** with an email and password. This email will act as the Super Admin account.

3.  Go to **"Integrations"** -> **PostgreSQL**, and fill in the connection details:

    *   **Connection Name**: Enter a name for this connection (e.g., `EdgeOS DB`). This is simply a label to identify the connection in NocoDB.
    *   **Host Address**: `postgres` (This matches the `DB_HOST` value in your `.env` file, which corresponds to the service name defined in the Docker Compose file.)
    *   **Port Number**: `5432` (This matches the `DB_PORT` value in your `.env` file.)
    *   **Username**: `myuser` (Replace this with the `DB_USERNAME` value from your `.env` file.)
    *   **Password**: `secret` (This matches the `DB_PASSWORD` value in your `.env` file.)
    *   **Database Name**: `edgeos_db` (This matches the `DB_NAME` value in your `.env` file.)
    *   **Schema Name**: `public` (Keep this as `public` unless you are using a different schema.)

4.  Click on **"Test Connection"** to verify the provided details. If the test is successful, click **"Create Connection"** to save it.

5.  Next, go to **"Create Base"** and assign a name for the Base.

6.  Navigate to **"Connect External Data"**, and select the PostgreSQL connection you created earlier.

7.  Click on **"Test Connection"** to confirm the setup, then click **"Add Source"** to complete the process.

Your database is now connected to NocoDB, and you can start managing your data through the NocoDB interface. 