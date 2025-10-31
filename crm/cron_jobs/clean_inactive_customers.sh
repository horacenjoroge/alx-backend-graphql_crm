#!/bin/bash

# Get the project root directory (assuming script is in crm/cron_jobs)
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# Navigate to project root
cd "$PROJECT_ROOT"

# Run Django shell command to delete inactive customers
python manage.py shell << EOF
from django.utils import timezone
from datetime import timedelta
from crm.models import Customer

# Calculate date one year ago
one_year_ago = timezone.now() - timedelta(days=365)

# Find customers with no orders since a year ago
inactive_customers = Customer.objects.filter(
    orders__order_date__lt=one_year_ago
).distinct() | Customer.objects.filter(orders__isnull=True)

# Count and delete
count = inactive_customers.count()
inactive_customers.delete()

# Log the result
from datetime import datetime
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
with open('/tmp/customer_cleanup_log.txt', 'a') as f:
    f.write(f"[{timestamp}] Deleted {count} inactive customers\n")

print(f"Deleted {count} inactive customers")
EOF