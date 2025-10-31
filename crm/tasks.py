"""
Celery tasks for CRM application.
"""

import requests
from celery import shared_task
from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from decimal import Decimal


@shared_task
def generate_crm_report():
    """
    Generate a weekly CRM report summarizing:
    - Total number of customers
    - Total number of orders
    - Total revenue (sum of total_amount from orders)
    
    Logs the report to /tmp/crm_report_log.txt
    """
    try:
        # Set up the GraphQL client
        transport = RequestsHTTPTransport(
            url='http://localhost:8000/graphql',
            use_json=True,
        )
        
        client = Client(transport=transport, fetch_schema_from_transport=True)
        
        # Define the GraphQL query to fetch CRM statistics
        query = gql("""
            query {
                allCustomers {
                    edges {
                        node {
                            id
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
        """)
        
        # Execute the query
        result = client.execute(query)
        
        # Calculate statistics
        customers = result.get('allCustomers', {}).get('edges', [])
        total_customers = len(customers)
        
        orders = result.get('allOrders', {}).get('edges', [])
        total_orders = len(orders)
        
        # Calculate total revenue
        total_revenue = Decimal('0.00')
        for order in orders:
            order_node = order.get('node', {})
            amount = order_node.get('totalAmount', '0')
            if amount:
                total_revenue += Decimal(str(amount))
        
        # Format timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create report message
        report_message = (
            f"{timestamp} - Report: {total_customers} customers, "
            f"{total_orders} orders, ${total_revenue:.2f} revenue."
        )
        
        # Log to file
        with open('/tmp/crm_report_log.txt', 'a') as log_file:
            log_file.write(report_message + '\n')
        
        print(f"CRM Report generated: {report_message}")
        return report_message
        
    except Exception as e:
        error_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_message = f"{error_timestamp} - ERROR: {str(e)}"
        
        with open('/tmp/crm_report_log.txt', 'a') as log_file:
            log_file.write(error_message + '\n')
        
        print(f"Error generating CRM report: {e}")
        raise