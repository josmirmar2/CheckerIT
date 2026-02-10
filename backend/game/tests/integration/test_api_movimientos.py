import pytest

from game.models import Movimiento, Pieza, Turno


@pytest.mark.django_db
class TestMovimientosAPI:
    def test_post_movimientos_crea_movimiento_ok(self, api_client, make_jugador, make_partida, make_turno, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        t = make_turno(id_turno="T1", jugador=j, numero=1, partida=p)
        pieza = make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")

        payload = {
            "id_movimiento": "M1",
            "jugador": j.id_jugador,
            "pieza": pieza.id_pieza,
            "turno": t.id_turno,
            "partida": p.id_partida,
            "origen": "0-4",
            "destino": "1-4",
        }

        res = api_client.post("/api/movimientos/", payload, format="json")
        assert res.status_code == 201
        assert Movimiento.objects.count() == 1

    def test_post_movimientos_falla_si_falta_partida(self, api_client, make_jugador, make_partida, make_turno, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        t = make_turno(id_turno="T1", jugador=j, numero=1, partida=p)
        pieza = make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")

        payload = {
            "id_movimiento": "M1",
            "jugador": j.id_jugador,
            "pieza": pieza.id_pieza,
            "turno": t.id_turno,
            "origen": "0-4",
            "destino": "1-4",
        }

        res = api_client.post("/api/movimientos/", payload, format="json")
        assert res.status_code == 400
        assert "partida" in res.data

    def test_post_movimientos_falla_origen_no_coincide_con_pieza(self, api_client, make_jugador, make_partida, make_turno, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        t = make_turno(id_turno="T1", jugador=j, numero=1, partida=p)
        pieza = make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")

        payload = {
            "id_movimiento": "M1",
            "jugador": j.id_jugador,
            "pieza": pieza.id_pieza,
            "turno": t.id_turno,
            "partida": p.id_partida,
            "origen": "2-4",
            "destino": "1-4",
        }

        res = api_client.post("/api/movimientos/", payload, format="json")
        assert res.status_code == 400
        assert "origen" in res.data

    def test_post_movimientos_falla_destino_ocupado_misma_partida(self, api_client, make_jugador, make_partida, make_turno, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        t = make_turno(id_turno="T1", jugador=j, numero=1, partida=p)
        pieza = make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")
        make_pieza(id_pieza="X2", jugador=j, partida=p, posicion="1-4")

        payload = {
            "id_movimiento": "M1",
            "jugador": j.id_jugador,
            "pieza": pieza.id_pieza,
            "turno": t.id_turno,
            "partida": p.id_partida,
            "origen": "0-4",
            "destino": "1-4",
        }

        res = api_client.post("/api/movimientos/", payload, format="json")
        assert res.status_code == 400
        assert "destino" in res.data


@pytest.mark.django_db
class TestRegistrarMovimientos:
    def test_registrar_movimientos_requiere_lista_no_vacia(self, api_client, make_partida):
        p = make_partida(id_partida="P1", numero_jugadores=2)

        res1 = api_client.post(f"/api/partidas/{p.id_partida}/registrar_movimientos/", {}, format="json")
        assert res1.status_code == 400

        res2 = api_client.post(
            f"/api/partidas/{p.id_partida}/registrar_movimientos/",
            {"movimientos": "no_es_lista"},
            format="json",
        )
        assert res2.status_code == 400

        res3 = api_client.post(
            f"/api/partidas/{p.id_partida}/registrar_movimientos/",
            {"movimientos": []},
            format="json",
        )
        assert res3.status_code == 400

    def test_registrar_movimientos_falla_sin_turno_activo(self, api_client, make_jugador, make_partida):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)

        payload = {
            "movimientos": [
                {
                    "jugador_id": j.id_jugador,
                    "turno_id": "T1",
                    "partida_id": p.id_partida,
                    "pieza_id": "X1",
                    "origen": "0-4",
                    "destino": "1-4",
                }
            ]
        }
        res = api_client.post(f"/api/partidas/{p.id_partida}/registrar_movimientos/", payload, format="json")
        assert res.status_code == 400
        assert "turno" in str(res.data).lower() or "No hay turno activo" in str(res.data)

    def test_registrar_movimientos_falla_por_partida_id_mismatch(self, api_client, make_jugador, make_partida, make_turno, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        t = make_turno(id_turno="T1", jugador=j, numero=1, partida=p)
        make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")

        payload = {
            "movimientos": [
                {
                    "jugador_id": j.id_jugador,
                    "turno_id": t.id_turno,
                    "partida_id": "P999",
                    "pieza_id": "X1",
                    "origen": "0-4",
                    "destino": "1-4",
                }
            ]
        }
        res = api_client.post(f"/api/partidas/{p.id_partida}/registrar_movimientos/", payload, format="json")
        assert res.status_code == 400

    def test_registrar_movimientos_falla_si_mueve_varias_piezas(self, api_client, make_jugador, make_partida, make_turno, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        t = make_turno(id_turno="T1", jugador=j, numero=1, partida=p)
        make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")
        make_pieza(id_pieza="X2", jugador=j, partida=p, posicion="3-4")

        payload = {
            "movimientos": [
                {
                    "jugador_id": j.id_jugador,
                    "turno_id": t.id_turno,
                    "partida_id": p.id_partida,
                    "pieza_id": "X1",
                    "origen": "0-4",
                    "destino": "1-4",
                },
                {
                    "jugador_id": j.id_jugador,
                    "turno_id": t.id_turno,
                    "partida_id": p.id_partida,
                    "pieza_id": "X2",
                    "origen": "3-4",
                    "destino": "4-4",
                },
            ]
        }
        res = api_client.post(f"/api/partidas/{p.id_partida}/registrar_movimientos/", payload, format="json")
        assert res.status_code == 400

    def test_registrar_movimientos_falla_cadena_no_permite_simples(self, api_client, make_jugador, make_partida, make_turno, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        t = make_turno(id_turno="T1", jugador=j, numero=1, partida=p)
        make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")

        payload = {
            "movimientos": [
                {
                    "jugador_id": j.id_jugador,
                    "turno_id": t.id_turno,
                    "partida_id": p.id_partida,
                    "pieza_id": "X1",
                    "origen": "0-4",
                    "destino": "1-4",
                },
                {
                    "jugador_id": j.id_jugador,
                    "turno_id": t.id_turno,
                    "partida_id": p.id_partida,
                    "pieza_id": "X1",
                    "origen": "1-4",
                    "destino": "2-4",
                },
            ]
        }

        res = api_client.post(f"/api/partidas/{p.id_partida}/registrar_movimientos/", payload, format="json")
        assert res.status_code == 400

    def test_registrar_movimientos_ok_salto_en_cadena_actualiza_pieza_y_crea_movimientos(
        self, api_client, make_jugador, make_partida, make_turno, make_pieza
    ):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        t = make_turno(id_turno="T1", jugador=j, numero=1, partida=p)

        # Pieza a mover
        pieza = make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")

        # Piezas intermedias para permitir saltos: 0-4 -> 2-4 (sobre 1-4) -> 4-4 (sobre 3-4)
        make_pieza(id_pieza="B1", jugador=j, partida=p, posicion="1-4")
        make_pieza(id_pieza="B2", jugador=j, partida=p, posicion="3-4")

        payload = {
            "movimientos": [
                {
                    "jugador_id": j.id_jugador,
                    "turno_id": t.id_turno,
                    "partida_id": p.id_partida,
                    "pieza_id": pieza.id_pieza,
                    "origen": "0-4",
                    "destino": "2-4",
                },
                {
                    "jugador_id": j.id_jugador,
                    "turno_id": t.id_turno,
                    "partida_id": p.id_partida,
                    "pieza_id": pieza.id_pieza,
                    "origen": "2-4",
                    "destino": "4-4",
                },
            ]
        }

        res = api_client.post(f"/api/partidas/{p.id_partida}/registrar_movimientos/", payload, format="json")
        assert res.status_code == 201
        assert Movimiento.objects.filter(partida=p).count() == 2

        pieza.refresh_from_db()
        assert pieza.posicion == "4-4"

    def test_registrar_movimientos_falla_si_turno_finalizado(self, api_client, make_jugador, make_partida, make_turno, make_pieza):
        from django.utils import timezone
        from datetime import timedelta

        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        t = make_turno(id_turno="T1", jugador=j, numero=1, partida=p, fin=timezone.now() + timedelta(seconds=5))
        make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")

        payload = {
            "movimientos": [
                {
                    "jugador_id": j.id_jugador,
                    "turno_id": t.id_turno,
                    "partida_id": p.id_partida,
                    "pieza_id": "X1",
                    "origen": "0-4",
                    "destino": "1-4",
                }
            ]
        }
        res = api_client.post(f"/api/partidas/{p.id_partida}/registrar_movimientos/", payload, format="json")
        assert res.status_code == 400

    def test_registrar_movimientos_falla_si_pieza_no_pertenece_jugador(self, api_client, make_jugador, make_partida, make_turno, make_pieza):
        j1 = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        j2 = make_jugador(id_jugador="J2", nombre="Beto", humano=True, numero=2)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        t = make_turno(id_turno="T1", jugador=j1, numero=1, partida=p)
        make_pieza(id_pieza="X1", jugador=j2, partida=p, posicion="0-4")

        payload = {
            "movimientos": [
                {
                    "jugador_id": j1.id_jugador,
                    "turno_id": t.id_turno,
                    "partida_id": p.id_partida,
                    "pieza_id": "X1",
                    "origen": "0-4",
                    "destino": "1-4",
                }
            ]
        }

        res = api_client.post(f"/api/partidas/{p.id_partida}/registrar_movimientos/", payload, format="json")
        assert res.status_code == 400


@pytest.mark.django_db
class TestMovimientosQueryParams:
    def test_list_movimientos_filtra_por_turno_id(self, api_client, make_jugador, make_partida, make_turno, make_pieza, make_movimiento):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)

        t1 = make_turno(id_turno="T1", jugador=j, numero=1, partida=p)
        t2 = make_turno(id_turno="T2", jugador=j, numero=2, partida=p)
        pieza = make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")

        make_movimiento(id_movimiento="M1", jugador=j, pieza=pieza, turno=t1, partida=p, origen="0-4", destino="1-4")
        make_movimiento(id_movimiento="M2", jugador=j, pieza=pieza, turno=t2, partida=p, origen="0-4", destino="1-4")

        res = api_client.get(f"/api/movimientos/?turno_id={t1.id_turno}")
        assert res.status_code == 200
        assert len(res.data) == 1
        assert res.data[0]["turno"] == t1.id_turno
