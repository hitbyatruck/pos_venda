# Generated by Django 5.1.5 on 2025-02-18 21:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assistencia', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pedidoassistencia',
            name='data_criacao',
        ),
    ]
