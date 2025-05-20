# Email Management System Documentation

## Overview

The Citizen Portal API's email system provides a comprehensive solution for sending and tracking emails through the Postmark service. The system supports templated emails, scheduled delivery, and detailed logging of all email operations.

## Components

### 1. Configuration (`app/core/config.py`)

Email-related settings are managed through environment variables:

| Environment Variable | Description |
|---------------------|-------------|
| `POSTMARK_API_TOKEN` | Authentication token for the Postmark API |
| `EMAIL_FROM_ADDRESS` | Default sender email address |
| `EMAIL_FROM_NAME` | Default sender name |
| `EMAIL_REPLY_TO` | Optional reply-to address for emails |

### 2. Email Sending (`app/core/mail.py`)

<details>
<summary>The <code>send_mail</code> function handles communication with the Postmark API</summary>

- Sends templated emails using Postmark's template system
- Supports file attachments
- Provides detailed logging
- Returns standardized response formats
- Handles test environment scenarios by returning mock success responses

```python
send_mail(
    receiver_mail: str,
    *,
    template: str,
    params: dict,
    attachments: list[EmailAttachment] = None,
)
```
</details>

### 3. Email Logging System (`app/api/email_logs/`)

### Models (`models.py`)

The `EmailLog` database model stores:
- Email recipient information
- Template and event details
- Email status (success, failed, scheduled, cancelled)
- Error messages for failed deliveries
- Relationship to citizens and popup cities
- Timestamps for auditing

A database event listener automatically associates emails with existing citizens based on email address.

### Schemas (`schemas.py`)

- `EmailStatus`: Enum defining possible email delivery statuses
- `EmailEvent`: Standard email event types (application-received, authentication, etc.)
- `EmailAttachment`: Format for file attachments
- `EmailLogFilter`: Schema for filtering email logs
- `EmailLog`: Complete email log entry representation

### Operations (`crud.py`)

<details>
<summary>The <code>CRUDEmailLog</code> class provides email management functionality</summary>

1. **Email Sending**:
   - `send_mail`: Core method for sending emails with comprehensive logging
   - `send_login_mail`: Specialized method for authentication emails

2. **Authentication URL Generation**:
   - `generate_authenticate_url`: Creates authenticated portal access links
   - `_generate_authenticate_url`: Internal helper for URL generation

3. **Scheduled Email Management**:
   - `send_scheduled_mails`: Processes and sends emails scheduled for delivery
   - `cancel_scheduled_emails`: Cancels pending scheduled emails

4. **Query Functions**:
   - `get_by_email`: Retrieves all email logs for a specific recipient
</details>

### 4. PopUp City Email Templates (`app/api/popup_city/`)

Each popup city can have its own custom email templates for different event types. This allows for city-specific branding and messaging.

### Models (`models.py`)

<details>
<summary>The <code>EmailTemplate</code> model manages popup-specific email templates</summary>

- Associates templates with specific popup cities
- Maps templates to event types
- Supports frequency settings for reminder emails
- Tracks template creation and updates

```python
class EmailTemplate(Base):
    __tablename__ = 'popup_email_templates'

    id = Column(Integer, primary_key=True)
    popup_city_id = Column(Integer, ForeignKey('popups.id'), nullable=False)
    event = Column(String, nullable=False)
    template = Column(String, nullable=False)
    frequency = Column(String)
    created_at = Column(DateTime, default=current_time)
    updated_at = Column(DateTime, default=current_time, onupdate=current_time)
```
</details>

<details>
<summary>The <code>PopUpCity</code> model includes a method to retrieve appropriate templates</summary>

```python
def get_email_template(self, event: EmailEvent) -> str:
    for t in self.templates:
        if t.event == event:
            return t.template
    raise ValueError(
        f'No template found for event: {event} (popup_city: {self.id} {self.name})'
    )
```
</details>

### Operations (`crud.py`)

The `CRUDPopUpCity` class provides methods for template management:

1. **Template Retrieval**:
   - `get_email_template`: Fetches a specific template for a popup city and event

2. **Reminder Management**:
   - `get_reminder_templates`: Retrieves templates for scheduled reminders  

### 5. Automated Email Processes

The system includes background processes to handle scheduled and reminder emails.

### Scheduled Email Processor (`app/processes/send_scheduled_emails.py`)

A background process that:
- Queries for emails marked with `SCHEDULED` status that are due for delivery
- Processes these emails by calling `email_log.send_scheduled_mails()`
- Runs periodically to check for new emails ready for delivery

### Reminder Email Processor (`app/processes/send_reminder_emails.py`)

<details>
<summary>Manages frequency-based reminder emails</summary>

1. **Configuration**:
   - Reminder templates are defined with comma-separated frequency values (e.g., "1h,1d,1w")
   - Supports frequency formats: minutes (m), hours (h), days (d), weeks (w)

2. **Reminder Types**:
   - `PURCHASE_REMINDER`: Sent after application acceptance if no payment is found
   - `APPLICATION_IN_DRAFT`: Sent to users with draft applications

3. **Duplicate Prevention**:
   - Tracks previously sent frequencies for each application
   - Prevents sending the same reminder twice

4. **Processing Logic**:
   - Determines appropriate starting date based on reminder type
   - Calculates if reminders are due based on configured frequencies
   - Sends reminders with application-specific context

Example frequency string: `"1h,1d,3d,1w"` (send after 1 hour, 1 day, 3 days, and 1 week)
</details>

## Email Workflow

1. Application code calls `email_log.send_mail()` with appropriate parameters
2. If scheduled, the email is stored with SCHEDULED status
3. For immediate delivery, the system:
   - Processes template parameters
   - Calls Postmark API via `core.mail.send_mail()`
   - Records the outcome (success/failure)
4. Scheduled emails are processed by `send_scheduled_mails()` when invoked
5. All email operations are logged to the database

## Template Processing

When sending an email, if a `popup_city` is specified:
1. The system looks up the appropriate template for the event using `popup_city.get_email_template()`
2. Default popup-specific parameters are added to the email context:
   
   | Parameter | Description |
   |-----------|-------------|
   | `popup_name` | The name of the popup city |
   | `web_url` | The popup city's website URL |
   | `email_image` | Custom image for the email |
   | `contact_email` | Contact email for the popup |
   | `blog_url` | Blog URL for the popup |
   | `twitter_url` | Twitter profile for the popup |

3. This allows for completely customized email experiences for each popup city

## Event Types

The system supports several standardized email events:

| Event Type | Description |
|------------|-------------|
| `application-received` | Sent when a new application is received |
| `auth-citizen-portal` | Portal authentication emails |
| `auth-citizen-by-code` | Code-based authentication |
| `payment-confirmed` | Payment confirmation notifications |
| `edit-passes-confirmed` | Pass modification confirmations |
| `check-in` | Check-in confirmations |

Additionally, reminder-specific events include:
- `purchase-reminder`: Sent to users with accepted applications who haven't completed payment
- `application-in-draft`: Sent to users with draft applications

## Error Handling

- Failed email attempts are logged with detailed error messages
- Database errors during logging are caught and logged separately
- Scheduled emails with delivery failures are marked as FAILED with error details 

---

**← [Back to Documentation Index](./index.md)**
