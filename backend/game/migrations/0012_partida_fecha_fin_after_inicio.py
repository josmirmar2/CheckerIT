from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0011_partida_numero_jugadores_constraints"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="partida",
            constraint=models.CheckConstraint(
                check=models.Q(fecha_fin__isnull=True) | models.Q(fecha_fin__gt=models.F("fecha_inicio")),
                name="partida_fecha_fin_after_fecha_inicio",
            ),
        ),
    ]
