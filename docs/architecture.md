# System Architecture

This document provides an overview of the EdgeOS system architecture, showing how various components interact to deliver functionality.

## System Overview

```
┌──────────────────────────────────────┐       ┌───────────────┐
│                                      │       │               │
│              Frontend                │◄──────►   Client      │
│                                      │       │   Browser     │
└───────────────────┬──────────────────┘       └───────────────┘
                    │
                    ▼
┌──────────────────────────────────────┐
│                                      │
│         EdgeOS FastAPI Backend       │
│                                      │
└───────────────────┬──────────────────┘
                    │
        ┌───────────┴───────────┐──────────────────────┐
        │                       │                      │
        ▼                       ▼                      ▼
┌────────────────┐      ┌───────────────┐     ┌─────────────────┐
│                │      │               │     │                 │
│  PostgreSQL    │◄─────►    NocoDB     │     │    Postmark     │
│  Database      │      │               │     │    Email API    │
│                │      └───────────────┘     │                 │
└────────────────┘                            └────────┬────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │                 │
                                              │    End User     │
                                              │      Email      │
                                              │                 │
                                              └─────────────────┘
```

The EdgeOS architecture consists of the following major components, all containerized using Docker:

| Component | Description |
|-----------|-------------|
| **FastAPI Backend** | The core API service that handles business logic and data operations |
| **PostgreSQL Database** | Persistent storage for all application data |
| **NocoDB** | A no-code interface for database management without requiring SQL knowledge |
| **Postmark** | External email service for all communication with users |

## Component Interactions

### FastAPI and PostgreSQL

<details>
<summary>The FastAPI application connects to PostgreSQL using SQLAlchemy ORM</summary>

Key interactions include:

- Database initialization during startup
- CRUD operations for all data entities (applications, citizens, payments, etc.)
- Transaction management for complex operations
- Schema validation using Pydantic models

Configuration details are stored in environment variables and managed through the `Settings` class in `app/core/config.py`.
</details>

### NocoDB Integration

<details>
<summary>NocoDB provides a user-friendly interface for database operations</summary>

Particularly useful for:

- Data visualization and exploration
- Simple CRUD operations without SQL knowledge
- Webhooks that trigger API functionality

The integration works as follows:
1. NocoDB connects directly to the PostgreSQL database
2. The API retrieves data from PostgreSQL through SQLAlchemy
3. NocoDB webhooks call API endpoints to trigger specific business logic
</details>

### Email System with Postmark

<details>
<summary>The application uses Postmark for all email communications</summary>

1. The `send_mail` function in `app/core/mail.py` handles communication with the Postmark API
2. Email templates are managed through Postmark's template system
3. The application logs all email operations in the database for tracking
4. Scheduled emails and reminders are handled by background processes
</details>

## Data Flow

### User Authentication Flow

1. User requests access via email
2. System generates unique authentication URL using citizen spice
3. Email sent via Postmark
4. User clicks link and gains authenticated access

### Application Processing Flow

1. User submits application data
2. Data stored in PostgreSQL
3. Status updates trigger webhook notifications
4. Email notifications sent at various stages

### Payment Processing Flow

1. Payment information submitted
2. Payment processed and recorded
3. Confirmation emails sent
4. Status updated in database

## Deployment Architecture

The system is containerized using Docker Compose for simplified deployment:

| Container | Purpose |
|-----------|---------|
| **API Container** | Runs the FastAPI application |
| **PostgreSQL Container** | Runs the database with persistent volume |
| **NocoDB Container** | Runs the NocoDB service with persistent volume |

The containers are networked together, with PostgreSQL available only to the API and NocoDB containers for security.

## External Services

### Postmark Email API

<details>
<summary>The system integrates with Postmark for reliable email delivery</summary>

- Template-based emails for consistent formatting
- Delivery tracking and reporting
- Support for attachments
- Authentication emails with secure links
</details>

## Security Considerations

| Area | Approach |
|------|----------|
| Configuration | Environment variables for sensitive configuration |
| Secrets | Secret keys and tokens stored securely |
| Authentication | API authentication using secure tokens |
| Database | Database credentials isolated within the Docker network |

---

**← [Back to Documentation Index](./index.md)**
