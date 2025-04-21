from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('equipamentos', '0001_initial'),  # Update this to match your last migration
    ]

    operations = [
        migrations.AddField(
            model_name='categoriaequipamento',
            name='ativo',
            field=models.BooleanField(default=True, verbose_name='Ativo'),
        ),
    ]
