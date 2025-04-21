"""
Data population script for the POS/post-sales system.
Populates the database with sample data for testing and demonstration purposes.
"""
import os
import sys
import django
import random
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_venda.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction

# Import models from all apps
from clientes.models import Cliente, Contacto
from equipamentos.models import EquipamentoCliente, EquipamentoFabricado, CategoriaEquipamento
from assistencia.models import PedidoAssistencia, ItemPAT
from stock.models import Peca, Fornecedor, CategoriaPeca, MovimentacaoStock, EncomendaPeca
from notas.models import Nota, Tarefa

User = get_user_model()

def create_users(num_users=5):
    """Create sample users"""
    print("Creating users...")
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            first_name='Admin',
            last_name='User'
        )
        print(f"  Created admin user: {admin_user.username}")

    users = [admin_user]

    # Create regular staff users
    staff_roles = ['Técnico', 'Vendedor', 'Gerente', 'Assistente']
    for i in range(1, num_users):
        role = random.choice(staff_roles)
        username = f"user{i}"

        # Skip if user already exists
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            users.append(user)
            print(f"  Using existing user: {user.username}")
            continue

        user = User.objects.create_user(
            username=username,
            email=f"user{i}@example.com",
            password=f"password{i}",
            first_name=f"Nome{i}",
            last_name=f"Sobrenome{i}",
            is_staff=True
        )
        users.append(user)
        print(f"  Created user: {user.username}")

    return users

def create_clients(num_clients=20, users=None):
    """Create sample clients"""
    print("Creating clients...")
    clients = []

    for i in range(1, num_clients + 1):
        # Skip if client already exists
        if Cliente.objects.filter(nome=f"Cliente Teste {i}").exists():
            client = Cliente.objects.get(nome=f"Cliente Teste {i}")
            clients.append(client)
            print(f"  Using existing client: {client.nome}")
            continue

        client = Cliente.objects.create(
            nome=f"Cliente Teste {i}",
            email_principal=f"cliente{i}@example.com",
            nif=f"5001231{i:02d}",
            morada=f"Rua Teste {i}, nº {i}",
            codigo_postal=f"1000-{i:03d}",
            cidade="Lisboa"
        )

        # Create contacts for each client
        for j in range(1, random.randint(1, 3)):
            try:
                contacto = Contacto.objects.create(
                    cliente=client,
                    tipo="email" if j % 2 == 0 else "telefone",
                    valor=f"contacto{j}@example.com" if j % 2 == 0 else f"9{j}12345{i:02d}",
                    nome_contacto=f"Contacto {j}",
                    cargo=random.choice(["Gerente", "Diretor", "Técnico", "Admin"])
                )
            except Exception as e:
                print(f"    Error creating contact for {client.nome}: {e}")

        clients.append(client)
        print(f"  Created client: {client.nome}")

    return clients

def create_equipment_categories():
    """Create equipment categories"""
    print("Creating equipment categories...")
    categories = []

    category_names = [
        "Servidores", "Desktops", "Portáteis", "Impressoras",
        "Switches", "Routers", "Access Points", "Monitores"
    ]

    for name in category_names:
        if CategoriaEquipamento.objects.filter(nome=name).exists():
            category = CategoriaEquipamento.objects.get(nome=name)
            categories.append(category)
            print(f"  Using existing category: {category.nome}")
            continue

        category = CategoriaEquipamento.objects.create(
            nome=name,
            descricao=f"Categoria para {name}"
        )
        categories.append(category)
        print(f"  Created category: {category.nome}")

    return categories

# Additional functions for creating equipment, parts, service requests, etc.

def populate_all():
    """Main function to populate all data"""
    print("\n=== Populating Test Data ===\n")

    with transaction.atomic():
        # Create users first as they're needed for other objects
        users = create_users(5)

        # Create clients
        clients = create_clients(20, users)

        # Create equipment categories and equipment
        categories = create_equipment_categories()

        # You would add more data population functions here

    print("\n=== Data Population Complete ===\n")

if __name__ == "__main__":
    populate_all()
