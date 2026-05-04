import {
  buildRoundAdvancePayload,
  buildSecureMovimientosPayload,
  isValidPositionKey,
} from './integrityGuards';

describe('integrityGuards', () => {
  test('isValidPositionKey validates board bounds', () => {
    expect(isValidPositionKey('0-0')).toBe(true);
    expect(isValidPositionKey('0-16')).toBe(true);
    expect(isValidPositionKey('1-0')).toBe(false);
    expect(isValidPositionKey('99-99')).toBe(false);
    expect(isValidPositionKey('abc')).toBe(false);
  });

  test('buildSecureMovimientosPayload filters tampered moves', () => {
    const payload = buildSecureMovimientosPayload({
      partidaId: 'P1',
      jugadorId: 'J1',
      rondaId: 'R1',
      allowedPieceIds: new Set(['PX_OK']),
      moves: [
        { from: { col: 0, fila: 4 }, to: { col: 1, fila: 4 }, pieza_id: 'PX_OK' },
        { from: { col: 0, fila: 4 }, to: { col: 99, fila: 99 }, pieza_id: 'PX_OK' },
        { from: { col: 1, fila: 4 }, to: { col: 1, fila: 4 }, pieza_id: 'PX_OK' },
        { from: { col: 1, fila: 4 }, to: { col: 2, fila: 4 }, pieza_id: 'PX_HIJACK' },
        { from: { col: 1, fila: 4 }, to: { col: 2, fila: 4 } },
      ],
    });

    expect(payload).toHaveLength(1);
    expect(payload[0]).toEqual({
      origen: '0-4',
      destino: '1-4',
      partida_id: 'P1',
      jugador_id: 'J1',
      ronda_id: 'R1',
      pieza_id: 'PX_OK',
    });
  });

  test('buildRoundAdvancePayload computes next player and round number', () => {
    const dbJugadores = [
      { id_jugador: 'J1', numero: 1 },
      { id_jugador: 'J2', numero: 2 },
    ];

    const payload = buildRoundAdvancePayload({
      partidaId: 'P1',
      actualRound: { numero: 1, inicio: '2026-05-04T10:00:00Z' },
      dbJugadores,
      currentPlayerIndex: 0,
    });

    expect(payload).not.toBeNull();
    expect(payload.newRoundCreated.jugador_id).toBe('J2');
    expect(payload.newRoundCreated.numero).toBe(1);

    const wrapPayload = buildRoundAdvancePayload({
      partidaId: 'P1',
      actualRound: { numero: 1, inicio: '2026-05-04T10:00:00Z' },
      dbJugadores,
      currentPlayerIndex: 1,
    });

    expect(wrapPayload).not.toBeNull();
    expect(wrapPayload.newRoundCreated.jugador_id).toBe('J1');
    expect(wrapPayload.newRoundCreated.numero).toBe(2);
  });

  test('buildRoundAdvancePayload returns null when context is incomplete', () => {
    expect(
      buildRoundAdvancePayload({
        partidaId: null,
        actualRound: { numero: 1 },
        dbJugadores: [{ id_jugador: 'J1', numero: 1 }],
        currentPlayerIndex: 0,
      })
    ).toBeNull();
  });
});
