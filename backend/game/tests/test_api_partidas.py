import pytest

from game.models import Jugador, Partida, Pieza, Turno


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

    res = api_client.post("/api/partidas/start_game/", payload, format="json")
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

    res = api_client.post("/api/partidas/start_game/", payload, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_start_game_rechaza_mas_de_seis_jugadores(api_client):
    payload = {
        "numero_jugadores": 7,
        "jugadores": [
            {"tipo": "humano", "nombre": f"J{i}", "numero": i} for i in range(1, 8)
        ],
    }

    res = api_client.post("/api/partidas/start_game/", payload, format="json")
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

    res = api_client.post("/api/partidas/start_game/", payload, format="json")
    assert res.status_code == 400


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
