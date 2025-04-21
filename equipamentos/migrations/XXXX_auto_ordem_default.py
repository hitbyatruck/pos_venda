from django.db import migrations, models

def set_default_ordem(apps, schema_editor):
    CategoriaEquipamento = apps.get_model('equipamentos', 'CategoriaEquipamento')

    # Set ordem values for existing categories
    for i, categoria in enumerate(CategoriaEquipamento.objects.all().order_by('id')):
        categoria.ordem = (i + 1) * 10
        categoria.save()

class Migration(migrations.Migration):

    dependencies = [
        ('equipamentos', '0001_initial'),  # Update this to point to your last migration
    ]

    operations = [
        # First ensure the field exists
        migrations.AddField(
            model_name='categoriaequipamento',
            name='ordem',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        # Then run the data migration
        migrations.RunPython(set_default_ordem, migrations.RunPython.noop),
    ]
