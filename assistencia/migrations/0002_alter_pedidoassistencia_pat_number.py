# Generated by Django 5.1.5 on 2025-03-20 21:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assistencia', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pedidoassistencia',
            name='pat_number',
            field=models.CharField(max_length=10, unique=True, verbose_name='Número da PAT'),
        ),
    ]
