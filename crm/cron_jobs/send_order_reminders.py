#!/usr/bin/env python
"""
Script to send order reminders for pending orders from the last 7 days.
Queries the GraphQL endpoint and logs results.
"""

import os
import sys
from datetime import datetime, timedelta
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
import django
django.setup()

def send_order_reminders():
    """Query GraphQL for recent pending orders and log reminders."""
    
    # Set up the GraphQL client
    transport = RequestsHTTPTransport(
        url='http://localhost:8000/graphql',
        use_json=True,
    )
    
    client = Client(transport=transport, fetch_schema_from_transport=True)
    
    # Calculate date 7 days ago
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Define the GraphQL query
    query = gql("""
        query GetRecentOrders {
            allOrders {
                id
                orderDate
                customer {
                    email
                }
            }
        }
    """)
    
    try:
        # Execute the query
        result = client.execute(query)
        
        # Filter orders from the last 7 days
        orders = result.get('allOrders', [])
        recent_orders = []
        
        for order in orders:
            order_date_str = order.get('orderDate', '')
            if order_date_str >= seven_days_ago:
                recent_orders.append(order)
        
        # Log the reminders
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open('/tmp/order_reminders_log.txt', 'a') as log_file:
            log_file.write(f"\n[{timestamp}] Order Reminders Processing\n")
            log_file.write(f"{'='*50}\n")
            
            if recent_orders:
                for order in recent_orders:
                    order_id = order.get('id', 'N/A')
                    customer_email = order.get('customer', {}).get('email', 'N/A')
                    order_date = order.get('orderDate', 'N/A')
                    
                    log_entry = f"Order ID: {order_id} | Customer: {customer_email} | Date: {order_date}\n"
                    log_file.write(log_entry)
                
                log_file.write(f"Total reminders: {len(recent_orders)}\n")
            else:
                log_file.write("No pending orders found in the last 7 days.\n")
        
        print("Order reminders processed!")
        
    except Exception as e:
        error_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open('/tmp/order_reminders_log.txt', 'a') as log_file:
            log_file.write(f"[{error_timestamp}] ERROR: {str(e)}\n")
        print(f"Error processing order reminders: {e}")
        sys.exit(1)

if __name__ == '__main__':
    send_order_reminders()