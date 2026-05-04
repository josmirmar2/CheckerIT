import pytest

from game.models import Movimiento, Pieza, Ronda


@pytest.mark.django_db
class TestMovimientosAPI:
    def test_post_movimientos_crea_movimiento_ok(self, api_client, make_jugador, make_partida, make_ronda, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        r = make_ronda(id_ronda="R1", jugador=j, numero=1, partida=p)
        pieza = make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")

        payload = {
            "id_movimiento": "M1",
            "jugador": j.id_jugador,
            "pieza": pieza.id_pieza,
            "ronda": r.id_ronda,
            "partida": p.id_partida,
            "origen": "0-4",
            "destino": "1-4",
        }

        res = api_client.post("/api/movimientos/", payload, format="json")
        assert res.status_code == 201
        assert Movimiento.objects.count() == 1

    def test_post_movimientos_falla_si_falta_partida(self, api_client, make_jugador, make_partida, make_ronda, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        r = make_ronda(id_ronda="R1", jugador=j, numero=1, partida=p)
        pieza = make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")

        payload = {
            "id_movimiento": "M1",
            "jugador": j.id_jugador,
            "pieza": pieza.id_pieza,
            "ronda": r.id_ronda,
            "origen": "0-4",
            "destino": "1-4",
        }

        res = api_client.post("/api/movimientos/", payload, format="json")
        assert res.status_code == 400
        assert "partida" in res.data

    def test_post_movimientos_falla_origen_no_coincide_con_pieza(self, api_client, make_jugador, make_partida, make_ronda, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        r = make_ronda(id_ronda="R1", jugador=j, numero=1, partida=p)
        pieza = make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")

        payload = {
            "id_movimiento": "M1",
            "jugador": j.id_jugador,
            "pieza": pieza.id_pieza,
            "ronda": r.id_ronda,
            "partida": p.id_partida,
            "origen": "2-4",
            "destino": "1-4",
        }

        res = api_client.post("/api/movimientos/", payload, format="json")
        assert res.status_code == 400
        assert "origen" in res.data

    def test_post_movimientos_falla_destino_ocupado_misma_partida(self, api_client, make_jugador, make_partida, make_ronda, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        r = make_ronda(id_ronda="R1", jugador=j, numero=1, partida=p)
        pieza = make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")
        make_pieza(id_pieza="X2", jugador=j, partida=p, posicion="1-4")

        payload = {
            "id_movimiento": "M1",
            "jugador": j.id_jugador,
            "pieza": pieza.id_pieza,
            "ronda": r.id_ronda,
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

    def test_registrar_movimientos_falla_sin_ronda_activa(self, api_client, make_jugador, make_partida):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)

        payload = {
            "movimientos": [
                {
                    "jugador_id": j.id_jugador,
                    "ronda_id": "R1",
                    "partida_id": p.id_partida,
                    "pieza_id": "X1",
                    "origen": "0-4",
                    "destino": "1-4",
                }
            ]
        }
        res = api_client.post(f"/api/partidas/{p.id_partida}/registrar_movimientos/", payload, format="json")
        assert res.status_code == 400
        assert "ronda" in str(res.data).lower() or "No hay ronda activa" in str(res.data)

    def test_registrar_movimientos_falla_por_partida_id_mismatch(self, api_client, make_jugador, make_partida, make_ronda, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        r = make_ronda(id_ronda="R1", jugador=j, numero=1, partida=p)
        make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")

        payload = {
            "movimientos": [
                {
                    "jugador_id": j.id_jugador,
                    "ronda_id": r.id_ronda,
                    "partida_id": "P999",
                    "pieza_id": "X1",
                    "origen": "0-4",
                    "destino": "1-4",
                }
            ]
        }
        res = api_client.post(f"/api/partidas/{p.id_partida}/registrar_movimientos/", payload, format="json")
        assert res.status_code == 400

    def test_registrar_movimientos_falla_si_mueve_varias_piezas(self, api_client, make_jugador, make_partida, make_ronda, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        r = make_ronda(id_ronda="R1", jugador=j, numero=1, partida=p)
        make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")
        make_pieza(id_pieza="X2", jugador=j, partida=p, posicion="3-4")

        payload = {
            "movimientos": [
                {
                    "jugador_id": j.id_jugador,
                    "ronda_id": r.id_ronda,
                    "partida_id": p.id_partida,
                    "pieza_id": "X1",
                    "origen": "0-4",
                    "destino": "1-4",
                },
                {
                    "jugador_id": j.id_jugador,
                    "ronda_id": r.id_ronda,
                    "partida_id": p.id_partida,
                    "pieza_id": "X2",
                    "origen": "3-4",
                    "destino": "4-4",
                },
            ]
        }
        res = api_client.post(f"/api/partidas/{p.id_partida}/registrar_movimientos/", payload, format="json")
        assert res.status_code == 400

    def test_registrar_movimientos_falla_cadena_no_permite_simples(self, api_client, make_jugador, make_partida, make_ronda, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Agente Inteligente 1", humano=False, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        r = make_ronda(id_ronda="R1", jugador=j, numero=1, partida=p)
        make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")

        payload = {
            "movimientos": [
                {
                    "jugador_id": j.id_jugador,
                    "ronda_id": r.id_ronda,
                    "partida_id": p.id_partida,
                    "pieza_id": "X1",
                    "origen": "0-4",
                    "destino": "1-4",
                },
                {
                    "jugador_id": j.id_jugador,
                    "ronda_id": r.id_ronda,
                    "partida_id": p.id_partida,
                    "pieza_id": "X1",
                    "origen": "1-4",
                    "destino": "2-4",
                },
            ]
        }

        res = api_client.post(f"/api/partidas/{p.id_partida}/registrar_movimientos/", payload, format="json")
        assert res.status_code == 400

    def test_registrar_movimientos_falla_avanzar_mas_de_un_nodo_sin_saltar(
        self, api_client, make_jugador, make_partida, make_ronda, make_pieza
    ):
        j = make_jugador(id_jugador="J1", nombre="Agente Inteligente 1", humano=False, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        r = make_ronda(id_ronda="R1", jugador=j, numero=1, partida=p)

        # 0-4 -> 2-4 sería un salto si 1-4 estuviera ocupado. Aquí NO lo está.
        pieza = make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")

        payload = {
            "movimientos": [
                {
                    "jugador_id": j.id_jugador,
                    "ronda_id": r.id_ronda,
                    "partida_id": p.id_partida,
                    "pieza_id": pieza.id_pieza,
                    "origen": "0-4",
                    "destino": "2-4",
                }
            ]
        }

        res = api_client.post(f"/api/partidas/{p.id_partida}/registrar_movimientos/", payload, format="json")
        assert res.status_code == 400

    def test_registrar_movimientos_falla_salto_sin_casilla_libre_detras(self, api_client, make_jugador, make_partida, make_ronda, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Agente Inteligente 1", humano=False, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        r = make_ronda(id_ronda="R1", jugador=j, numero=1, partida=p)

        pieza = make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")
        make_pieza(id_pieza="B1", jugador=j, partida=p, posicion="1-4")
        # La casilla de aterrizaje está ocupada: salto prohibido.
        make_pieza(id_pieza="BLOCK", jugador=j, partida=p, posicion="2-4")

        payload = {
            "movimientos": [
                {
                    "jugador_id": j.id_jugador,
                    "ronda_id": r.id_ronda,
                    "partida_id": p.id_partida,
                    "pieza_id": pieza.id_pieza,
                    "origen": "0-4",
                    "destino": "2-4",
                }
            ]
        }

        res = api_client.post(f"/api/partidas/{p.id_partida}/registrar_movimientos/", payload, format="json")
        assert res.status_code == 400

    def test_registrar_movimientos_falla_salto_no_colineal(self, api_client, make_jugador, make_partida, make_ronda, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Agente Inteligente 1", humano=False, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        r = make_ronda(id_ronda="R1", jugador=j, numero=1, partida=p)

        pieza = make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")
        # Ponemos una pieza vecina para que "parezca" un salto, pero el destino no es colineal.
        make_pieza(id_pieza="B1", jugador=j, partida=p, posicion="1-4")

        payload = {
            "movimientos": [
                {
                    "jugador_id": j.id_jugador,
                    "ronda_id": r.id_ronda,
                    "partida_id": p.id_partida,
                    "pieza_id": pieza.id_pieza,
                    "origen": "0-4",
                    "destino": "2-5",
                }
            ]
        }

        res = api_client.post(f"/api/partidas/{p.id_partida}/registrar_movimientos/", payload, format="json")
        assert res.status_code == 400

    def test_registrar_movimientos_falla_origen_igual_destino(self, api_client, make_jugador, make_partida, make_ronda, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        r = make_ronda(id_ronda="R1", jugador=j, numero=1, partida=p)

        pieza = make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")

        payload = {
            "movimientos": [
                {
                    "jugador_id": j.id_jugador,
                    "ronda_id": r.id_ronda,
                    "partida_id": p.id_partida,
                    "pieza_id": pieza.id_pieza,
                    "origen": "0-4",
                    "destino": "0-4",
                }
            ]
        }

        res = api_client.post(f"/api/partidas/{p.id_partida}/registrar_movimientos/", payload, format="json")
        assert res.status_code == 400

    def test_registrar_movimientos_falla_cadena_con_salto_invalido(self, api_client, make_jugador, make_partida, make_ronda, make_pieza):
        j = make_jugador(id_jugador="J1", nombre="Agente Inteligente 1", humano=False, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        r = make_ronda(id_ronda="R1", jugador=j, numero=1, partida=p)

        pieza = make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")
        make_pieza(id_pieza="B1", jugador=j, partida=p, posicion="1-4")
        # OJO: no creamos pieza en 3-4, así que el segundo salto (2-4 -> 4-4) es inválido.

        payload = {
            "movimientos": [
                {
                    "jugador_id": j.id_jugador,
                    "ronda_id": r.id_ronda,
                    "partida_id": p.id_partida,
                    "pieza_id": pieza.id_pieza,
                    "origen": "0-4",
                    "destino": "2-4",
                },
                {
                    "jugador_id": j.id_jugador,
                    "ronda_id": r.id_ronda,
                    "partida_id": p.id_partida,
                    "pieza_id": pieza.id_pieza,
                    "origen": "2-4",
                    "destino": "4-4",
                },
            ]
        }

        res = api_client.post(f"/api/partidas/{p.id_partida}/registrar_movimientos/", payload, format="json")
        assert res.status_code == 400

    def test_registrar_movimientos_ok_salto_en_cadena_actualiza_pieza_y_crea_movimientos(
        self, api_client, make_jugador, make_partida, make_ronda, make_pieza
    ):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        t = make_ronda(id_ronda="R1", jugador=j, numero=1, partida=p)

        # Pieza a mover
        pieza = make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")

        # Piezas intermedias para permitir saltos: 0-4 -> 2-4 (sobre 1-4) -> 4-4 (sobre 3-4)
        make_pieza(id_pieza="B1", jugador=j, partida=p, posicion="1-4")
        make_pieza(id_pieza="B2", jugador=j, partida=p, posicion="3-4")

        payload = {
            "movimientos": [
                {
                    "jugador_id": j.id_jugador,
                    "ronda_id": t.id_ronda,
                    "partida_id": p.id_partida,
                    "pieza_id": pieza.id_pieza,
                    "origen": "0-4",
                    "destino": "2-4",
                },
                {
                    "jugador_id": j.id_jugador,
                    "ronda_id": t.id_ronda,
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

    def test_registrar_movimientos_ok_salto_encadenado_en_un_solo_movimiento_humano(
        self, api_client, make_jugador, make_partida, make_ronda, make_pieza
    ):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        t = make_ronda(id_ronda="R1", jugador=j, numero=1, partida=p)

        pieza = make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")
        make_pieza(id_pieza="B1", jugador=j, partida=p, posicion="1-4")
        make_pieza(id_pieza="B2", jugador=j, partida=p, posicion="3-4")

        # El frontend puede enviar directamente el destino final de un salto encadenado.
        payload = {
            "movimientos": [
                {
                    "jugador_id": j.id_jugador,
                    "ronda_id": t.id_ronda,
                    "partida_id": p.id_partida,
                    "pieza_id": pieza.id_pieza,
                    "origen": "0-4",
                    "destino": "4-4",
                }
            ]
        }

        res = api_client.post(f"/api/partidas/{p.id_partida}/registrar_movimientos/", payload, format="json")
        assert res.status_code == 201
        assert Movimiento.objects.filter(partida=p).count() == 2

        pieza.refresh_from_db()
        assert pieza.posicion == "4-4"

    def test_registrar_movimientos_falla_si_ronda_finalizada(self, api_client, make_jugador, make_partida, make_ronda, make_pieza):
        from django.utils import timezone
        from datetime import timedelta

        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        t = make_ronda(id_ronda="R1", jugador=j, numero=1, partida=p, fin=timezone.now() + timedelta(seconds=5))
        make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")

        payload = {
            "movimientos": [
                {
                    "jugador_id": j.id_jugador,
                    "ronda_id": t.id_ronda,
                    "partida_id": p.id_partida,
                    "pieza_id": "X1",
                    "origen": "0-4",
                    "destino": "1-4",
                }
            ]
        }
        res = api_client.post(f"/api/partidas/{p.id_partida}/registrar_movimientos/", payload, format="json")
        assert res.status_code == 400

    def test_registrar_movimientos_falla_si_pieza_no_pertenece_jugador(self, api_client, make_jugador, make_partida, make_ronda, make_pieza):
        j1 = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        j2 = make_jugador(id_jugador="J2", nombre="Beto", humano=True, numero=2)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        t = make_ronda(id_ronda="R1", jugador=j1, numero=1, partida=p)
        make_pieza(id_pieza="X1", jugador=j2, partida=p, posicion="0-4")

        payload = {
            "movimientos": [
                {
                    "jugador_id": j1.id_jugador,
                    "ronda_id": t.id_ronda,
                    "partida_id": p.id_partida,
                    "pieza_id": "X1",
                    "origen": "0-4",
                    "destino": "1-4",
                }
            ]
        }

        res = api_client.post(f"/api/partidas/{p.id_partida}/registrar_movimientos/", payload, format="json")
        assert res.status_code == 400

    def test_registrar_movimientos_falla_si_jugador_no_existe(self, api_client, make_jugador, make_partida, make_ronda, make_pieza):
        j1 = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        t = make_ronda(id_ronda="R1", jugador=j1, numero=1, partida=p)
        make_pieza(id_pieza="X1", jugador=j1, partida=p, posicion="0-4")

        payload = {
            "movimientos": [
                {
                    "jugador_id": "J_NO_EXISTE",
                    "ronda_id": t.id_ronda,
                    "partida_id": p.id_partida,
                    "pieza_id": "X1",
                    "origen": "0-4",
                    "destino": "1-4",
                }
            ]
        }

        res = api_client.post(f"/api/partidas/{p.id_partida}/registrar_movimientos/", payload, format="json")
        assert res.status_code == 400
        assert "Jugador no encontrado" in str(res.data)

    def test_registrar_movimientos_falla_si_pieza_no_existe(self, api_client, make_jugador, make_partida, make_ronda):
        j1 = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        t = make_ronda(id_ronda="R1", jugador=j1, numero=1, partida=p)

        payload = {
            "movimientos": [
                {
                    "jugador_id": j1.id_jugador,
                    "ronda_id": t.id_ronda,
                    "partida_id": p.id_partida,
                    "pieza_id": "X_NO_EXISTE",
                    "origen": "0-4",
                    "destino": "1-4",
                }
            ]
        }

        res = api_client.post(f"/api/partidas/{p.id_partida}/registrar_movimientos/", payload, format="json")
        assert res.status_code == 400
        assert "Pieza no encontrada" in str(res.data)

    def test_registrar_movimientos_falla_si_ronda_no_existe(self, api_client, make_jugador, make_partida, make_pieza, make_ronda):
        j1 = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        make_ronda(id_ronda="R1", jugador=j1, numero=1, partida=p)
        make_pieza(id_pieza="X1", jugador=j1, partida=p, posicion="0-4")

        payload = {
            "movimientos": [
                {
                    "jugador_id": j1.id_jugador,
                    "ronda_id": "R_NO_EXISTE",
                    "partida_id": p.id_partida,
                    "pieza_id": "X1",
                    "origen": "0-4",
                    "destino": "1-4",
                }
            ]
        }

        res = api_client.post(f"/api/partidas/{p.id_partida}/registrar_movimientos/", payload, format="json")
        assert res.status_code == 400
        assert "Ronda no encontrada" in str(res.data)

    def test_registrar_movimientos_falla_si_destino_fuera_del_tablero(self, api_client, make_jugador, make_partida, make_ronda, make_pieza):
        j1 = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)
        t = make_ronda(id_ronda="R1", jugador=j1, numero=1, partida=p)
        make_pieza(id_pieza="X1", jugador=j1, partida=p, posicion="0-4")

        payload = {
            "movimientos": [
                {
                    "jugador_id": j1.id_jugador,
                    "ronda_id": t.id_ronda,
                    "partida_id": p.id_partida,
                    "pieza_id": "X1",
                    "origen": "0-4",
                    "destino": "99-99",
                }
            ]
        }

        res = api_client.post(f"/api/partidas/{p.id_partida}/registrar_movimientos/", payload, format="json")
        assert res.status_code == 400


@pytest.mark.django_db
class TestMovimientosQueryParams:
    def test_list_movimientos_filtra_por_ronda_id(self, api_client, make_jugador, make_partida, make_ronda, make_pieza, make_movimiento):
        j = make_jugador(id_jugador="J1", nombre="Ana", humano=True, numero=1)
        p = make_partida(id_partida="P1", numero_jugadores=2)

        t1 = make_ronda(id_ronda="R1", jugador=j, numero=1, partida=p)
        t2 = make_ronda(id_ronda="R2", jugador=j, numero=2, partida=p)
        pieza = make_pieza(id_pieza="X1", jugador=j, partida=p, posicion="0-4")

        make_movimiento(id_movimiento="M1", jugador=j, pieza=pieza, ronda=t1, partida=p, origen="0-4", destino="1-4")
        make_movimiento(id_movimiento="M2", jugador=j, pieza=pieza, ronda=t2, partida=p, origen="0-4", destino="1-4")

        res = api_client.get(f"/api/movimientos/?ronda_id={t1.id_ronda}")
        assert res.status_code == 200
        assert len(res.data) == 1
        assert res.data[0]["ronda"] == t1.id_ronda
