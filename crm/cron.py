"""
Cron jobs for the CRM application.
"""

from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport


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
        # Set up the GraphQL client
        transport = RequestsHTTPTransport(
            url='http://localhost:8000/graphql',
            use_json=True,
        )
        
        client = Client(transport=transport, fetch_schema_from_transport=True)
        
        # Define the GraphQL query
        query = gql("""
            query {
                hello
            }
        """)
        
        # Execute the query
        result = client.execute(query)
        
        if 'hello' in result:
            heartbeat_message += f" - GraphQL endpoint responsive: {result['hello']}"
        else:
            heartbeat_message += " - GraphQL endpoint responded but no hello field"
    
    except Exception as e:
        heartbeat_message += f" - GraphQL endpoint unreachable: {str(e)}"
    
    # Append to log file (does not overwrite)
    with open('/tmp/crm_heartbeat_log.txt', 'a') as log_file:
        log_file.write(heartbeat_message + '\n')
    
    # Optional: print to console for debugging
    print(heartbeat_message)