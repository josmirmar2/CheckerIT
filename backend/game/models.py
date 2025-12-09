from django.db import models


class Jugador(models.Model):
    """
    Modelo para representar un jugador (humano o IA)
    """
    id_jugador = models.CharField(max_length=50, primary_key=True)
    nombre = models.CharField(max_length=100)
    humano = models.BooleanField(default=True)

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
    estado = models.CharField(max_length=20, choices=ESTADOS, default='EN_CURSO')
    numero_jugadores = models.IntegerField()
    jugador_actual = models.ForeignKey(
        Jugador, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='partidas_actual'  # Jugador actual en una partida
    )
    jugadores = models.ManyToManyField(
        Jugador,
        related_name='partidas',  # Relación: Jugador 2..6 --> 0..* Partida
        through='ParticipacionPartida'
    )
    tablero = models.OneToOneField(
        'Tablero',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='partida'  # Composición: Tablero 1 --> 1 Partida
    )

    class Meta:
        verbose_name_plural = "Partidas"

    def __str__(self):
        return f"Partida {self.id_partida}"


class Pieza(models.Model):
    """
    Modelo para representar una pieza del juego
    Relación: Jugador 1 --> 1..* Pieza
    Relación: Tablero 1 -- 0..* Pieza
    """
    id_pieza = models.CharField(max_length=50, primary_key=True)
    tipo = models.CharField(max_length=50)
    posicion = models.CharField(max_length=10)  # Ej: "A3", "B10", coordenadas del tablero
    jugador = models.ForeignKey(
        Jugador, 
        on_delete=models.CASCADE, 
        related_name='piezas'  # Jugador 1 --> 1..* Pieza
    )
    tablero = models.ForeignKey(
        'Tablero',
        on_delete=models.CASCADE,
        related_name='piezas',  # Tablero 1 -- 0..* Pieza
        null=True,
        blank=True
    )

    class Meta:
        verbose_name_plural = "Piezas"

    def __str__(self):
        return f"{self.tipo} de {self.jugador}"


class Tablero(models.Model):
    """
    Modelo para representar el tablero del juego
    Relación: Tablero 1 --> 1 Partida (Composición)
    Relación: Tablero 1 -- 0..* Pieza
    Relación: IA 1 --> 1 Tablero (inversa)
    """
    id_tablero = models.CharField(max_length=50, primary_key=True)
    dimension = models.CharField(max_length=50)  # puede ser "10x10", "Hexagonal", etc.
    estado_casillas = models.JSONField()  # Mapa String-Pieza JSON
    historial = models.JSONField(default=list)  # Lista de Strings

    class Meta:
        verbose_name_plural = "Tableros"

    def __str__(self):
        return f"Tablero {self.id_tablero}"


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
    pieza = models.OneToOneField(
        Pieza, 
        on_delete=models.CASCADE,
        related_name='movimiento'  # Pieza 1 --> 1 Movimiento
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
    origen = models.CharField(max_length=10)
    destino = models.CharField(max_length=10)
    inicio = models.DateTimeField(auto_now_add=True)
    fin = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Movimientos"

    def __str__(self):
        return f"{self.pieza} de {self.origen} a {self.destino}"


class IA(models.Model):
    """
    Modelo para representar la configuración de IA de un jugador
    Relación: Jugador 1 --> 0..1 IA
    Relación: IA 1 --> 1 Tablero
    Relación: Chatbot 1 --> 1 IA (inversa)
    """
    jugador = models.OneToOneField(
        Jugador, 
        on_delete=models.CASCADE, 
        primary_key=True,
        related_name='ia'  # Jugador 1 --> 0..1 IA
    )
    nivel = models.IntegerField()
    tablero = models.OneToOneField(
        Tablero,
        on_delete=models.CASCADE,
        related_name='ia',  # IA 1 --> 1 Tablero
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "IA"
        verbose_name_plural = "IAs"

    def __str__(self):
        return f"IA Nivel {self.nivel} del jugador {self.jugador}"


class Chatbot(models.Model):
    """
    Modelo para representar el chatbot de ayuda
    Relación: Chatbot 1 --> 1 IA
    Relación: Chatbot 1 --> 1 Tablero
    """
    ia = models.OneToOneField(
        IA,
        on_delete=models.CASCADE,
        related_name='chatbot',  # Chatbot 1 --> 1 IA
        null=True,
        blank=True
    )
    tablero = models.OneToOneField(
        Tablero,
        on_delete=models.CASCADE,
        related_name='chatbot',  # Chatbot 1 --> 1 Tablero
        null=True,
        blank=True
    )
    memoria = models.JSONField(default=dict)
    contexto = models.JSONField(default=dict)

    class Meta:
        verbose_name_plural = "Chatbots"

    def __str__(self):
        return "Chatbot"


class ParticipacionPartida(models.Model):
    """
    Modelo para representar la participación de jugadores en partidas
    Relación: Jugador 2..6 --> 0..* Partida (through)
    """
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE)
    partida = models.ForeignKey(Partida, on_delete=models.CASCADE)
    fecha_union = models.DateTimeField(auto_now_add=True)
    orden_participacion = models.IntegerField()  # Orden en que se unió

    class Meta:
        verbose_name_plural = "Participaciones en Partida"
        unique_together = ('jugador', 'partida')

    def __str__(self):
        return f"{self.jugador} en {self.partida}"
