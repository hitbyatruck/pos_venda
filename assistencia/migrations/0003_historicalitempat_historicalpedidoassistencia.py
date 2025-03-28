# Generated by Django 5.1.5 on 2025-03-21 21:08

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
import simple_history.models
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assistencia', '0002_alter_pedidoassistencia_pat_number'),
        ('clientes', '0002_historicalcliente'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalItemPat',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('servico', 'Serviço'), ('componente', 'Componente')], db_index=True, max_length=20, verbose_name='Tipo')),
                ('referencia', models.CharField(help_text='Código de referência do serviço ou componente', max_length=100, verbose_name='Referência')),
                ('designacao', models.CharField(help_text='Descrição do serviço ou componente', max_length=255, verbose_name='Designação')),
                ('quantidade', models.PositiveIntegerField(default=1, help_text='Quantidade mínima é 1', validators=[django.core.validators.MinValueValidator(1)], verbose_name='Quantidade')),
                ('preco', models.DecimalField(decimal_places=2, help_text='Preço unitário em euros', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='Preço')),
                ('created_at', models.DateTimeField(blank=True, editable=False, verbose_name='Data de Criação')),
                ('updated_at', models.DateTimeField(blank=True, editable=False, verbose_name='Última Atualização')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('pat', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='assistencia.pedidoassistencia', verbose_name='PAT')),
            ],
            options={
                'verbose_name': 'historical Item de PAT',
                'verbose_name_plural': 'historical Itens de PAT',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalPedidoAssistencia',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('pat_number', models.CharField(db_index=True, max_length=10, verbose_name='Número da PAT')),
                ('data_entrada', models.DateField(default=django.utils.timezone.now, verbose_name='Data de Entrada')),
                ('estado', models.CharField(choices=[('aberto', 'Aberto'), ('em_curso', 'Em Curso'), ('concluido', 'Concluído'), ('cancelado', 'Cancelado'), ('em_diagnostico', 'Em Diagnóstico')], db_index=True, default='aberto', max_length=20, verbose_name='Estado da PAT')),
                ('relatorio', models.TextField(blank=True, null=True, verbose_name='Relatório')),
                ('garantia', models.BooleanField(default=False, help_text='Marque se o equipamento estiver em garantia.', verbose_name='Em Garantia')),
                ('data_reparacao', models.DateField(blank=True, null=True, verbose_name='Data de Reparação')),
                ('created_at', models.DateTimeField(blank=True, editable=False, verbose_name='Data de Criação')),
                ('updated_at', models.DateTimeField(blank=True, editable=False, verbose_name='Última Atualização')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('cliente', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='clientes.cliente', verbose_name='Cliente')),
                ('equipamento', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='clientes.equipamentocliente', verbose_name='Equipamento')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical Pedido de Assistência Técnica',
                'verbose_name_plural': 'historical Pedidos de Assistência Técnica',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
