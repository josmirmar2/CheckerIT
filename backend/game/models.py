from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

ROW_LENGTHS = (1,2,3,4,13,12,11,10,9,10,11,12,13,4,3,2,1,)


def is_valid_position_key(key: str) -> bool:
    if not isinstance(key, str):
        return False
    if "-" not in key:
        return False

    col_str, row_str = key.split("-", 1)
    try:
        col = int(col_str)
        row = int(row_str)
    except Exception:
        return False

    if row < 0 or row >= len(ROW_LENGTHS):
        return False

    row_len = ROW_LENGTHS[row]
    return 0 <= col < row_len


def validate_position_key(key: str) -> None:
    if not is_valid_position_key(key):
        raise ValidationError("Posición inválida: fuera del tablero")


class Jugador(models.Model):
    """
    Modelo para representar un jugador (humano o IA)
    """
    id_jugador = models.CharField(max_length=50, primary_key=True)
    nombre = models.CharField(max_length=100)
    humano = models.BooleanField(default=True)
    numero = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Jugadores"

    def __str__(self):
        return self.nombre


class Partida(models.Model):
    """
    Modelo para representar una partida de Damas Chinas
    Relación: Jugador 2..6 --> 0..* Partida
    """
    ESTADOS = [
        ('EN_CURSO', 'En curso'),
        ('PAUSADA', 'Pausada'),
        ('FINALIZADA', 'Finalizada'),
    ]

    id_partida = models.CharField(max_length=50, primary_key=True)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    tiempo_sobrante = models.IntegerField(default=0) 
    estado = models.CharField(max_length=20, choices=ESTADOS, default='EN_CURSO')
    numero_jugadores = models.IntegerField(
        validators=[MinValueValidator(2), MaxValueValidator(6)]
    )
    jugadores = models.ManyToManyField(
        Jugador,
        related_name='partidas',  # Relación: Jugador 2..6 --> 0..* Partida
        through='JugadorPartida'
    )

    class Meta:
        verbose_name_plural = "Partidas"
        constraints = [
            models.CheckConstraint(
                check=models.Q(numero_jugadores__gte=2) & models.Q(numero_jugadores__lte=6),
                name="partida_numero_jugadores_between_2_6",
            )
            ,
            models.CheckConstraint(
                check=models.Q(fecha_fin__isnull=True) | models.Q(fecha_fin__gt=models.F('fecha_inicio')),
                name="partida_fecha_fin_after_fecha_inicio",
            )
        ]

    def __str__(self):
        return f"Partida {self.id_partida}"


class Pieza(models.Model):
    """
    Modelo para representar una pieza del juego
    Relación: Jugador 1 --> 1..* Pieza
    Relación: IA 1 -- 0..* Pieza
    Relación: Chatbot 1 -- 0..* Pieza
    """
    id_pieza = models.CharField(max_length=50, primary_key=True)
    tipo = models.CharField(max_length=50)
    posicion = models.CharField(
        max_length=10,
        validators=[validate_position_key],
    )
    jugador = models.ForeignKey(
        Jugador, 
        on_delete=models.CASCADE, 
        related_name='piezas'  # Jugador 1 --> 1..* Pieza
    )
    ia = models.ForeignKey(
        'IA',
        on_delete=models.CASCADE,
        related_name='piezas',  # IA 1 -- 0..* Pieza
        null=True,
        blank=True
    )
    chatbot = models.ForeignKey(
        'Chatbot',
        on_delete=models.CASCADE,
        related_name='piezas',  # ChatBot 1 -- 0..* Pieza
        null=True,
        blank=True
    )
    partida = models.ForeignKey(
        Partida,
        on_delete=models.CASCADE,
        related_name='piezas',  # Partida 1 --> 1..* Pieza
        null=True,
        blank=True
    )

    class Meta:
        verbose_name_plural = "Piezas"

    def __str__(self):
        return f"{self.tipo} de {self.jugador}"




class Turno(models.Model):
    """
    Modelo para representar un turno en la partida
    Relación: Partida 1 --> 1..* Turno
    Relación: Turno 1 --> 0..* Movimiento
    """
    id_turno = models.CharField(max_length=50, primary_key=True)
    jugador = models.ForeignKey(
        Jugador, 
        on_delete=models.CASCADE,
        related_name='turnos'
    )
    numero = models.IntegerField()
    inicio = models.DateTimeField(auto_now_add=True)
    fin = models.DateTimeField(null=True, blank=True)
    partida = models.ForeignKey(
        Partida, 
        on_delete=models.CASCADE, 
        related_name='turnos'  # Partida 1 --> 1..* Turno
    )

    class Meta:
        verbose_name_plural = "Turnos"
        constraints = [
            models.CheckConstraint(
                check=models.Q(fin__isnull=True) | models.Q(fin__gt=models.F('inicio')),
                name="turno_fin_after_inicio",
            )
        ]

    def __str__(self):
        return f"Turno {self.numero} de {self.jugador}"


class Movimiento(models.Model):
    """
    Modelo para representar un movimiento de una pieza
    Relación: Partida 1 --> 0..* Movimiento
    Relación: Turno 1 --> 0..* Movimiento
    Relación: Pieza 1 --> 1 Movimiento
    """
    id_movimiento = models.CharField(max_length=50, primary_key=True)
    jugador = models.ForeignKey(
        Jugador, 
        on_delete=models.CASCADE,
        related_name='movimientos'
    )
    pieza = models.ForeignKey(
        Pieza, 
        on_delete=models.CASCADE,
        related_name='movimientos'  # Pieza 1 --> 0..* Movimiento
    )
    turno = models.ForeignKey(
        Turno, 
        on_delete=models.CASCADE, 
        related_name='movimientos'  # Turno 1 --> 0..* Movimiento
    )
    partida = models.ForeignKey(
        Partida,
        on_delete=models.CASCADE,
        related_name='movimientos',  # Partida 1 --> 0..* Movimiento
        null=True,
        blank=True
    )
    origen = models.CharField(max_length=10, validators=[validate_position_key])
    destino = models.CharField(max_length=10, validators=[validate_position_key])

    class Meta:
        verbose_name_plural = "Movimientos"

    def __str__(self):
        return f"{self.pieza} de {self.origen} a {self.destino}"


class IA(models.Model):
    """
    Modelo para representar la configuración de IA de un jugador
    Relación: Jugador 1 --> 0..1 IA
    Relación: IA 1 --> 1..* Pieza
    Relación: Chatbot 1 --> 1 IA (inversa)
    """
    jugador = models.OneToOneField(
        Jugador, 
        on_delete=models.CASCADE, 
        primary_key=True,
        related_name='ia'  # Jugador 1 --> 0..1 IA
    )
    nivel = models.IntegerField()

    class Meta:
        verbose_name = "IA"
        verbose_name_plural = "IAs"

    def __str__(self):
        return f"IA Nivel {self.nivel} del jugador {self.jugador}"


class Chatbot(models.Model):
    """
    Modelo para representar el chatbot de ayuda
    Relación: Chatbot 1 --> 1 IA
    """
    ia = models.OneToOneField(
        IA,
        on_delete=models.CASCADE,
        related_name='chatbot',  # Chatbot 1 --> 1 IA
        null=True,
        blank=True
    )
    memoria = models.JSONField(default=dict)
    contexto = models.JSONField(default=dict)

    class Meta:
        verbose_name_plural = "Chatbots"

    def __str__(self):
        return "Chatbot"


class JugadorPartida(models.Model):
    """
    Modelo para representar la participación de jugadores en partidas
    Relación: Jugador 2..6 --> 0..* Partida (through)
    """
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE)
    partida = models.ForeignKey(Partida, on_delete=models.CASCADE)
    fecha_union = models.DateTimeField(auto_now_add=True)
    orden_participacion = models.IntegerField()

    class Meta:
        verbose_name_plural = "Participaciones en Partida"
        unique_together = ('jugador', 'partida')

    def __str__(self):
        return f"{self.jugador} en {self.partida}"
