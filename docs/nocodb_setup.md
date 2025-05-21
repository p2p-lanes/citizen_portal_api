# Configuring NocoDB to Connect to the Database

Follow these steps to connect NocoDB to your PostgreSQL database:

### 1. Initial Access

**Open NocoDB** in your browser by navigating to http://localhost:8080.

### 2. Account Setup

**Sign Up** with an email and password. This email will act as the Super Admin account.

### 3. Database Connection

Go to **"Integrations"** -> **PostgreSQL**, and fill in the connection details:

| Field | Value | Description |
|-------|-------|-------------|
| **Connection Name** | `EdgeOS DB` | A label to identify the connection in NocoDB |
| **Host Address** | `postgres` | Matches the `DB_HOST` value in your `.env` file |
| **Port Number** | `5432` | Matches the `DB_PORT` value in your `.env` file |
| **Username** | `myuser` | Replace with the `DB_USERNAME` value from your `.env` file |
| **Password** | `secret` | Matches the `DB_PASSWORD` value in your `.env` file |
| **Database Name** | `edgeos_db` | Matches the `DB_NAME` value in your `.env` file |
| **Schema Name** | `public` | Keep as `public` unless using a different schema |

### 4. Connection Testing

Click on **"Test Connection"** to verify the provided details. If the test is successful, click **"Create Connection"** to save it.

### 5. Base Creation

Next, go to **"Create Base"** and assign a name for the Base.

### 6. External Data Connection

Navigate to **"Connect External Data"**, and select the PostgreSQL connection you created earlier.

### 7. Finalize Setup

Click on **"Test Connection"** to confirm the setup, then click **"Add Source"** to complete the process.

Your database is now connected to NocoDB, and you can start managing your data through the NocoDB interface. 

---

**← [Back to Documentation Index](./index.md)**
