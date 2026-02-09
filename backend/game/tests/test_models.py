import pytest
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from game.models import Jugador, Partida, JugadorPartida, Pieza, Turno, Movimiento


@pytest.mark.django_db
def test_jugador_str_devuelve_nombre():
    j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    assert str(j) == "Ana"


@pytest.mark.django_db
def test_partida_str_devuelve_id():
    p = Partida.objects.create(id_partida="P1", numero_jugadores=2)
    assert str(p) == "Partida P1"


@pytest.mark.django_db
def test_jugador_partida_no_permite_duplicados_misma_partida():
    j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    p = Partida.objects.create(id_partida="P1", numero_jugadores=2)

    JugadorPartida.objects.create(jugador=j, partida=p, orden_participacion=1)

    with pytest.raises(IntegrityError):
        JugadorPartida.objects.create(jugador=j, partida=p, orden_participacion=2)


@pytest.mark.django_db
def test_jugador_partida_creacion_y_conteo():
    j1 = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    j2 = Jugador.objects.create(id_jugador="J2", nombre="Pedro", humano=True, numero=2)
    p = Partida.objects.create(id_partida="P1", numero_jugadores=2)

    JugadorPartida.objects.create(jugador=j1, partida=p, orden_participacion=1)
    JugadorPartida.objects.create(jugador=j2, partida=p, orden_participacion=2)

    assert JugadorPartida.objects.filter(partida=p).count() == 2


@pytest.mark.django_db
def test_partida_numero_jugadores_entre_2_y_6_forzado_por_bd():
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Partida.objects.create(id_partida="P_BAD_1", numero_jugadores=1)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Partida.objects.create(id_partida="P_BAD_7", numero_jugadores=7)


@pytest.mark.django_db
def test_partida_fecha_fin_posterior_a_fecha_inicio_forzada_por_bd():
    # fecha_fin antes de la fecha_inicio (auto_now_add) debe fallar
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Partida.objects.create(
                id_partida="P_BAD_DATE",
                numero_jugadores=2,
                fecha_fin=timezone.now() - timedelta(days=1),
            )

    # Caso válido: se puede cerrar la partida en el futuro (o simplemente dejar fecha_fin en null)
    p = Partida.objects.create(id_partida="P_OK_DATE", numero_jugadores=2)
    p.fecha_fin = p.fecha_inicio + timedelta(seconds=1)
    p.save(update_fields=["fecha_fin"])

@pytest.mark.django_db
def test_pieza_str_incluye_tipo_y_jugador():
    j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    partida = Partida.objects.create(id_partida="P1", numero_jugadores=2)
    pieza = Pieza.objects.create(
        id_pieza="X1",
        tipo="punta-0",
        posicion="0-0",
        jugador=j,
        partida=partida,
    )
    assert "punta-0" in str(pieza)
    assert "Ana" in str(pieza)


@pytest.mark.django_db
def test_pieza_creacion_minima_permite_fk_nulas():
    j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    pieza = Pieza.objects.create(
        id_pieza="X_MIN",
        tipo="punta-0",
        posicion="0-0",
        jugador=j,
        partida=None,
        ia=None,
        chatbot=None,
    )
    assert pieza.jugador_id == "J1"
    assert pieza.partida_id is None
    assert pieza.ia_id is None
    assert pieza.chatbot_id is None


@pytest.mark.django_db
def test_pieza_requiere_jugador():
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Pieza.objects.create(
                id_pieza="X_NO_PLAYER",
                tipo="punta-0",
                posicion="0-0",
                jugador=None,
            )


@pytest.mark.django_db
def test_pieza_requiere_tipo_y_posicion_no_nulos():
    j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Pieza.objects.create(
                id_pieza="X_NO_TIPO",
                tipo=None,
                posicion="0-0",
                jugador=j,
            )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Pieza.objects.create(
                id_pieza="X_NO_POS",
                tipo="punta-0",
                posicion=None,
                jugador=j,
            )


@pytest.mark.django_db
def test_pieza_posicion_debe_estar_en_tablero_full_clean():
    j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    pieza = Pieza(
        id_pieza="X_BAD_POS",
        tipo="punta-0",
        posicion="99-99",
        jugador=j,
    )

    with pytest.raises(ValidationError):
        pieza.full_clean()


@pytest.mark.django_db
def test_turno_str_formato():
    j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    p = Partida.objects.create(id_partida="P1", numero_jugadores=2)
    t = Turno.objects.create(id_turno="T1", jugador=j, numero=1, partida=p)
    assert str(t) == "Turno 1 de Ana"


@pytest.mark.django_db
def test_turno_inicio_se_asigna_y_fin_es_nullable():
    j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    p = Partida.objects.create(id_partida="P1", numero_jugadores=2)
    t = Turno.objects.create(id_turno="T1", jugador=j, numero=1, partida=p)

    assert t.inicio is not None
    assert t.fin is None

    t.fin = t.inicio + timedelta(seconds=5)
    t.save(update_fields=["fin"])
    t.refresh_from_db()
    assert t.fin is not None
    assert t.fin > t.inicio


@pytest.mark.django_db
def test_turno_fin_posterior_a_inicio_forzado_por_bd():
    j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    p = Partida.objects.create(id_partida="P1", numero_jugadores=2)
    t = Turno.objects.create(id_turno="T1", jugador=j, numero=1, partida=p)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            t.fin = t.inicio - timedelta(seconds=1)
            t.save(update_fields=["fin"])


@pytest.mark.django_db
def test_turno_requiere_jugador_y_partida():
    p = Partida.objects.create(id_partida="P1", numero_jugadores=2)
    j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Turno.objects.create(id_turno="T_NO_PLAYER", jugador=None, numero=1, partida=p)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Turno.objects.create(id_turno="T_NO_PARTIDA", jugador=j, numero=1, partida=None)


@pytest.mark.django_db
def test_turno_related_name_funciona():
    j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    p = Partida.objects.create(id_partida="P1", numero_jugadores=2)
    Turno.objects.create(id_turno="T1", jugador=j, numero=1, partida=p)
    Turno.objects.create(id_turno="T2", jugador=j, numero=2, partida=p)

    assert j.turnos.count() == 2
    assert p.turnos.count() == 2


@pytest.mark.django_db
def test_movimiento_str_incluye_origen_destino_y_pieza():
    j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    p = Partida.objects.create(id_partida="P1", numero_jugadores=2)
    pieza = Pieza.objects.create(
        id_pieza="X1",
        tipo="punta-0",
        posicion="0-0",
        jugador=j,
        partida=p,
    )
    t = Turno.objects.create(id_turno="T1", jugador=j, numero=1, partida=p)
    m = Movimiento.objects.create(
        id_movimiento="M1",
        jugador=j,
        pieza=pieza,
        turno=t,
        partida=p,
        origen="0-0",
        destino="0-1",
    )

    s = str(m)
    assert "0-0" in s
    assert "0-1" in s
    assert "punta-0" in s


@pytest.mark.django_db
def test_movimiento_partida_es_nullable():
    j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    p = Partida.objects.create(id_partida="P1", numero_jugadores=2)
    pieza = Pieza.objects.create(
        id_pieza="X1",
        tipo="punta-0",
        posicion="0-0",
        jugador=j,
        partida=p,
    )
    t = Turno.objects.create(id_turno="T1", jugador=j, numero=1, partida=p)
    m = Movimiento.objects.create(
        id_movimiento="M1",
        jugador=j,
        pieza=pieza,
        turno=t,
        partida=None,
        origen="0-0",
        destino="0-1",
    )
    assert m.partida_id is None


@pytest.mark.django_db
def test_movimiento_requiere_fk_y_origen_destino_no_nulos():
    j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    p = Partida.objects.create(id_partida="P1", numero_jugadores=2)
    pieza = Pieza.objects.create(
        id_pieza="X1",
        tipo="punta-0",
        posicion="0-0",
        jugador=j,
        partida=p,
    )
    t = Turno.objects.create(id_turno="T1", jugador=j, numero=1, partida=p)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Movimiento.objects.create(
                id_movimiento="M_NO_PLAYER",
                jugador=None,
                pieza=pieza,
                turno=t,
                partida=p,
                origen="0-0",
                destino="0-1",
            )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Movimiento.objects.create(
                id_movimiento="M_NO_PIEZA",
                jugador=j,
                pieza=None,
                turno=t,
                partida=p,
                origen="0-0",
                destino="0-1",
            )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Movimiento.objects.create(
                id_movimiento="M_NO_TURNO",
                jugador=j,
                pieza=pieza,
                turno=None,
                partida=p,
                origen="0-0",
                destino="0-1",
            )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Movimiento.objects.create(
                id_movimiento="M_NO_ORIGEN",
                jugador=j,
                pieza=pieza,
                turno=t,
                partida=p,
                origen=None,
                destino="0-1",
            )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Movimiento.objects.create(
                id_movimiento="M_NO_DESTINO",
                jugador=j,
                pieza=pieza,
                turno=t,
                partida=p,
                origen="0-0",
                destino=None,
            )


@pytest.mark.django_db
def test_movimiento_related_names_funcionan():
    j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    p = Partida.objects.create(id_partida="P1", numero_jugadores=2)
    pieza = Pieza.objects.create(
        id_pieza="X1",
        tipo="punta-0",
        posicion="0-0",
        jugador=j,
        partida=p,
    )
    t = Turno.objects.create(id_turno="T1", jugador=j, numero=1, partida=p)
    Movimiento.objects.create(
        id_movimiento="M1",
        jugador=j,
        pieza=pieza,
        turno=t,
        partida=p,
        origen="0-0",
        destino="0-1",
    )

    assert j.movimientos.count() == 1
    assert pieza.movimientos.count() == 1
    assert t.movimientos.count() == 1
    assert p.movimientos.count() == 1


@pytest.mark.django_db
def test_movimiento_origen_y_destino_deben_estar_en_tablero():
    j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    p = Partida.objects.create(id_partida="P1", numero_jugadores=2)
    pieza = Pieza.objects.create(
        id_pieza="X1",
        tipo="punta-0",
        posicion="0-0",
        jugador=j,
        partida=p,
    )
    t = Turno.objects.create(id_turno="T1", jugador=j, numero=1, partida=p)

    m1 = Movimiento(
        id_movimiento="M_BAD_ORIGEN",
        jugador=j,
        pieza=pieza,
        turno=t,
        partida=p,
        origen="99-99",
        destino="0-1",
    )
    with pytest.raises(ValidationError):
        m1.full_clean()

    m2 = Movimiento(
        id_movimiento="M_BAD_DESTINO",
        jugador=j,
        pieza=pieza,
        turno=t,
        partida=p,
        origen="0-0",
        destino="99-99",
    )
    with pytest.raises(ValidationError):
        m2.full_clean()


@pytest.mark.django_db
def test_movimiento_origen_debe_coincidir_con_posicion_de_pieza():
    j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    p = Partida.objects.create(id_partida="P1", numero_jugadores=2)
    pieza = Pieza.objects.create(
        id_pieza="X1",
        tipo="punta-0",
        posicion="0-0",
        jugador=j,
        partida=p,
    )
    t = Turno.objects.create(id_turno="T1", jugador=j, numero=1, partida=p)

    m = Movimiento(
        id_movimiento="M_BAD_ORIGEN_MATCH",
        jugador=j,
        pieza=pieza,
        turno=t,
        partida=p,
        origen="0-1",
        destino="0-2",
    )
    with pytest.raises(ValidationError):
        m.full_clean()


@pytest.mark.django_db
def test_movimiento_destino_no_debe_estar_ocupado_en_misma_partida():
    j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    p = Partida.objects.create(id_partida="P1", numero_jugadores=2)
    pieza = Pieza.objects.create(
        id_pieza="X1",
        tipo="punta-0",
        posicion="0-0",
        jugador=j,
        partida=p,
    )
    Pieza.objects.create(
        id_pieza="X2",
        tipo="punta-0",
        posicion="0-1",
        jugador=j,
        partida=p,
    )
    t = Turno.objects.create(id_turno="T1", jugador=j, numero=1, partida=p)

    m = Movimiento(
        id_movimiento="M_DESTINO_OCUPADO",
        jugador=j,
        pieza=pieza,
        turno=t,
        partida=p,
        origen="0-0",
        destino="0-1",
    )
    with pytest.raises(ValidationError):
        m.full_clean()


@pytest.mark.django_db
def test_movimiento_destino_ocupado_en_otra_partida_no_debe_fallar():
    j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    p1 = Partida.objects.create(id_partida="P1", numero_jugadores=2)
    p2 = Partida.objects.create(id_partida="P2", numero_jugadores=2)

    # En la partida 2 hay una pieza ocupando 0-1
    Pieza.objects.create(
        id_pieza="X_OTHER",
        tipo="punta-0",
        posicion="0-1",
        jugador=j,
        partida=p2,
    )

    pieza_p1 = Pieza.objects.create(
        id_pieza="X1",
        tipo="punta-0",
        posicion="0-0",
        jugador=j,
        partida=p1,
    )
    t1 = Turno.objects.create(id_turno="T1", jugador=j, numero=1, partida=p1)

    m = Movimiento(
        id_movimiento="M_OK_OTRA_PARTIDA",
        jugador=j,
        pieza=pieza_p1,
        turno=t1,
        partida=p1,
        origen="0-0",
        destino="0-1",
    )
    # No debe fallar porque el destino solo está ocupado en otra partida.
    m.full_clean()