# CRM Application with Celery Task Scheduling

This CRM application uses Celery with Redis as a message broker for asynchronous task processing and scheduled report generation.

## Prerequisites

- Python 3.8+
- Django
- Redis server
- Virtual environment (recommended)

## Installation Steps

### 1. Install Redis

#### On Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### On macOS (using Homebrew):
```bash
brew install redis
brew services start redis
```

#### On Windows:
Download Redis from https://github.com/microsoftarchive/redis/releases or use WSL2.

### 2. Verify Redis is Running
```bash
redis-cli ping
# Should return: PONG
```

### 3. Install Python Dependencies
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Run Database Migrations
```bash
python manage.py migrate
```

### 5. Create Celery Beat Database Tables
```bash
python manage.py migrate django_celery_beat
```

## Running the Application

You need to run **three separate terminal windows/processes**:

### Terminal 1: Django Development Server
```bash
python manage.py runserver
```

### Terminal 2: Celery Worker
```bash
celery -A crm worker -l info
```

### Terminal 3: Celery Beat Scheduler
```bash
celery -A crm beat -l info
```

## Scheduled Tasks

### CRM Weekly Report
- **Task:** `generate_crm_report`
- **Schedule:** Every Monday at 6:00 AM UTC
- **Purpose:** Generates a summary report of:
  - Total number of customers
  - Total number of orders
  - Total revenue
- **Log Location:** `/tmp/crm_report_log.txt`

## Manual Testing

### Test the Celery Worker Connection
```bash
celery -A crm inspect ping
```

### Manually Trigger the Report Task
```bash
python manage.py shell
```

In the Python shell:
```python
from crm.tasks import generate_crm_report
result = generate_crm_report.delay()
print(result.id)
exit()
```

### Check the Report Log
```bash
cat /tmp/crm_report_log.txt
```

## Monitoring

### View Celery Worker Status
```bash
celery -A crm inspect active
celery -A crm inspect stats
```

### View Scheduled Tasks
```bash
celery -A crm inspect scheduled
```

### Monitor Logs in Real-Time
```bash
tail -f /tmp/crm_report_log.txt
```

## Django Admin Interface for Celery Beat

You can manage periodic tasks via Django Admin:

1. Access Django Admin: `http://localhost:8000/admin/`
2. Navigate to: **Periodic Tasks** under **Django Celery Beat**
3. View, edit, or create new periodic tasks

## Troubleshooting

### Redis Connection Issues
```bash
# Check if Redis is running
sudo systemctl status redis-server  # Linux
brew services list  # macOS

# Test Redis connection
redis-cli ping
```

### Celery Worker Not Processing Tasks
- Ensure Redis is running
- Check that `CELERY_BROKER_URL` in settings.py is correct
- Restart the Celery worker

### Task Not Executing on Schedule
- Ensure Celery Beat is running
- Check the schedule configuration in `settings.py`
- Verify timezone settings

### View Celery Logs
The Celery worker and beat processes output logs directly to the terminal. Monitor these for errors.

## Production Deployment

For production environments:

1. Use a process manager like **Supervisor** or **systemd** to keep Celery workers running
2. Configure Redis with persistence and security
3. Use a dedicated message broker like RabbitMQ for high-traffic applications
4. Set up proper logging and monitoring
5. Use environment variables for sensitive configuration

### Example Supervisor Configuration
```ini
[program:celery-worker]
command=/path/to/venv/bin/celery -A crm worker -l info
directory=/path/to/project
user=your-user
autostart=true
autorestart=true
stdout_logfile=/var/log/celery/worker.log
stderr_logfile=/var/log/celery/worker_err.log

[program:celery-beat]
command=/path/to/venv/bin/celery -A crm beat -l info
directory=/path/to/project
user=your-user
autostart=true
autorestart=true
stdout_logfile=/var/log/celery/beat.log
stderr_logfile=/var/log/celery/beat_err.log
```

## Additional Resources

- [Celery Documentation](https://docs.celeryproject.org/)
- [Django Celery Beat Documentation](https://django-celery-beat.readthedocs.io/)
- [Redis Documentation](https://redis.io/documentation)

## Support

For issues or questions, please refer to the project documentation or contact the development team.