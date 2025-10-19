# crm/schema.py

import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
import re
from decimal import Decimal


# GraphQL Types
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = '__all__'
        interfaces = (graphene.relay.Node,)


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = '__all__'
        interfaces = (graphene.relay.Node,)


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = '__all__'
        interfaces = (graphene.relay.Node,)


# Input Types for Mutations
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()


class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int()


class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime()


# Mutations
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, input):
        # Validate email format
        email_validator = EmailValidator()
        try:
            email_validator(input.email)
        except ValidationError:
            raise Exception("Invalid email format")

        # Check if email already exists
        if Customer.objects.filter(email=input.email).exists():
            raise Exception("Email already exists")

        # Validate phone format if provided
        if input.phone:
            phone_pattern = re.compile(r'^(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$')
            if not phone_pattern.match(input.phone):
                raise Exception("Invalid phone format. Use formats like +1234567890 or 123-456-7890")

        # Create customer using save()
        customer = Customer(
            name=input.name,
            email=input.email,
            phone=input.phone if input.phone else None
        )
        customer.save()

        return CreateCustomer(customer=customer, message="Customer created successfully")


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        customers = []
        errors = []
        email_validator = EmailValidator()
        phone_pattern = re.compile(r'^(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$')

        for idx, customer_input in enumerate(input):
            try:
                # Validate email
                email_validator(customer_input.email)

                # Check duplicate email
                if Customer.objects.filter(email=customer_input.email).exists():
                    errors.append(f"Row {idx + 1}: Email {customer_input.email} already exists")
                    continue

                # Validate phone if provided
                if customer_input.phone and not phone_pattern.match(customer_input.phone):
                    errors.append(f"Row {idx + 1}: Invalid phone format for {customer_input.email}")
                    continue

                # Create customer using save()
                customer = Customer(
                    name=customer_input.name,
                    email=customer_input.email,
                    phone=customer_input.phone if customer_input.phone else None
                )
                customer.save()
                customers.append(customer)

            except Exception as e:
                errors.append(f"Row {idx + 1}: {str(e)}")

        return BulkCreateCustomers(customers=customers, errors=errors)


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)

    def mutate(self, info, input):
        # Validate price is positive
        if input.price <= 0:
            raise Exception("Price must be positive")

        # Validate stock is non-negative
        stock = input.stock if input.stock is not None else 0
        if stock < 0:
            raise Exception("Stock cannot be negative")

        # Create product using save()
        product = Product(
            name=input.name,
            price=input.price,
            stock=stock
        )
        product.save()

        return CreateProduct(product=product)


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)

    def mutate(self, info, input):
        # Validate customer exists
        try:
            customer = Customer.objects.get(id=input.customer_id)
        except Customer.DoesNotExist:
            raise Exception(f"Customer with ID {input.customer_id} does not exist")

        # Validate at least one product
        if not input.product_ids or len(input.product_ids) == 0:
            raise Exception("At least one product must be selected")

        # Validate all products exist and calculate total
        products = []
        total_amount = Decimal('0.00')

        for product_id in input.product_ids:
            try:
                product = Product.objects.get(id=product_id)
                products.append(product)
                total_amount += product.price
            except Product.DoesNotExist:
                raise Exception(f"Product with ID {product_id} does not exist")

        # Create order using save()
        order = Order(
            customer=customer,
            total_amount=total_amount
        )
        if input.order_date:
            order.order_date = input.order_date
        order.save()

        # Associate products
        order.products.set(products)

        return CreateOrder(order=order)


# Query with Filtering
class Query(graphene.ObjectType):
    all_customers = DjangoFilterConnectionField(CustomerType, filterset_class=CustomerFilter)
    all_products = DjangoFilterConnectionField(ProductType, filterset_class=ProductFilter)
    all_orders = DjangoFilterConnectionField(OrderType, filterset_class=OrderFilter)


# Mutation
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()