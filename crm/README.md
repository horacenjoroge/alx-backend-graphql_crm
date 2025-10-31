# CRM Application with Celery Task Scheduling

This CRM application uses Celery with Redis as a message broker for asynchronous task processing and scheduled report generation.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation Steps](#installation-steps)
- [Running the Application](#running-the-application)
- [Scheduled Tasks](#scheduled-tasks)
- [Manual Testing](#manual-testing)
- [Verification](#verification)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)

## Prerequisites

- Python 3.8 or higher
- Django 4.0+
- Redis server 5.0+
- Virtual environment (recommended)
- Git (for version control)

## Installation Steps

### Step 1: Install Redis

Redis is required as the message broker for Celery.

#### On Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
sudo systemctl status redis-server
```

#### On macOS (using Homebrew):
```bash
brew install redis
brew services start redis
brew services list
```

#### On Windows:
1. Download Redis from https://github.com/microsoftarchive/redis/releases
2. Or use Windows Subsystem for Linux (WSL2) and follow Ubuntu instructions
3. Or use Docker: `docker run -d -p 6379:6379 redis`

### Step 2: Verify Redis is Running

Test Redis connectivity:
```bash
redis-cli ping
# Expected output: PONG
```

If you get "PONG", Redis is running correctly.

### Step 3: Clone the Repository (if applicable)
```bash
git clone <repository-url>
cd alx-backend-graphql_crm
```

### Step 4: Create and Activate Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate on Linux/macOS
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

### Step 5: Install Python Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

Required packages include:
- Django
- graphene-django
- django-filter
- celery
- django-celery-beat
- redis
- gql[all]
- django-crontab

### Step 6: Configure Django Settings

Ensure `crm/settings.py` contains:
```python
INSTALLED_APPS = [
    # ... other apps
    'crm',
    'graphene_django',
    'django_crontab',
    'django_celery_beat',  # Required for Celery Beat
]

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Celery Beat Schedule
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'generate-crm-report': {
        'task': 'crm.tasks.generate_crm_report',
        'schedule': crontab(day_of_week='mon', hour=6, minute=0),
    },
}
```

### Step 7: Run Database Migrations
```bash
# Run all migrations
python manage.py migrate

# Specifically migrate django_celery_beat tables
python manage.py migrate django_celery_beat
```

### Step 8: Create Superuser (Optional but Recommended)
```bash
python manage.py createsuperuser
```

This allows you to access Django Admin at `http://localhost:8000/admin/`

### Step 9: Verify Installation
```bash
# Check if Django is set up correctly
python manage.py check

# Test Celery configuration
celery -A crm inspect ping
```

## Running the Application

The application requires **three separate terminal windows/processes** running simultaneously:

### Terminal 1: Django Development Server
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Start Django server
python manage.py runserver

# Server will be available at: http://localhost:8000
# GraphQL endpoint: http://localhost:8000/graphql
```

### Terminal 2: Celery Worker
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Start Celery worker
celery -A crm worker -l info

# On Windows, you may need to use:
celery -A crm worker -l info --pool=solo
```

### Terminal 3: Celery Beat Scheduler
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Start Celery Beat
celery -A crm beat -l info

# Alternative with scheduler database
celery -A crm beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

## Scheduled Tasks

### CRM Weekly Report

- **Task Name:** `generate_crm_report`
- **Module:** `crm.tasks.generate_crm_report`
- **Schedule:** Every Monday at 6:00 AM UTC
- **Functionality:** Generates a comprehensive summary report including:
  - Total number of customers
  - Total number of orders
  - Total revenue (sum of all order amounts)
- **Output:** Logs to `/tmp/crm_report_log.txt`
- **Format:** `YYYY-MM-DD HH:MM:SS - Report: X customers, Y orders, $Z.ZZ revenue.`

### Other Scheduled Tasks (via django-crontab)

- **Heartbeat Logger:** Runs every 5 minutes
- **Low Stock Update:** Runs every 12 hours

## Manual Testing

### Test 1: Verify Celery Worker Connection
```bash
celery -A crm inspect ping
```

Expected output:
```
-> celery@hostname: OK
    pong
```

### Test 2: Manually Trigger the Report Task

#### Using Django Shell:
```bash
python manage.py shell
```

Inside the shell:
```python
from crm.tasks import generate_crm_report

# Run task asynchronously
result = generate_crm_report.delay()
print(f"Task ID: {result.id}")

# Or run synchronously for immediate testing
result = generate_crm_report()
print(result)

exit()
```

#### Using Celery Command:
```bash
celery -A crm call crm.tasks.generate_crm_report
```

### Test 3: Check the Report Log
```bash
# View the entire log
cat /tmp/crm_report_log.txt

# View last 20 lines
tail -n 20 /tmp/crm_report_log.txt

# Watch log in real-time
tail -f /tmp/crm_report_log.txt
```

### Test 4: Verify GraphQL Endpoint

Visit `http://localhost:8000/graphql` and run:
```graphql
query {
  allCustomers {
    edges {
      node {
        id
        name
        email
      }
    }
  }
  allOrders {
    edges {
      node {
        id
        totalAmount
      }
    }
  }
}
```

## Verification

### Verify Logs in /tmp/crm_report_log.txt

After running the task, check the log file:
```bash
cat /tmp/crm_report_log.txt
```

Expected output format:
```
2025-10-31 15:30:00 - Report: 5 customers, 10 orders, $1250.50 revenue.
2025-11-04 06:00:00 - Report: 7 customers, 15 orders, $2100.75 revenue.
```

### Verify All Components Are Running
```bash
# Check Django server
curl http://localhost:8000

# Check Redis
redis-cli ping

# Check Celery worker
celery -A crm inspect active

# Check Celery Beat scheduler
celery -A crm inspect scheduled
```

## Monitoring

### View Celery Worker Status
```bash
# Check active tasks
celery -A crm inspect active

# Check registered tasks
celery -A crm inspect registered

# Check worker statistics
celery -A crm inspect stats

# Check reserved tasks
celery -A crm inspect reserved
```

### View Scheduled Tasks
```bash
# View scheduled tasks
celery -A crm inspect scheduled

# View Celery Beat schedule
celery -A crm beat --help
```

### Monitor Logs in Real-Time
```bash
# Monitor CRM report log
tail -f /tmp/crm_report_log.txt

# Monitor Celery worker output (in worker terminal)
# Monitor Celery beat output (in beat terminal)
```

### Django Admin Interface for Celery Beat

Manage periodic tasks via Django Admin:

1. Start Django server: `python manage.py runserver`
2. Access Django Admin: `http://localhost:8000/admin/`
3. Login with your superuser credentials
4. Navigate to: **Periodic Tasks** under **Django Celery Beat**
5. View, edit, create, or delete periodic tasks
6. Manage crontab schedules, intervals, and clocked schedules

## Troubleshooting

### Issue 1: Redis Connection Errors

**Error:** `Error 111 connecting to localhost:6379. Connection refused.`

**Solution:**
```bash
# Check if Redis is running
sudo systemctl status redis-server  # Linux
brew services list  # macOS

# Start Redis if not running
sudo systemctl start redis-server  # Linux
brew services start redis  # macOS

# Test connection
redis-cli ping
```

### Issue 2: Celery Worker Not Processing Tasks

**Symptoms:** Tasks are queued but not executed

**Solutions:**
1. Ensure Redis is running: `redis-cli ping`
2. Check `CELERY_BROKER_URL` in `settings.py` is correct
3. Restart the Celery worker
4. Check worker logs for errors
5. Verify task is registered: `celery -A crm inspect registered`

### Issue 3: Task Not Executing on Schedule

**Solutions:**
1. Ensure Celery Beat is running
2. Verify schedule configuration in `settings.py`
3. Check timezone settings match between Django and Celery
4. Verify migrations: `python manage.py migrate django_celery_beat`
5. Check Beat scheduler logs

### Issue 4: Import Errors

**Error:** `ModuleNotFoundError: No module named 'celery'`

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue 5: Permission Denied on Log File

**Error:** `PermissionError: [Errno 13] Permission denied: '/tmp/crm_report_log.txt'`

**Solution:**
```bash
# Create the file with proper permissions
touch /tmp/crm_report_log.txt
chmod 666 /tmp/crm_report_log.txt
```

### Issue 6: GraphQL Endpoint Unreachable

**Solution:**
1. Ensure Django server is running: `python manage.py runserver`
2. Verify GraphQL is configured in `urls.py`
3. Test endpoint manually: `http://localhost:8000/graphql`

### View Detailed Logs

Celery worker and beat processes output logs directly to the terminal where they're running. Monitor these terminals for detailed error messages and debugging information.

## Production Deployment

### Best Practices for Production

1. **Use a Process Manager**
   - Use **Supervisor**, **systemd**, or **Docker** to keep Celery workers running
   - Automatically restart workers if they crash

2. **Redis Configuration**
   - Enable Redis persistence (RDB or AOF)
   - Configure Redis authentication
   - Use Redis Sentinel for high availability

3. **Security**
   - Don't use `DEBUG = True` in production
   - Use environment variables for sensitive settings
   - Configure proper firewall rules

4. **Monitoring**
   - Set up logging to files or external services
   - Use monitoring tools like Flower, Prometheus, or Datadog
   - Set up alerts for task failures

5. **Performance**
   - Consider using RabbitMQ for high-traffic applications
   - Scale workers horizontally
   - Use task result expiration to prevent memory issues

### Example Supervisor Configuration

Create `/etc/supervisor/conf.d/celery.conf`:
```ini
[program:celery-worker]
command=/path/to/venv/bin/celery -A crm worker -l info
directory=/path/to/project
user=your-user
numprocs=1
stdout_logfile=/var/log/celery/worker.log
stderr_logfile=/var/log/celery/worker_err.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
killasgroup=true
priority=998

[program:celery-beat]
command=/path/to/venv/bin/celery -A crm beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
directory=/path/to/project
user=your-user
numprocs=1
stdout_logfile=/var/log/celery/beat.log
stderr_logfile=/var/log/celery/beat_err.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
killasgroup=true
priority=999
```

Then:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start celery-worker celery-beat
sudo supervisorctl status
```

### Example systemd Service Files

**Celery Worker** (`/etc/systemd/system/celery-worker.service`):
```ini
[Unit]
Description=Celery Worker
After=network.target redis.target

[Service]
Type=forking
User=your-user
Group=your-group
WorkingDirectory=/path/to/project
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/celery -A crm worker -l info --logfile=/var/log/celery/worker.log
Restart=always

[Install]
WantedBy=multi-user.target
```

**Celery Beat** (`/etc/systemd/system/celery-beat.service`):
```ini
[Unit]
Description=Celery Beat
After=network.target redis.target

[Service]
Type=simple
User=your-user
Group=your-group
WorkingDirectory=/path/to/project
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/celery -A crm beat -l info --logfile=/var/log/celery/beat.log
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start services:
```bash
sudo systemctl daemon-reload
sudo systemctl enable celery-worker celery-beat
sudo systemctl start celery-worker celery-beat
sudo systemctl status celery-worker celery-beat
```

### Docker Deployment

Example `docker-compose.yml`:
```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - redis

  celery-worker:
    build: .
    command: celery -A crm worker -l info
    volumes:
      - .:/app
    depends_on:
      - redis
      - web

  celery-beat:
    build: .
    command: celery -A crm beat -l info
    volumes:
      - .:/app
    depends_on:
      - redis
      - web
```

## Additional Resources

- [Celery Documentation](https://docs.celeryproject.org/)
- [Django Celery Beat Documentation](https://django-celery-beat.readthedocs.io/)
- [Redis Documentation](https://redis.io/documentation)
- [Django Documentation](https://docs.djangoproject.com/)
- [Graphene Django Documentation](https://docs.graphene-python.org/projects/django/)

## Project Structure
```
crm/
├── __init__.py              # Celery app initialization
├── celery.py                # Celery configuration
├── settings.py              # Django settings with Celery config
├── tasks.py                 # Celery tasks
├── cron.py                  # Django-crontab jobs
├── models.py                # Django models
├── schema.py                # GraphQL schema
├── urls.py                  # URL configuration
├── cron_jobs/               # Shell scripts for cron
│   ├── clean_inactive_customers.sh
│   ├── send_order_reminders.py
│   ├── customer_cleanup_crontab.txt
│   └── order_reminders_crontab.txt
└── README.md                # This file

requirements.txt             # Python dependencies
manage.py                    # Django management script
```

## Support and Contact

For issues, questions, or contributions:
- Check the project documentation
- Review the troubleshooting section
- Contact the development team
- Submit issues on the project repository

## License

[Include your license information here]

---

**Last Updated:** October 2025
**Version:** 1.0