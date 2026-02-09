import pytest

from game.models import IA, Chatbot, Jugador, JugadorPartida, Movimiento, Partida, Pieza, Turno


def _start_game(api_client, payload=None):
    if payload is None:
        payload = {
            "numero_jugadores": 2,
            "jugadores": [
                {"tipo": "humano", "nombre": "Jugador 1", "dificultad": "Fácil", "numero": 1},
                {"tipo": "ia", "dificultad": "Difícil", "numero": 2},
            ],
        }
    res = api_client.post("/api/partidas/start_game/", payload, format="json")
    return res


@pytest.mark.django_db
def test_api_root_responde_ok(api_client):
    res = api_client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data.get("mensaje")
    assert "api" in data.get("endpoints", {})


@pytest.mark.django_db
def test_start_game_crea_partida_y_turno(api_client):
    payload = {
        "numero_jugadores": 2,
        "jugadores": [
            {"tipo": "humano", "nombre": "Jugador 1", "dificultad": "Fácil", "numero": 1},
            {"tipo": "ia", "dificultad": "Difícil", "numero": 2},
        ],
    }

    res = _start_game(api_client, payload)
    assert res.status_code == 201

    data = res.json()
    assert data["id_partida"]
    assert data["numero_jugadores"] == 2
    assert len(data["participantes"]) == 2
    assert len(data["turnos"]) == 1


@pytest.mark.django_db
def test_start_game_rechaza_menos_de_dos_jugadores(api_client):
    payload = {
        "numero_jugadores": 1,
        "jugadores": [
            {"tipo": "humano", "nombre": "Solo", "numero": 1},
        ],
    }

    res = _start_game(api_client, payload)
    assert res.status_code == 400


@pytest.mark.django_db
def test_start_game_rechaza_mas_de_seis_jugadores(api_client):
    payload = {
        "numero_jugadores": 7,
        "jugadores": [
            {"tipo": "humano", "nombre": f"J{i}", "numero": i} for i in range(1, 8)
        ],
    }

    res = _start_game(api_client, payload)
    assert res.status_code == 400


@pytest.mark.django_db
def test_start_game_rechaza_numeros_de_jugador_duplicados(api_client):
    payload = {
        "numero_jugadores": 2,
        "jugadores": [
            {"tipo": "humano", "nombre": "A", "numero": 1},
            {"tipo": "humano", "nombre": "B", "numero": 1},
        ],
    }

    res = _start_game(api_client, payload)
    assert res.status_code == 400


@pytest.mark.django_db
def test_start_game_permita_numero_jugadores_implicito(api_client):
    payload = {
        "jugadores": [
            {"tipo": "humano", "nombre": "A", "numero": 1},
            {"tipo": "humano", "nombre": "B", "numero": 2},
        ]
    }
    res = _start_game(api_client, payload)
    assert res.status_code == 201
    data = res.json()
    assert data["numero_jugadores"] == 2


@pytest.mark.django_db
def test_start_game_rechaza_numero_jugadores_no_entero(api_client):
    payload = {
        "numero_jugadores": "dos",
        "jugadores": [
            {"tipo": "humano", "nombre": "A", "numero": 1},
            {"tipo": "humano", "nombre": "B", "numero": 2},
        ],
    }
    res = _start_game(api_client, payload)
    assert res.status_code == 400


@pytest.mark.django_db
def test_start_game_rechaza_sin_jugadores(api_client):
    res = _start_game(api_client, {"numero_jugadores": 2, "jugadores": []})
    assert res.status_code == 400


@pytest.mark.django_db
def test_start_game_crea_piezas_iniciales_10_por_jugador(api_client):
    res = _start_game(api_client)
    assert res.status_code == 201
    partida_id = res.json()["id_partida"]
    assert Pieza.objects.filter(partida_id=partida_id).count() == 20


@pytest.mark.django_db
def test_start_game_crea_ia_con_nivel_correcto(api_client):
    res = _start_game(api_client)
    assert res.status_code == 201
    data = res.json()
    partida_id = data["id_partida"]

    jugadores_ids = [p["jugador"] for p in data.get("participantes", [])]
    jugadores = list(Jugador.objects.filter(id_jugador__in=jugadores_ids))
    ia_players = [j for j in jugadores if not j.humano]
    assert len(ia_players) == 1
    assert IA.objects.get(jugador=ia_players[0]).nivel == 2

    assert Partida.objects.filter(id_partida=partida_id).exists()


@pytest.mark.django_db
def test_crear_pieza_rechaza_posicion_invalida(api_client):
    jugador = Jugador.objects.create(id_jugador="J_API", nombre="Ana", humano=True, numero=1)
    payload = {
        "id_pieza": "PX1",
        "tipo": "punta-0",
        "posicion": "99-99",
        "jugador": jugador.id_jugador,
        "ia": None,
        "chatbot": None,
        "partida": None,
    }

    res = api_client.post("/api/piezas/", payload, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_crear_movimiento_rechaza_origen_o_destino_fuera_del_tablero(api_client):
    jugador = Jugador.objects.create(id_jugador="J_API", nombre="Ana", humano=True, numero=1)
    partida = Partida.objects.create(id_partida="P_API", numero_jugadores=2)
    pieza = Pieza.objects.create(
        id_pieza="PX1",
        tipo="punta-0",
        posicion="0-0",
        jugador=jugador,
        partida=partida,
    )
    turno = Turno.objects.create(id_turno="T_API", jugador=jugador, numero=1, partida=partida)

    payload_bad_origen = {
        "id_movimiento": "M_API_1",
        "jugador": jugador.id_jugador,
        "pieza": pieza.id_pieza,
        "turno": turno.id_turno,
        "partida": partida.id_partida,
        "origen": "99-99",
        "destino": "0-1",
    }
    res1 = api_client.post("/api/movimientos/", payload_bad_origen, format="json")
    assert res1.status_code == 400

    payload_bad_destino = {
        "id_movimiento": "M_API_2",
        "jugador": jugador.id_jugador,
        "pieza": pieza.id_pieza,
        "turno": turno.id_turno,
        "partida": partida.id_partida,
        "origen": "0-0",
        "destino": "99-99",
    }
    res2 = api_client.post("/api/movimientos/", payload_bad_destino, format="json")
    assert res2.status_code == 400


@pytest.mark.django_db
def test_crear_movimiento_rechaza_origen_que_no_coincide_con_posicion_de_pieza(api_client):
    jugador = Jugador.objects.create(id_jugador="J_API", nombre="Ana", humano=True, numero=1)
    partida = Partida.objects.create(id_partida="P_API", numero_jugadores=2)
    pieza = Pieza.objects.create(
        id_pieza="PX1",
        tipo="punta-0",
        posicion="0-0",
        jugador=jugador,
        partida=partida,
    )
    turno = Turno.objects.create(id_turno="T_API", jugador=jugador, numero=1, partida=partida)

    payload = {
        "id_movimiento": "M_API_ORIGEN_MAL",
        "jugador": jugador.id_jugador,
        "pieza": pieza.id_pieza,
        "turno": turno.id_turno,
        "partida": partida.id_partida,
        "origen": "0-1",
        "destino": "0-2",
    }
    res = api_client.post("/api/movimientos/", payload, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_crear_movimiento_rechaza_destino_ocupado(api_client):
    jugador = Jugador.objects.create(id_jugador="J_API", nombre="Ana", humano=True, numero=1)
    partida = Partida.objects.create(id_partida="P_API", numero_jugadores=2)
    pieza = Pieza.objects.create(
        id_pieza="PX1",
        tipo="punta-0",
        posicion="0-0",
        jugador=jugador,
        partida=partida,
    )
    Pieza.objects.create(
        id_pieza="PX2",
        tipo="punta-0",
        posicion="0-1",
        jugador=jugador,
        partida=partida,
    )
    turno = Turno.objects.create(id_turno="T_API", jugador=jugador, numero=1, partida=partida)

    payload = {
        "id_movimiento": "M_API_DESTINO_OCUPADO",
        "jugador": jugador.id_jugador,
        "pieza": pieza.id_pieza,
        "turno": turno.id_turno,
        "partida": partida.id_partida,
        "origen": "0-0",
        "destino": "0-1",
    }
    res = api_client.post("/api/movimientos/", payload, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_crear_movimiento_no_rechaza_destino_ocupado_en_otra_partida(api_client):
    jugador = Jugador.objects.create(id_jugador="J_API", nombre="Ana", humano=True, numero=1)
    partida1 = Partida.objects.create(id_partida="P_API_1", numero_jugadores=2)
    partida2 = Partida.objects.create(id_partida="P_API_2", numero_jugadores=2)

    # En la otra partida existe una pieza en el destino
    Pieza.objects.create(
        id_pieza="PX_OTHER",
        tipo="punta-0",
        posicion="0-1",
        jugador=jugador,
        partida=partida2,
    )

    pieza = Pieza.objects.create(
        id_pieza="PX1",
        tipo="punta-0",
        posicion="0-0",
        jugador=jugador,
        partida=partida1,
    )
    turno = Turno.objects.create(id_turno="T_API", jugador=jugador, numero=1, partida=partida1)

    payload = {
        "id_movimiento": "M_API_OK_OTRA_PARTIDA",
        "jugador": jugador.id_jugador,
        "pieza": pieza.id_pieza,
        "turno": turno.id_turno,
        "partida": partida1.id_partida,
        "origen": "0-0",
        "destino": "0-1",
    }
    res = api_client.post("/api/movimientos/", payload, format="json")
    assert res.status_code == 201


@pytest.mark.django_db
def test_crear_participacion_rechaza_exceder_numero_jugadores_de_partida(api_client):
    p = Partida.objects.create(id_partida="P_API", numero_jugadores=2)
    j1 = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    j2 = Jugador.objects.create(id_jugador="J2", nombre="Pedro", humano=True, numero=2)
    j3 = Jugador.objects.create(id_jugador="J3", nombre="Luis", humano=True, numero=3)

    res1 = api_client.post(
        "/api/participaciones/",
        {"jugador": j1.id_jugador, "partida": p.id_partida, "orden_participacion": 1},
        format="json",
    )
    assert res1.status_code == 201

    res2 = api_client.post(
        "/api/participaciones/",
        {"jugador": j2.id_jugador, "partida": p.id_partida, "orden_participacion": 2},
        format="json",
    )
    assert res2.status_code == 201

    res3 = api_client.post(
        "/api/participaciones/",
        {"jugador": j3.id_jugador, "partida": p.id_partida, "orden_participacion": 3},
        format="json",
    )
    assert res3.status_code == 400


@pytest.mark.django_db
def test_crear_participacion_rechaza_orden_participacion_fuera_de_rango(api_client):
    p = Partida.objects.create(id_partida="P_API", numero_jugadores=2)
    j1 = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)

    res = api_client.post(
        "/api/participaciones/",
        {"jugador": j1.id_jugador, "partida": p.id_partida, "orden_participacion": 3},
        format="json",
    )
    assert res.status_code == 400


@pytest.mark.django_db
def test_crear_participacion_rechaza_orden_duplicado_en_partida(api_client):
    p = Partida.objects.create(id_partida="P_API", numero_jugadores=3)
    j1 = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)
    j2 = Jugador.objects.create(id_jugador="J2", nombre="Pedro", humano=True, numero=2)

    res1 = api_client.post(
        "/api/participaciones/",
        {"jugador": j1.id_jugador, "partida": p.id_partida, "orden_participacion": 1},
        format="json",
    )
    assert res1.status_code == 201

    res2 = api_client.post(
        "/api/participaciones/",
        {"jugador": j2.id_jugador, "partida": p.id_partida, "orden_participacion": 1},
        format="json",
    )
    assert res2.status_code == 400


@pytest.mark.django_db
def test_crear_participacion_rechaza_jugador_duplicado_en_partida(api_client):
    p = Partida.objects.create(id_partida="P_API", numero_jugadores=3)
    j1 = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=True, numero=1)

    res1 = api_client.post(
        "/api/participaciones/",
        {"jugador": j1.id_jugador, "partida": p.id_partida, "orden_participacion": 1},
        format="json",
    )
    assert res1.status_code == 201

    res2 = api_client.post(
        "/api/participaciones/",
        {"jugador": j1.id_jugador, "partida": p.id_partida, "orden_participacion": 2},
        format="json",
    )
    assert res2.status_code == 400


@pytest.mark.django_db
def test_accion_actualizar_posiciones_iniciales_ok(api_client):
    res = _start_game(api_client)
    assert res.status_code == 201
    partida_id = res.json()["id_partida"]

    res2 = api_client.post(f"/api/partidas/{partida_id}/actualizar_posiciones_iniciales/", {}, format="json")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2.get("piezas_actualizadas") == 20


@pytest.mark.django_db
def test_accion_end_game_finaliza_partida_y_turno(api_client):
    res = _start_game(api_client)
    assert res.status_code == 201
    partida_id = res.json()["id_partida"]

    res2 = api_client.post(f"/api/partidas/{partida_id}/end_game/", {}, format="json")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["estado"] == "FINALIZADA"
    assert data2.get("fecha_fin") is not None

    turno = Turno.objects.filter(partida_id=partida_id).order_by("numero").first()
    assert turno is not None
    turno.refresh_from_db()
    assert turno.fin is not None


@pytest.mark.django_db
def test_accion_avanzar_turno_crea_nuevo_turno(api_client):
    res = _start_game(api_client)
    assert res.status_code == 201
    data = res.json()
    partida_id = data["id_partida"]

    jugador_ids = [p["jugador"] for p in data.get("participantes", [])]
    assert len(jugador_ids) == 2

    payload = {
        "oldTurn": {"final": None},
        "newTurnCreated": {"numero": 2, "jugador_id": jugador_ids[1]},
    }
    res2 = api_client.post(f"/api/partidas/{partida_id}/avanzar_turno/", payload, format="json")
    assert res2.status_code == 201
    data2 = res2.json()
    assert data2["nuevo_turno"]["numero"] == 2
    assert data2["nuevo_turno"]["jugador"] == jugador_ids[1]


@pytest.mark.django_db
def test_delete_partida_elimina_partida_y_jugadores_asociados(api_client):
    res = _start_game(api_client)
    assert res.status_code == 201
    data = res.json()
    partida_id = data["id_partida"]
    jugador_ids = [p["jugador"] for p in data.get("participantes", [])]

    res2 = api_client.delete(f"/api/partidas/{partida_id}/")
    assert res2.status_code == 204

    assert Partida.objects.filter(id_partida=partida_id).count() == 0
    assert JugadorPartida.objects.filter(partida_id=partida_id).count() == 0
    assert Pieza.objects.filter(partida_id=partida_id).count() == 0
    assert Turno.objects.filter(partida_id=partida_id).count() == 0
    assert Movimiento.objects.filter(partida_id=partida_id).count() == 0
    assert Jugador.objects.filter(id_jugador__in=jugador_ids).count() == 0


@pytest.mark.django_db
def test_crear_ia_rechaza_nivel_fuera_de_1_2(api_client):
    j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=False, numero=1)
    res = api_client.post("/api/ia/", {"jugador": j.id_jugador, "nivel": 3}, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_crear_jugador_ia_normaliza_nombre(api_client):
    res = api_client.post(
        "/api/jugadores/",
        {"id_jugador": "J_IA", "nombre": "X", "humano": False, "numero": 7},
        format="json",
    )
    assert res.status_code == 201
    j = Jugador.objects.get(id_jugador="J_IA")
    assert j.nombre == "IA 7"


@pytest.mark.django_db
def test_chatbot_send_message_responde(api_client):
    j = Jugador.objects.create(id_jugador="J1", nombre="Ana", humano=False, numero=1)
    ia = IA.objects.create(jugador=j, nivel=1)
    chatbot = Chatbot.objects.create(ia=ia, memoria={}, contexto={})

    res = api_client.post(f"/api/chatbot/{chatbot.pk}/send_message/", {"mensaje": "hola"}, format="json")
    assert res.status_code == 200
    assert "respuesta" in res.json()
