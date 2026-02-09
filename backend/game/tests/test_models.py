import pytest
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from game.models import Chatbot, IA, Jugador, JugadorPartida, Movimiento, Partida, Pieza, Turno


# ============================================================================
# 1) TESTEO NORMAL DE CADA ENTIDAD
# ============================================================================


class TestEntidadesBasico:
    @pytest.mark.django_db
    def test_jugador_str_devuelve_nombre(self):
        j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        assert str(j) == "Ana"

    @pytest.mark.django_db
    def test_partida_str_devuelve_id(self):
        p = Partida.objects.create(id_partida="P1", numero_jugadores=2)
        assert str(p) == "Partida P1"

    @pytest.mark.django_db
    def test_pieza_str_incluye_tipo_y_jugador(self):
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
    def test_turno_str_formato(self):
        j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = Partida.objects.create(id_partida="P1", numero_jugadores=2)
        t = Turno.objects.create(id_turno="T1", jugador=j, numero=1, partida=p)
        assert str(t) == "Turno 1 de Ana"

    @pytest.mark.django_db
    def test_movimiento_str_incluye_origen_destino_y_pieza(self):
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


    # ============================================================================
    # 2) TESTEO DE PROPIEDADES Y VALIDACIONES
    # ============================================================================


class TestPropiedadesYValidaciones:
    @pytest.mark.django_db
    def test_partida_numero_jugadores_entre_2_y_6_forzado_por_bd(self):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Partida.objects.create(id_partida="P_BAD_1", numero_jugadores=1)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Partida.objects.create(id_partida="P_BAD_7", numero_jugadores=7)

    @pytest.mark.django_db
    def test_partida_fecha_fin_posterior_a_fecha_inicio_forzada_por_bd(self):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Partida.objects.create(
                    id_partida="P_BAD_DATE",
                    numero_jugadores=2,
                    fecha_fin=timezone.now() - timedelta(days=1),
                )

        p = Partida.objects.create(id_partida="P_OK_DATE", numero_jugadores=2)
        p.fecha_fin = p.fecha_inicio + timedelta(seconds=1)
        p.save(update_fields=["fecha_fin"])

    @pytest.mark.django_db
    def test_pieza_creacion_minima_permite_fk_nulas(self):
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
    def test_pieza_requiere_jugador(self):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Pieza.objects.create(
                    id_pieza="X_NO_PLAYER",
                    tipo="punta-0",
                    posicion="0-0",
                    jugador=None,
                )

    @pytest.mark.django_db
    def test_pieza_requiere_tipo_y_posicion_no_nulos(self):
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
    def test_pieza_posicion_debe_estar_en_tablero_full_clean(self):
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
    def test_turno_inicio_se_asigna_y_fin_es_nullable(self):
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
    def test_turno_fin_posterior_a_inicio_forzado_por_bd(self):
        j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = Partida.objects.create(id_partida="P1", numero_jugadores=2)
        t = Turno.objects.create(id_turno="T1", jugador=j, numero=1, partida=p)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                t.fin = t.inicio - timedelta(seconds=1)
                t.save(update_fields=["fin"])

    @pytest.mark.django_db
    def test_turno_requiere_jugador_y_partida(self):
        p = Partida.objects.create(id_partida="P1", numero_jugadores=2)
        j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Turno.objects.create(id_turno="T_NO_PLAYER", jugador=None, numero=1, partida=p)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Turno.objects.create(id_turno="T_NO_PARTIDA", jugador=j, numero=1, partida=None)

    @pytest.mark.django_db
    def test_movimiento_partida_es_nullable(self):
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
    def test_movimiento_requiere_fk_y_origen_destino_no_nulos(self):
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
    def test_movimiento_origen_y_destino_deben_estar_en_tablero(self):
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
    def test_movimiento_origen_debe_coincidir_con_posicion_de_pieza(self):
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
    def test_movimiento_destino_no_debe_estar_ocupado_en_misma_partida(self):
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
    def test_movimiento_destino_ocupado_en_otra_partida_no_debe_fallar(self):
        j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p1 = Partida.objects.create(id_partida="P1", numero_jugadores=2)
        p2 = Partida.objects.create(id_partida="P2", numero_jugadores=2)

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
        m.full_clean()

    @pytest.mark.django_db
    def test_ia_nivel_solo_puede_ser_1_o_2_full_clean(self):
        j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=False, numero=1)

        ia_bad_0 = IA(jugador=j, nivel=0)
        with pytest.raises(ValidationError):
            ia_bad_0.full_clean()

        ia_bad_3 = IA(jugador=j, nivel=3)
        with pytest.raises(ValidationError):
            ia_bad_3.full_clean()

        ia_ok_1 = IA(jugador=j, nivel=1)
        ia_ok_1.full_clean()

    @pytest.mark.django_db
    def test_ia_nivel_solo_puede_ser_1_o_2_forzado_por_bd(self):
        j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=False, numero=1)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                IA.objects.create(jugador=j, nivel=3)


    # ============================================================================
    # 3) TESTEO DE RELACIONES ENTRE ENTIDADES
    # ============================================================================


class TestRelacionesEntreEntidades:
    @pytest.mark.django_db
    def test_jugador_partida_no_permite_duplicados_misma_partida(self):
        j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = Partida.objects.create(id_partida="P1", numero_jugadores=2)

        JugadorPartida.objects.create(jugador=j, partida=p, orden_participacion=1)

        with pytest.raises(IntegrityError):
            JugadorPartida.objects.create(jugador=j, partida=p, orden_participacion=2)

    @pytest.mark.django_db
    def test_jugador_partida_creacion_y_conteo(self):
        j1 = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        j2 = Jugador.objects.create(id_jugador="J2", nombre="Pedro", humano=True, numero=2)
        p = Partida.objects.create(id_partida="P1", numero_jugadores=2)

        JugadorPartida.objects.create(jugador=j1, partida=p, orden_participacion=1)
        JugadorPartida.objects.create(jugador=j2, partida=p, orden_participacion=2)

        assert JugadorPartida.objects.filter(partida=p).count() == 2

    @pytest.mark.django_db
    def test_turno_related_name_funciona(self):
        j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = Partida.objects.create(id_partida="P1", numero_jugadores=2)
        Turno.objects.create(id_turno="T1", jugador=j, numero=1, partida=p)
        Turno.objects.create(id_turno="T2", jugador=j, numero=2, partida=p)

        assert j.turnos.count() == 2
        assert p.turnos.count() == 2

    @pytest.mark.django_db
    def test_movimiento_related_names_funcionan(self):
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
    def test_m2m_partida_jugadores_y_jugador_partidas_via_through(self):
        j1 = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        j2 = Jugador.objects.create(id_jugador="J2", nombre="Pedro", humano=True, numero=2)
        p = Partida.objects.create(id_partida="P1", numero_jugadores=2)

        JugadorPartida.objects.create(jugador=j1, partida=p, orden_participacion=1)
        JugadorPartida.objects.create(jugador=j2, partida=p, orden_participacion=2)

        assert set(p.jugadores.all()) == {j1, j2}
        assert list(j1.partidas.all()) == [p]
        assert list(j2.partidas.all()) == [p]

    @pytest.mark.django_db
    def test_related_name_piezas_desde_jugador_funciona(self):
        j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = Partida.objects.create(id_partida="P1", numero_jugadores=2)

        Pieza.objects.create(id_pieza="X1", tipo="punta-0", posicion="0-0", jugador=j, partida=p)
        Pieza.objects.create(id_pieza="X2", tipo="punta-0", posicion="0-1", jugador=j, partida=None)

        assert j.piezas.count() == 2
        assert p.piezas.count() == 1

    @pytest.mark.django_db
    def test_one_to_one_jugador_ia_se_accede_y_pk_coincide(self):
        j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=False, numero=1)
        ia = IA.objects.create(jugador=j, nivel=3)

        assert j.ia == ia
        assert ia.pk == j.pk

    @pytest.mark.django_db
    def test_one_to_one_chatbot_desde_ia_y_chatbot_puede_ser_null(self):
        j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=False, numero=1)
        ia = IA.objects.create(jugador=j, nivel=1)

        chatbot = Chatbot.objects.create(ia=ia, memoria={"a": 1}, contexto={"b": 2})
        assert ia.chatbot == chatbot

        chatbot_sin_ia = Chatbot.objects.create(ia=None, memoria={}, contexto={})
        assert chatbot_sin_ia.ia is None

    @pytest.mark.django_db
    def test_related_name_piezas_desde_ia_y_chatbot_funciona(self):
        j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=False, numero=1)
        ia = IA.objects.create(jugador=j, nivel=2)
        chatbot = Chatbot.objects.create(ia=ia, memoria={}, contexto={})
        p = Partida.objects.create(id_partida="P1", numero_jugadores=2)

        Pieza.objects.create(
            id_pieza="X_IA",
            tipo="punta-0",
            posicion="0-0",
            jugador=j,
            partida=p,
            ia=ia,
            chatbot=None,
        )
        Pieza.objects.create(
            id_pieza="X_CB",
            tipo="punta-0",
            posicion="0-1",
            jugador=j,
            partida=p,
            ia=None,
            chatbot=chatbot,
        )

        assert ia.piezas.count() == 1
        assert chatbot.piezas.count() == 1

    @pytest.mark.django_db
    def test_borrado_partida_hace_cascade_a_turnos_movimientos_piezas_y_through(self):
        j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = Partida.objects.create(id_partida="P1", numero_jugadores=2)
        JugadorPartida.objects.create(jugador=j, partida=p, orden_participacion=1)

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

        assert Turno.objects.filter(partida=p).count() == 1
        assert Pieza.objects.filter(partida=p).count() == 1
        assert Movimiento.objects.filter(partida=p).count() == 1
        assert JugadorPartida.objects.filter(partida=p).count() == 1

        p.delete()

        assert Turno.objects.filter(id_turno="T1").count() == 0
        assert Pieza.objects.filter(id_pieza="X1").count() == 0
        assert Movimiento.objects.filter(id_movimiento="M1").count() == 0
        assert JugadorPartida.objects.filter(jugador=j).count() == 0

    @pytest.mark.django_db
    def test_borrado_jugador_hace_cascade_a_ia_chatbot_y_dependencias(self):
        j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=False, numero=1)
        ia = IA.objects.create(jugador=j, nivel=2)
        Chatbot.objects.create(ia=ia, memoria={}, contexto={})
        p = Partida.objects.create(id_partida="P1", numero_jugadores=2)
        JugadorPartida.objects.create(jugador=j, partida=p, orden_participacion=1)

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

        j.delete()

        assert IA.objects.filter(pk="J1").count() == 0
        assert Chatbot.objects.count() == 0
        assert Pieza.objects.count() == 0
        assert Turno.objects.count() == 0
        assert Movimiento.objects.count() == 0
        assert JugadorPartida.objects.count() == 0

    @pytest.mark.django_db
    def test_borrado_ia_hace_cascade_a_chatbot_y_piezas_asociadas(self):
        j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=False, numero=1)
        ia = IA.objects.create(jugador=j, nivel=2)
        Chatbot.objects.create(ia=ia, memoria={}, contexto={})

        pieza_ia = Pieza.objects.create(
            id_pieza="X_IA",
            tipo="punta-0",
            posicion="0-0",
            jugador=j,
            ia=ia,
            partida=None,
        )
        pieza_sin_ia = Pieza.objects.create(
            id_pieza="X_NO_IA",
            tipo="punta-0",
            posicion="0-1",
            jugador=j,
            ia=None,
            partida=None,
        )

        ia.delete()

        assert Chatbot.objects.count() == 0
        assert Pieza.objects.filter(id_pieza=pieza_ia.id_pieza).count() == 0
        assert Pieza.objects.filter(id_pieza=pieza_sin_ia.id_pieza).count() == 1

    @pytest.mark.django_db
    def test_borrado_chatbot_hace_cascade_a_piezas_asociadas(self):
        j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        ia = IA.objects.create(jugador=j, nivel=2)
        chatbot = Chatbot.objects.create(ia=ia, memoria={}, contexto={})

        pieza_cb = Pieza.objects.create(
            id_pieza="X_CB",
            tipo="punta-0",
            posicion="0-0",
            jugador=j,
            chatbot=chatbot,
            partida=None,
        )
        pieza_sin_cb = Pieza.objects.create(
            id_pieza="X_NO_CB",
            tipo="punta-0",
            posicion="0-1",
            jugador=j,
            chatbot=None,
            partida=None,
        )

        chatbot.delete()

        assert Pieza.objects.filter(id_pieza=pieza_cb.id_pieza).count() == 0
        assert Pieza.objects.filter(id_pieza=pieza_sin_cb.id_pieza).count() == 1
