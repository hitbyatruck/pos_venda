from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('equipamentos', '0001_initial'),  # Replace with your last migration
    ]

    operations = [
        migrations.AddField(
            model_name='categoriaequipamento',
            name='data_criacao',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='categoriaequipamento',
            name='data_atualizacao',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
