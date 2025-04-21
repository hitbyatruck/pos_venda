from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('equipamentos', '0001_initial'),  # Adjust this to your latest migration
    ]

    operations = [
        migrations.AddField(
            model_name='categoriaequipamento',
            name='ativo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='categoriaequipamento',
            name='cor',
            field=models.CharField(blank=True, help_text='Código de cor em hexadecimal (ex: #FF5733)', max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='categoriaequipamento',
            name='icone',
            field=models.CharField(blank=True, help_text='Nome do ícone FontAwesome (ex: fa-wrench)', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='categoriaequipamento',
            name='ordem',
            field=models.PositiveIntegerField(default=0, help_text='Ordem de exibição'),
        ),
        migrations.AddField(
            model_name='categoriaequipamento',
            name='pai',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subcategorias', to='equipamentos.categoriaequipamento'),
        ),
    ]
