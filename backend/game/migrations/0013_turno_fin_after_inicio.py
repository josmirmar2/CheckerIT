from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0012_partida_fecha_fin_after_inicio"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="turno",
            constraint=models.CheckConstraint(
                check=models.Q(fin__isnull=True) | models.Q(fin__gt=models.F("inicio")),
                name="turno_fin_after_inicio",
            ),
        ),
    ]
