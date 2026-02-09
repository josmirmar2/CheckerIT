from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0010_partida_tiempo_sobrante"),
    ]

    operations = [
        migrations.AlterField(
            model_name="partida",
            name="numero_jugadores",
            field=models.IntegerField(
                validators=[
                    django.core.validators.MinValueValidator(2),
                    django.core.validators.MaxValueValidator(6),
                ]
            ),
        ),
        migrations.AddConstraint(
            model_name="partida",
            constraint=models.CheckConstraint(
                check=models.Q(numero_jugadores__gte=2) & models.Q(numero_jugadores__lte=6),
                name="partida_numero_jugadores_between_2_6",
            ),
        ),
    ]
