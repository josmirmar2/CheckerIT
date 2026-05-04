const ROW_LENGTHS = [1, 2, 3, 4, 13, 12, 11, 10, 9, 10, 11, 12, 13, 4, 3, 2, 1];

export function isValidPositionKey(key) {
  if (typeof key !== 'string' || !key.includes('-')) return false;

  const [colRaw, rowRaw] = key.split('-', 2);
  const col = Number(colRaw);
  const row = Number(rowRaw);

  if (!Number.isInteger(col) || !Number.isInteger(row)) return false;
  if (row < 0 || row >= ROW_LENGTHS.length) return false;

  return col >= 0 && col < ROW_LENGTHS[row];
}

export function buildSecureMovimientosPayload({
  moves,
  partidaId,
  jugadorId,
  rondaId,
  allowedPieceIds,
}) {
  const allowed = allowedPieceIds instanceof Set ? allowedPieceIds : new Set(allowedPieceIds || []);

  if (!Array.isArray(moves) || !partidaId || !jugadorId || !rondaId) {
    return [];
  }

  return moves
    .map((m) => {
      const origen = `${m.from.col}-${m.from.fila}`;
      const destino = `${m.to.col}-${m.to.fila}`;
      return {
        origen,
        destino,
        partida_id: partidaId,
        jugador_id: jugadorId,
        ronda_id: rondaId,
        pieza_id: m.pieza_id,
      };
    })
    .filter((m) => {
      if (!m.pieza_id) return false;
      if (!allowed.has(m.pieza_id)) return false;
      if (!isValidPositionKey(m.origen) || !isValidPositionKey(m.destino)) return false;
      if (m.origen === m.destino) return false;
      return true;
    });
}

export function buildRoundAdvancePayload({ partidaId, actualRound, dbJugadores, currentPlayerIndex }) {
  if (!partidaId || !actualRound || !Array.isArray(dbJugadores) || dbJugadores.length === 0) {
    return null;
  }

  const currentJugador = dbJugadores[currentPlayerIndex];
  if (!currentJugador?.id_jugador) return null;

  const currentJugadorNumero = currentJugador.numero || 1;
  const maxNumero = Math.max(...dbJugadores.map((j) => j.numero || 1));
  const nextNumero = currentJugadorNumero >= maxNumero ? 1 : currentJugadorNumero + 1;
  const nextJugador = dbJugadores.find((j) => j.numero === nextNumero) || dbJugadores[0];
  if (!nextJugador?.id_jugador) return null;

  const roundNumber = actualRound.numero || 0;

  return {
    oldRound: {
      numero: roundNumber,
      inicio: actualRound.inicio,
      final: new Date().toISOString(),
      jugador_id: currentJugador.id_jugador,
      partida_id: partidaId,
    },
    newRoundCreated: {
      numero: roundNumber + 1,
      inicio: new Date().toISOString(),
      jugador_id: nextJugador.id_jugador,
      partida_id: partidaId,
    },
    nextNumero,
  };
}
