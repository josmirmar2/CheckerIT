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
    def test_jugador_str_devuelve_nombre(self, make_jugador):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        assert str(j) == "Ana"

    @pytest.mark.django_db
    def test_partida_str_devuelve_id(self, make_partida):
        p = make_partida(id_partida="P1", numero_jugadores=2)
        assert str(p) == "Partida P1"

    @pytest.mark.django_db
    def test_pieza_str_incluye_tipo_y_jugador(self, make_jugador, make_partida, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        partida = make_partida(id_partida="P1", numero_jugadores=2)
        pieza = make_pieza(id_pieza="X1", tipo="punta-0", posicion="0-0", jugador=j, partida=partida)
        assert "punta-0" in str(pieza)
        assert "Ana" in str(pieza)

    @pytest.mark.django_db
    def test_turno_str_formato(self, make_jugador, make_partida, make_turno):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        t = make_turno(id_turno="T1", jugador=j, numero=1, partida=p)
        assert str(t) == "Turno 1 de Ana"

    @pytest.mark.django_db
    def test_movimiento_str_incluye_origen_destino_y_pieza(self, make_partida, make_jugador, make_movimiento):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        m = make_movimiento(
            id_movimiento="M1",
            jugador=j,
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
    def test_partida_numero_jugadores_entre_2_y_6_forzado_por_bd(self, make_partida):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                make_partida(id_partida="P_BAD_1", numero_jugadores=1)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                make_partida(id_partida="P_BAD_7", numero_jugadores=7)

    @pytest.mark.django_db
    def test_partida_fecha_fin_posterior_a_fecha_inicio_forzada_por_bd(self, make_partida):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                make_partida(
                    id_partida="P_BAD_DATE",
                    numero_jugadores=2,
                    fecha_fin=timezone.now() - timedelta(days=1),
                )

        p = make_partida(id_partida="P_OK_DATE", numero_jugadores=2)
        p.fecha_fin = p.fecha_inicio + timedelta(seconds=1)
        p.save(update_fields=["fecha_fin"])

    @pytest.mark.django_db
    def test_pieza_creacion_minima_permite_fk_nulas(self, make_jugador, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        pieza = make_pieza(
            id_pieza="X_MIN",
            tipo="punta-0",
            posicion="0-0",
            jugador=j,
        )
        assert pieza.jugador_id == "J1"
        assert pieza.partida_id is None
        assert pieza.ia_id is None
        assert pieza.chatbot_id is None

    @pytest.mark.django_db
    def test_pieza_requiere_jugador(self, make_pieza):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                make_pieza(
                    id_pieza="X_NO_PLAYER",
                    tipo="punta-0",
                    posicion="0-0",
                    jugador=None,
                )

    @pytest.mark.django_db
    def test_pieza_requiere_tipo_y_posicion_no_nulos(self, make_jugador, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                make_pieza(
                    id_pieza="X_NO_TIPO",
                    tipo=None,
                    posicion="0-0",
                    jugador=j,
                )

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                make_pieza(
                    id_pieza="X_NO_POS",
                    tipo="punta-0",
                    posicion=None,
                    jugador=j,
                )

    @pytest.mark.django_db
    def test_pieza_posicion_debe_estar_en_tablero_full_clean(self, make_jugador, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        pieza = make_pieza(
            id_pieza="X_BAD_POS",
            tipo="punta-0",
            posicion="99-99",
            jugador=j,
        )

        with pytest.raises(ValidationError):
            pieza.full_clean()

    @pytest.mark.django_db
    def test_turno_inicio_se_asigna_y_fin_es_nullable(self, make_jugador, make_partida, make_turno):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        t = make_turno(id_turno="T1", jugador=j, numero=1, partida=p)

        assert t.inicio is not None
        assert t.fin is None

        t.fin = t.inicio + timedelta(seconds=5)
        t.save(update_fields=["fin"])
        t.refresh_from_db()
        assert t.fin is not None
        assert t.fin > t.inicio

    @pytest.mark.django_db
    def test_turno_fin_posterior_a_inicio_forzado_por_bd(self, make_jugador, make_partida, make_turno):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        t = make_turno(id_turno="T1", jugador=j, numero=1, partida=p)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                t.fin = t.inicio - timedelta(seconds=1)
                t.save(update_fields=["fin"])

    @pytest.mark.django_db
    def test_turno_requiere_jugador_y_partida(self, make_jugador, make_partida, make_turno):
        p = make_partida(id_partida="P1", numero_jugadores=2)
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                make_turno(id_turno="T_NO_PLAYER", partida=p, numero=1)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                make_turno(id_turno="T_NO_PARTIDA", jugador=j, numero=1)

    @pytest.mark.django_db
    def test_movimiento_campos_obligatorios(self, make_jugador, make_partida, make_pieza, make_turno):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        pieza = make_pieza(id_pieza="X1", tipo="punta-0", posicion="0-0", jugador=j, partida=p)
        t = make_turno(id_turno="T1", jugador=j, numero=1, partida=p)

        base = {
            "jugador": j,
            "pieza": pieza,
            "turno": t,
            "partida": p,
            "origen": "0-0",
            "destino": "0-1",
        }

        cases = [
            ("jugador", IntegrityError),
            ("pieza", IntegrityError),
            ("turno", IntegrityError),
            ("origen", IntegrityError),
            ("destino", IntegrityError),
            ("partida", IntegrityError),
        ]

        for field_name, expected_exc in cases:
            kwargs = dict(base)
            kwargs[field_name] = None

            if expected_exc is None:
                m = Movimiento.objects.create(
                    id_movimiento=f"M_NULL_{field_name.upper()}",
                    **kwargs,
                )
                assert m.partida_id is None
            else:
                with pytest.raises(expected_exc):
                    with transaction.atomic():
                        Movimiento.objects.create(
                            id_movimiento=f"M_NO_{field_name.upper()}",
                            **kwargs,
                        )

    @pytest.mark.django_db
    def test_movimiento_origen_y_destino_deben_estar_en_tablero(self, make_jugador, make_partida, make_pieza, make_turno, make_movimiento):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        pieza = make_pieza(id_pieza="X1", tipo="punta-0", posicion="0-0", jugador=j, partida=p)
        t = make_turno(id_turno="T1", jugador=j, numero=1, partida=p)

        m1 = make_movimiento(
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

        m2 = make_movimiento(
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
    def test_movimiento_origen_debe_coincidir_con_posicion_de_pieza(self, make_jugador, make_partida, make_pieza, make_turno, make_movimiento):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        pieza = make_pieza(id_pieza="X1", tipo="punta-0", posicion="0-0", jugador=j, partida=p)
        t = make_turno(id_turno="T1", jugador=j, numero=1, partida=p)
        
        m = make_movimiento(
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
    def test_movimiento_destino_no_debe_estar_ocupado_en_misma_partida(self, make_jugador, make_partida, make_pieza, make_turno, make_movimiento):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        pieza = make_pieza(id_pieza="X1", tipo="punta-0", posicion="0-0", jugador=j, partida=p)
        t = make_turno(id_turno="T1", jugador=j, numero=1, partida=p)

        make_pieza( id_pieza="X2", tipo="punta-0", posicion="0-1", jugador=j, partida=p)

        m = make_movimiento(
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
    def test_movimiento_destino_ocupado_en_otra_partida_no_debe_fallar(self, make_jugador, make_partida, make_pieza, make_turno, make_movimiento):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p1 = make_partida(id_partida="P1", numero_jugadores=2)
        p2 = make_partida(id_partida="P2", numero_jugadores=2)

        make_pieza(id_pieza="X_OTHER", tipo="punta-0", posicion="0-1", jugador=j, partida=p2)

        pieza_p1 = make_pieza(id_pieza="X1", tipo="punta-0", posicion="0-0", jugador=j, partida=p1)
        t1 = make_turno(id_turno="T1", jugador=j, numero=1, partida=p1)

        m = make_movimiento(
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
    def test_ia_nivel_solo_puede_ser_1_o_2_full_clean(self, make_jugador):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=False, numero=1)

        ia_bad_0 = IA(jugador=j, nivel=0)
        with pytest.raises(ValidationError):
            ia_bad_0.full_clean()

        ia_bad_3 = IA(jugador=j, nivel=3)
        with pytest.raises(ValidationError):
            ia_bad_3.full_clean()

        ia_ok_1 = IA(jugador=j, nivel=1)
        ia_ok_1.full_clean()

        ia_ok_2 = IA(jugador=j, nivel=2)
        ia_ok_2.full_clean()

    @pytest.mark.django_db
    def test_ia_nivel_solo_puede_ser_1_o_2_forzado_por_bd(self, make_jugador, make_ia):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=False, numero=1)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                make_ia(jugador=j, nivel=3)

    @pytest.mark.django_db
    def test_jugador_partida_orden_participacion_debe_ser_entre_1_y_6_full_clean(self, make_jugador, make_partida):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        jp = JugadorPartida(jugador=j, partida=p, orden_participacion=0)

        with pytest.raises(ValidationError):
            jp.full_clean()


# ============================================================================
# 3) TESTEO DE RELACIONES ENTRE ENTIDADES
# ============================================================================


class TestRelacionesEntreEntidades:
    @pytest.mark.django_db
    def test_jugador_partida_no_permite_duplicados_misma_partida(self, make_jugador, make_partida):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)

        JugadorPartida.objects.create(jugador=j, partida=p, orden_participacion=1)

        with pytest.raises(IntegrityError):
            JugadorPartida.objects.create(jugador=j, partida=p, orden_participacion=2)

    @pytest.mark.django_db
    def test_jugador_partida_creacion_y_conteo(self, make_jugador, make_partida):
        j1 = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        j2 = make_jugador(id_jugador="J2", nombre="Pedro", humano=True, numero=2)
        p = make_partida(id_partida="P1", numero_jugadores=2)

        JugadorPartida.objects.create(jugador=j1, partida=p, orden_participacion=1)
        JugadorPartida.objects.create(jugador=j2, partida=p, orden_participacion=2)

        assert JugadorPartida.objects.filter(partida=p).count() == 2

    @pytest.mark.django_db
    def test_jugador_partida_no_permite_orden_participacion_duplicado_en_partida(self, make_jugador, make_partida):
        j1 = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        j2 = make_jugador(id_jugador="J2", nombre="Pedro", humano=True, numero=2)
        p = make_partida(id_partida="P1", numero_jugadores=2)

        JugadorPartida.objects.create(jugador=j1, partida=p, orden_participacion=1)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                JugadorPartida.objects.create(jugador=j2, partida=p, orden_participacion=1)

    @pytest.mark.django_db
    def test_turno_related_name_funciona(self, make_jugador, make_partida, make_turno):
        p = make_partida(id_partida="P1", numero_jugadores=2)
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        make_turno(id_turno="T1", jugador=j, numero=1, partida=p)
        make_turno(id_turno="T2", jugador=j, numero=2, partida=p)

        assert j.turnos.count() == 2
        assert p.turnos.count() == 2

    @pytest.mark.django_db
    def test_movimiento_related_names_funcionan(self, make_jugador, make_partida, make_pieza, make_turno, make_movimiento):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        pieza = make_pieza(id_pieza="X1", tipo="punta-0", posicion="0-0", jugador=j, partida=p)
        t = make_turno(id_turno="T1", jugador=j, numero=1, partida=p)
        
        make_movimiento(
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
    def test_m2m_partida_jugadores_y_jugador_partidas_via_through(self, make_jugador, make_partida):
        j1 = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        j2 = make_jugador(id_jugador="J2", nombre="Pedro", humano=True, numero=2)
        p = make_partida(id_partida="P1", numero_jugadores=2)

        JugadorPartida.objects.create(jugador=j1, partida=p, orden_participacion=1)
        JugadorPartida.objects.create(jugador=j2, partida=p, orden_participacion=2)

        assert set(p.jugadores.all()) == {j1, j2}
        assert list(j1.partidas.all()) == [p]
        assert list(j2.partidas.all()) == [p]

    @pytest.mark.django_db
    def test_related_name_piezas_desde_jugador_funciona(self, make_jugador, make_partida, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)

        make_pieza(id_pieza="X1", tipo="punta-0", posicion="0-0", jugador=j, partida=p)
        make_pieza(id_pieza="X2", tipo="punta-0", posicion="0-1", jugador=j)

        assert j.piezas.count() == 2
        assert p.piezas.count() == 1

    @pytest.mark.django_db
    def test_one_to_one_jugador_ia_se_accede_y_pk_coincide(self, make_jugador, make_ia):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=False, numero=1)
        ia = make_ia(jugador=j, nivel=2)

        assert j.ia == ia
        assert ia.pk == j.pk

    @pytest.mark.django_db
    def test_one_to_one_chatbot_desde_ia_y_chatbot_puede_ser_null(self, make_jugador, make_ia):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=False, numero=1)
        ia = make_ia(jugador=j, nivel=1)

        chatbot = Chatbot.objects.create(ia=ia, memoria={"a": 1}, contexto={"b": 2})
        assert ia.chatbot == chatbot

        chatbot_sin_ia = Chatbot.objects.create(memoria={}, contexto={})
        assert chatbot_sin_ia.ia is None

    @pytest.mark.django_db
    def test_related_name_piezas_desde_ia_y_chatbot_funciona(self, make_jugador, make_ia, make_partida, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=False, numero=1)
        ia = make_ia(jugador=j, nivel=2)
        chatbot = Chatbot.objects.create(ia=ia, memoria={}, contexto={})
        p = make_partida(id_partida="P1", numero_jugadores=2)

        make_pieza(
            id_pieza="X_IA",
            tipo="punta-0",
            posicion="0-0",
            jugador=j,
            partida=p,
            ia=ia,
        )
        make_pieza(
            id_pieza="X_CB",
            tipo="punta-0",
            posicion="0-1",
            jugador=j,
            partida=p,
            chatbot=chatbot,
        )

        assert ia.piezas.count() == 1
        assert chatbot.piezas.count() == 1

    @pytest.mark.django_db
    def test_borrado_partida_hace_cascade_a_turnos_movimientos_piezas_y_through(self, make_jugador, make_partida, make_pieza, make_turno, make_movimiento):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        JugadorPartida.objects.create(jugador=j, partida=p, orden_participacion=1)

        pieza = make_pieza(
            id_pieza="X1",
            tipo="punta-0",
            posicion="0-0",
            jugador=j,
            partida=p,
        )
        t = make_turno(id_turno="T1", jugador=j, numero=1, partida=p)
        make_movimiento(
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
    def test_borrado_jugador_hace_cascade_a_ia_chatbot_y_dependencias(self, make_jugador, make_ia, make_partida, make_pieza, make_turno, make_movimiento):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=False, numero=1)
        ia = make_ia(jugador=j, nivel=2)
        Chatbot.objects.create(ia=ia, memoria={}, contexto={})
        p = make_partida(id_partida="P1", numero_jugadores=2)
        JugadorPartida.objects.create(jugador=j, partida=p, orden_participacion=1)

        pieza = make_pieza(
            id_pieza="X1",
            tipo="punta-0",
            posicion="0-0",
            jugador=j,
            partida=p,
        )
        t = make_turno(id_turno="T1", jugador=j, numero=1, partida=p)
        make_movimiento(
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
    def test_borrado_ia_hace_cascade_a_chatbot_y_piezas_asociadas(self, make_jugador, make_ia, make_partida, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=False, numero=1)
        ia = make_ia(jugador=j, nivel=2)
        Chatbot.objects.create(ia=ia, memoria={}, contexto={})

        pieza_ia = make_pieza(
            id_pieza="X_IA",
            tipo="punta-0",
            posicion="0-0",
            jugador=j,
            ia=ia,
        )
        pieza_sin_ia = make_pieza(
            id_pieza="X_NO_IA",
            tipo="punta-0",
            posicion="0-1",
            jugador=j,
        )

        ia.delete()

        assert Chatbot.objects.count() == 0
        assert Pieza.objects.filter(id_pieza=pieza_ia.id_pieza).count() == 0
        assert Pieza.objects.filter(id_pieza=pieza_sin_ia.id_pieza).count() == 1

    @pytest.mark.django_db
    def test_borrado_chatbot_hace_cascade_a_piezas_asociadas(self, make_ia, make_jugador, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        ia = make_ia(jugador=j, nivel=2)
        chatbot = Chatbot.objects.create(ia=ia, memoria={}, contexto={})

        pieza_cb = make_pieza(
            id_pieza="X_CB",
            tipo="punta-0",
            posicion="0-0",
            jugador=j,
            chatbot=chatbot,
        )
        pieza_sin_cb = make_pieza(
            id_pieza="X_NO_CB",
            tipo="punta-0",
            posicion="0-1",
            jugador=j,
        )

        chatbot.delete()

        assert Pieza.objects.filter(id_pieza=pieza_cb.id_pieza).count() == 0
        assert Pieza.objects.filter(id_pieza=pieza_sin_cb.id_pieza).count() == 1
