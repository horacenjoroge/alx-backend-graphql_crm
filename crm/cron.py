"""
Cron jobs for the CRM application.
"""

from datetime import datetime
import requests


def log_crm_heartbeat():
    """
    Log a heartbeat message to confirm CRM application health.
    Logs every 5 minutes in the format: DD/MM/YYYY-HH:MM:SS CRM is alive
    Optionally queries the GraphQL hello field to verify endpoint is responsive.
    """
    # Get current timestamp in the required format
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    
    # Base heartbeat message
    heartbeat_message = f"{timestamp} CRM is alive"
    
    # Optional: Query GraphQL endpoint to verify it's responsive
    try:
        response = requests.post(
            'http://localhost:8000/graphql',
            json={'query': '{ hello }'},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'hello' in data['data']:
                heartbeat_message += f" - GraphQL endpoint responsive: {data['data']['hello']}"
            else:
                heartbeat_message += " - GraphQL endpoint responded but no hello field"
        else:
            heartbeat_message += f" - GraphQL endpoint returned status {response.status_code}"
    
    except requests.exceptions.RequestException as e:
        heartbeat_message += f" - GraphQL endpoint unreachable: {str(e)}"
    
    # Append to log file (does not overwrite)
    with open('/tmp/crm_heartbeat_log.txt', 'a') as log_file:
        log_file.write(heartbeat_message + '\n')
    
    # Optional: print to console for debugging
    print(heartbeat_message)