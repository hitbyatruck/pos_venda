"""
Script to add custom fields for testing purposes
"""
import os
import sys
import django
from django.utils.text import slugify

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_venda.settings')
django.setup()

from configuracao.models import CustomField, CustomFieldValue

def create_custom_field(name, field_type, model, description=None, required=False, options=None, active=True, order=0):
    """Create a custom field with the proper fields based on the model structure"""
    key = slugify(name)  # Generate a valid slug for the key field

    # Check if field already exists
    if CustomField.objects.filter(name=name, model=model).exists():
        print(f"✓ Field '{name}' for model '{model}' already exists.")
        return CustomField.objects.get(name=name, model=model)

    # Create the custom field using the actual fields from the model
    field = CustomField(
        name=name,
        key=key,
        description=description or "",
        field_type=field_type,
        options=options or "",
        model=model,
        required=required,
        active=active,
        order=order
    )
    field.save()
    print(f"✓ Created new field: {field.name} ({field.key}) for {field.model}")
    return field

def add_client_fields():
    """Add custom fields for client model"""
    # Industry field (text)
    create_custom_field(
        name="Industry",
        field_type="text",
        model="cliente",
        description="Setor de atividade principal do cliente",
        required=False
    )

    # Client size (select)
    create_custom_field(
        name="Company Size",
        field_type="select",
        model="cliente",
        description="Tamanho/porte da empresa",
        options="micro,pequena,média,grande",
        required=False
    )

    # Tax ID (text)
    create_custom_field(
        name="Tax ID",
        field_type="text",
        model="cliente",
        description="Número de contribuinte ou NIF",
        required=False
    )

    return True

def add_equipment_fields():
    """Add custom fields for equipment model"""
    # Warranty expiration (date)
    create_custom_field(
        name="Warranty Expiration",
        field_type="date",
        model="equipamento",
        description="Data de término da garantia",
        required=False
    )

    # Maintenance interval (number)
    create_custom_field(
        name="Maintenance Interval",
        field_type="number",
        model="equipamento",
        description="Intervalo entre manutenções preventivas (em meses)",
        required=False
    )

    # Custom specifications (textarea)
    create_custom_field(
        name="Specifications",
        field_type="textarea",
        model="equipamento",
        description="Especificações técnicas personalizadas",
        required=False
    )

    return True

def add_pat_fields():
    """Add custom fields for service request (pat) model"""
    # Urgency level (select)
    create_custom_field(
        name="Urgency Level",
        field_type="select",
        model="pedidoassistencia",
        description="Nível de urgência do pedido",
        options="baixa,média,alta,crítica",
        required=False
    )

    # External reference (text)
    create_custom_field(
        name="External Reference",
        field_type="text",
        model="pedidoassistencia",
        description="Número de referência de sistema externo",
        required=False
    )

    return True

if __name__ == "__main__":
    print("Adding custom fields for testing...")
    print("\nAdding client fields:")
    add_client_fields()

    print("\nAdding equipment fields:")
    add_equipment_fields()

    print("\nAdding service request fields:")
    add_pat_fields()

    # Print summary
    print("\nCustom fields summary:")
    field_counts = {}
    for field in CustomField.objects.all():
        if field.model not in field_counts:
            field_counts[field.model] = 0
        field_counts[field.model] += 1

    for model, count in field_counts.items():
        print(f"- {model}: {count} fields")

    print("\nCustom fields added successfully.")
