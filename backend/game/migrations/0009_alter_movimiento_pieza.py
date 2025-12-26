from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0008_pieza_partida'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movimiento',
            name='pieza',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='movimientos', to='game.pieza'),
        ),
    ]
