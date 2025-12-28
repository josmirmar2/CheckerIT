import React, { useState, useEffect } from 'react';
import './Board.css';

const Board = ({ jugadoresConfig, dbJugadores = [], currentPlayerIndex = 0, partidaId = null, onMove = null, moveMade = false, lockedPiecePos = null, undoToken = 0, undoToOriginalToken = 0, originalPiecePos = null, initialBoardState = null, pieceByPos = new Map() }) => {
  const BOARD_COLORS = ['#FFFFFF', '#0000ffff', '#00ff00ff', '#000000', '#ff0000ff', '#ffbf00ff'];
  const LIGHT_COLORS = ['#ffffffcf', '#8888ffaf', '#9af89aab', '#666666af', '#ffa2a2a1', '#ffe988b6'];

  // Mapa de coordenadas cartesianas (q, r) por posición col-fila
  const CARTESIAN_COORD_ROWS = [
    [{ q: 0, r: 0 }],
    [{ q: -1, r: 1 }, { q: 0, r: 1 }],
    [{ q: -2, r: 2 }, { q: -1, r: 2 }, { q: 0, r: 2 }],
    [{ q: -3, r: 3 }, { q: -2, r: 3 }, { q: -1, r: 3 }, { q: 0, r: 3 }],
    [{ q: -8, r: 4 }, { q: -7, r: 4 }, { q: -6, r: 4 }, { q: -5, r: 4 }, { q: -4, r: 4 }, { q: -3, r: 4 }, { q: -2, r: 4 }, { q: -1, r: 4 }, { q: 0, r: 4 }, { q: 1, r: 4 }, { q: 2, r: 4 }, { q: 3, r: 4 }, { q: 4, r: 4 }],
    [{ q: -8, r: 5 }, { q: -7, r: 5 }, { q: -6, r: 5 }, { q: -5, r: 5 }, { q: -4, r: 5 }, { q: -3, r: 5 }, { q: -2, r: 5 }, { q: -1, r: 5 }, { q: 0, r: 5 }, { q: 1, r: 5 }, { q: 2, r: 5 }, { q: 3, r: 5 }],
    [{ q: -8, r: 6 }, { q: -7, r: 6 }, { q: -6, r: 6 }, { q: -5, r: 6 }, { q: -4, r: 6 }, { q: -3, r: 6 }, { q: -2, r: 6 }, { q: -1, r: 6 }, { q: 0, r: 6 }, { q: 1, r: 6 }, { q: 2, r: 6 }],
    [{ q: -8, r: 7 }, { q: -7, r: 7 }, { q: -6, r: 7 }, { q: -5, r: 7 }, { q: -4, r: 7 }, { q: -3, r: 7 }, { q: -2, r: 7 }, { q: -1, r: 7 }, { q: 0, r: 7 }, { q: 1, r: 7 }],
    [{ q: -8, r: 8 }, { q: -7, r: 8 }, { q: -6, r: 8 }, { q: -5, r: 8 }, { q: -4, r: 8 }, { q: -3, r: 8 }, { q: -2, r: 8 }, { q: -1, r: 8 }, { q: 0, r: 8 }],
    [{ q: -9, r: 9 }, { q: -8, r: 9 }, { q: -7, r: 9 }, { q: -6, r: 9 }, { q: -5, r: 9 }, { q: -4, r: 9 }, { q: -3, r: 9 }, { q: -2, r: 9 }, { q: -1, r: 9 }, { q: 0, r: 9 }],
    [{ q: -10, r: 10 }, { q: -9, r: 10 }, { q: -8, r: 10 }, { q: -7, r: 10 }, { q: -6, r: 10 }, { q: -5, r: 10 }, { q: -4, r: 10 }, { q: -3, r: 10 }, { q: -2, r: 10 }, { q: -1, r: 10 }, { q: 0, r: 10 }],
    [{ q: -11, r: 11 }, { q: -10, r: 11 }, { q: -9, r: 11 }, { q: -8, r: 11 }, { q: -7, r: 11 }, { q: -6, r: 11 }, { q: -5, r: 11 }, { q: -4, r: 11 }, { q: -3, r: 11 }, { q: -2, r: 11 }, { q: -1, r: 11 }, { q: 0, r: 11 }],
    [{ q: -12, r: 12 }, { q: -11, r: 12 }, { q: -10, r: 12 }, { q: -9, r: 12 }, { q: -8, r: 12 }, { q: -7, r: 12 }, { q: -6, r: 12 }, { q: -5, r: 12 }, { q: -4, r: 12 }, { q: -3, r: 12 }, { q: -2, r: 12 }, { q: -1, r: 12 }, { q: 0, r: 12 }],
    [{ q: -8, r: 13 }, { q: -7, r: 13 }, { q: -6, r: 13 }, { q: -5, r: 13 }],
    [{ q: -8, r: 14 }, { q: -7, r: 14 }, { q: -6, r: 14 }],
    [{ q: -8, r: 15 }, { q: -7, r: 15 }],
    [{ q: -8, r: 16 }],
  ];

  const POSITION_TO_CARTESIAN = new Map();
  CARTESIAN_COORD_ROWS.forEach((row, filaIdx) => {
    row.forEach((coord, colIdx) => {
      POSITION_TO_CARTESIAN.set(`${colIdx}-${filaIdx}`, coord);
    });
  });

  const [pieceMapLocal, setPieceMapLocal] = useState(new Map());
  const [selectedPieceId, setSelectedPieceId] = useState(null);
  const [positionsList, setPositionsList] = useState([]); 

  useEffect(() => {
    const loadPieces = async () => {
      try {
        if (!partidaId) return;
        const res = await fetch(`http://localhost:8000/api/piezas/?partida_id=${partidaId}`);
        const data = await res.json();
        const map = new Map();
        (Array.isArray(data) ? data : []).forEach(p => {
          if (p.partida !== partidaId) return;
          if (!p.posicion) return;
          map.set(p.posicion, p.id_pieza);
        });
        setPieceMapLocal(map);
        setPositionsList(Array.from(map.keys()));
      } catch (e) {
        console.error('Error cargando piezas en Board:', e);
      }
    };
    loadPieces();
  }, [jugadoresConfig, partidaId]);

  const getActivePuntas = (numJugadores) => {
    switch (numJugadores) {
      case 2:
        return [0, 3];
      case 3:
        return [0, 4, 5];
      case 4:
        return [1, 2, 4, 5];
      case 6:
        return [0, 1, 2, 3, 4, 5];
      default:
        return [];
    }
  };

  const generarTablero = () => {
    const filas = [
      [0],
      [0, 1],  
      [0, 1, 2],                         
      [0, 1, 2, 3],  
      [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], 
      [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], 
      [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 
      [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
      [0, 1, 2, 3, 4, 5, 6, 7, 8],                      
      [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
      [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
      [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], 
      [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
      [0, 1, 2, 3],
      [0, 1, 2],
      [0, 1],
      [0],                       
    ];

    const posicionAPunta = {
      // Punta 0 (Arriba)
      '0-0': 0, '1-1': 0, '0-3': 0, '1-3': 0, '2-3': 0,
      '0-1': 0, '0-2': 0, '1-2': 0, '2-2': 0, '3-3': 0,
      // Punta 1 (Izquierda-Arriba)
      '0-4': 1, '2-4': 1, '0-5': 1, '2-5': 1, '1-6': 1,
      '1-4': 1, '3-4': 1, '1-5': 1, '0-6': 1, '0-7': 1,
      // Punta 2 (Derecha-Arriba)
      '12-4': 2, '10-4': 2, '11-5': 2, '9-5': 2, '9-6': 2,
      '11-4': 2, '9-4': 2, '10-5': 2, '10-6': 2, '9-7': 2,
      // Punta 4 (Izquierda-Abajo)
      '0-9': 4, '0-11': 4, '1-11': 4, '0-12': 4, '2-12': 4,
      '0-10': 4, '1-10': 4, '2-11': 4, '1-12': 4, '3-12': 4,
      // Punta 5 (Derecha-Abajo)
      '9-9': 5, '9-11': 5, '10-11': 5, '10-12': 5, '12-12': 5,
      '9-10': 5, '10-10': 5, '11-11': 5, '9-12': 5, '11-12': 5,
      // Punta 3 (Abajo)
      '3-13': 3, '1-13': 3, '0-14': 3, '2-14': 3, '1-15': 3,
      '2-13': 3, '0-13': 3, '1-14': 3, '0-15': 3, '0-16': 3,
    };

    const activePuntas = getActivePuntas(jugadoresConfig.length);
    const tablero = [];
    let huecoId = 0;

    filas.forEach((fila, filaIdx) => {
      const huecosFila = [];
      const numHuecos = fila.length;
      const offset = (10 - numHuecos) / 2; 

      fila.forEach((_, colIdx) => {
        const punta = posicionAPunta[`${colIdx}-${filaIdx}`] ?? null;
        const tieneJugador = punta !== null && activePuntas.includes(punta);

        huecosFila.push({
          id: huecoId++,
          punta,
          jugadorIndex: tieneJugador ? punta : null,
          offset,
        });
      });

      tablero.push(huecosFila);
    });

    return tablero;
  };

  const [tablero, setTablero] = useState(() => generarTablero());
  const [boardPieces, setBoardPieces] = useState([]);
  const [selectedCell, setSelectedCell] = useState(null);
  const [moveHistory, setMoveHistory] = useState([]);
  const [turnStartBoardState, setTurnStartBoardState] = useState(null);
  const [turnStartPieceMap, setTurnStartPieceMap] = useState(null);
  const [turnStartPositionsList, setTurnStartPositionsList] = useState(null);

  const activePuntas = getActivePuntas(jugadoresConfig.length);
  const puntaToPlayerIndex = activePuntas.reduce((acc, puntaIdx, playerIdx) => {
    acc[puntaIdx] = playerIdx;
    return acc;
  }, {});

  useEffect(() => {
    const layout = generarTablero();
    setTablero(layout);

    const piezas = layout.map((fila) =>
      fila.map((hueco) => {
        const punta = hueco.punta;
        const hasPlayer = punta !== null && activePuntas.includes(punta);
        return hasPlayer ? punta : null;
      })
    );

    setBoardPieces(piezas);
    setSelectedCell(null);
    setMoveHistory([]);
    setTurnStartBoardState(piezas);
  }, [jugadoresConfig.length]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!moveMade) {
      // Solo limpiar snapshots cuando el turno termina (moveMade = false)
      // Esto asegura que el snapshot esté disponible para undo
      setTurnStartBoardState(null);
      setTurnStartPieceMap(null);
      setTurnStartPositionsList(null);
    }
  }, [moveMade]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (undoToken === 0 || moveHistory.length === 0) return;
    const last = moveHistory[moveHistory.length - 1];
    const { from, to, piezaId: lastPiezaId = null } = last;
    const next = boardPieces.map((r) => [...r]);
    next[from.fila][from.col] = next[to.fila][to.col];
    next[to.fila][to.col] = null;
    setBoardPieces(next);
    console.log('↩️ Movimiento deshecho:', last);
    console.log('🔙 Estado del tablero después de deshacer:', next);
    
    // Actualizar pieceMapLocal: mover la pieza de vuelta a su posición original
    const oldKey = `${to.col}-${to.fila}`;
    const newKey = `${from.col}-${from.fila}`;
    const piezaIdToRestore = lastPiezaId ?? pieceMapLocal.get(oldKey) ?? selectedPieceId;
    if (piezaIdToRestore !== null) {
      setPieceMapLocal((prevMap) => {
        const newMap = new Map(prevMap);
        newMap.delete(oldKey);
        newMap.set(newKey, piezaIdToRestore);
        console.log('🔄 pieceMapLocal actualizado al deshacer:', { piezaId: piezaIdToRestore, vuelveA: newKey, desdePos: oldKey });
        return newMap;
      });

      setPositionsList((prev) => prev.map((pos) => (pos === oldKey ? newKey : pos)));
      setSelectedPieceId(piezaIdToRestore);
    } else {
      console.warn('⚠️ No se pudo restaurar pieza_id al deshacer', { oldKey, newKey, last });
    }
    
    setSelectedCell({ fila: from.fila, col: from.col });
    setMoveHistory((prev) => prev.slice(0, prev.length - 1));
  }, [undoToken]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (undoToOriginalToken === 0) return;
    
    // Restaurar el mapa de piezas al estado original del turno (prioritario)
    if (turnStartPieceMap) {
      setPieceMapLocal(new Map(turnStartPieceMap));
      console.log('🔄 pieceMapLocal restaurado desde snapshot del turno:', turnStartPieceMap);
    }
    if (turnStartPositionsList) {
      setPositionsList([...turnStartPositionsList]);
      console.log('🔄 positionsList restaurado desde snapshot del turno:', turnStartPositionsList);
    }
    
    // Restaurar el tablero si hay initialBoardState
    if (initialBoardState) {
      setBoardPieces(initialBoardState.map((row) => [...row]));
    }
    
    setSelectedCell(null);
    setMoveHistory([]);
    setSelectedPieceId(null);
  }, [undoToOriginalToken]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!moveMade || moveHistory.length === 0) return;
    const lastMove = moveHistory[moveHistory.length - 1];
    const { from, to, piezaId: lastPiezaId = null } = lastMove;
    const newKey = `${to.col}-${to.fila}`;
    const originKey = `${from.col}-${from.fila}`;

    setPositionsList((prev) => prev.map((pos) => (pos === originKey ? newKey : pos)));

    // Actualizar pieceMapLocal preferentemente con lastPiezaId
    const idToMove = lastPiezaId ?? selectedPieceId ?? null;
    if (idToMove !== null) {
      setPieceMapLocal((prevMap) => {
        const newMap = new Map(prevMap);
        // Intentar eliminar por clave de origen; si no, por ID
        if (newMap.has(originKey)) {
          newMap.delete(originKey);
        } else {
          for (const [key, id] of newMap.entries()) {
            if (id === idToMove) {
              newMap.delete(key);
              break;
            }
          }
        }
        newMap.set(newKey, idToMove);
        console.log('🔄 pieceMapLocal actualizado:', { piezaId: idToMove, from: originKey, to: newKey });
        return newMap;
      });
    }
    setSelectedPieceId(null);
  }, [moveMade, moveHistory, selectedPieceId]);

  return (
    <div className="chinese-checkers-board">
      <div className="board-grid">
        {tablero.map((fila, filaIdx) => (
          <div key={filaIdx} className="board-row" style={{ justifyContent: 'center' }}>
            {fila.map((hueco, colIdx) => {
              const punta = hueco.punta;
              const occupant = boardPieces[filaIdx]?.[colIdx] ?? null;
              const hasPlayer = occupant !== null;
              const jugadorIndex = hasPlayer ? puntaToPlayerIndex[occupant] : null;
              const jugador =
                jugadorIndex !== null && jugadorIndex !== undefined
                  ? jugadoresConfig[jugadorIndex]
                  : null;
              const lightColor = punta !== null ? LIGHT_COLORS[punta] : '#f4ebd6ff';
              const backgroundColor = hasPlayer ? BOARD_COLORS[occupant] : (punta !== null ? lightColor : '#f4ebd6ff');
              const borderColor = hasPlayer ? BOARD_COLORS[occupant] : (punta !== null ? lightColor : '#e6dcc9');
              const isSelected = selectedCell && selectedCell.fila === filaIdx && selectedCell.col === colIdx;

              const onClick = () => {
                if (moveMade) {
                  if (hasPlayer) {
                    if (!lockedPiecePos || lockedPiecePos.fila !== filaIdx || lockedPiecePos.col !== colIdx) {
                      return;
                    }
                  }
                }

                if (hasPlayer) {
                  const ownerPunta = boardPieces[filaIdx][colIdx];
                  const ownerPlayerIndex = puntaToPlayerIndex[ownerPunta];
                  if (ownerPlayerIndex === currentPlayerIndex) {
                    setSelectedCell({ fila: filaIdx, col: colIdx });
                    const key = `${colIdx}-${filaIdx}`;
                    const fetchPieceId = async () => {
                      try {
                        const jugadorDb = dbJugadores[ownerPlayerIndex];
                        if (!jugadorDb?.id_jugador) {
                          console.warn('No se pudo obtener id_jugador para jugador en índice:', ownerPlayerIndex);
                          return;
                        }
                        
                        const res = await fetch(`http://localhost:8000/api/piezas/?partida_id=${partidaId}&jugador_id=${jugadorDb.id_jugador}`);
                        const piezas = await res.json();
                        
                        const pieza = piezas.find(p => p.posicion === key);
                        if (pieza) {
                          setSelectedPieceId(pieza.id_pieza);
                          console.log('🎯 Pieza seleccionada:', { posicion: key, piezaId: pieza.id_pieza, jugador: jugadorDb.id_jugador });
                        } else {
                          const altKey = `${filaIdx}-${colIdx}`;
                          let resolvedId = null;

                          const piezaAlt = (Array.isArray(piezas) ? piezas : []).find(p => p.posicion === altKey);
                          if (piezaAlt) {
                            resolvedId = piezaAlt.id_pieza;
                            console.info('✅ Pieza resuelta con clave alternativa (fila-col):', { posicion: altKey, piezaId: resolvedId });
                          }

                          if (!resolvedId) {
                            resolvedId = pieceMapLocal.get(key) ?? pieceMapLocal.get(altKey) ?? pieceByPos.get(key) ?? pieceByPos.get(altKey) ?? null;
                          }

                          // Fallback adicional: buscar en histórico de movimientos
                          if (!resolvedId && moveHistory.length > 0) {
                            const currentCellKey = `${colIdx}-${filaIdx}`;
                            for (let i = moveHistory.length - 1; i >= 0; i--) {
                              const m = moveHistory[i];
                              const endKey = `${m.to.col}-${m.to.fila}`;
                              const startKey = `${m.from.col}-${m.from.fila}`;
                              if ((endKey === currentCellKey || startKey === currentCellKey) && m.piezaId) {
                                resolvedId = m.piezaId;
                                console.info('✅ Pieza resuelta desde historial:', { posicion: currentCellKey, piezaId: resolvedId });
                                break;
                              }
                            }
                          }

                          if (resolvedId) {
                            setSelectedPieceId(resolvedId);
                            console.info('✅ Pieza resuelta por mapas locales:', { key, altKey, piezaId: resolvedId });
                          } else {
                            console.warn('No se encontró pieza en posición:', key, 'piezas disponibles:', positionsList);
                            setSelectedPieceId(null);
                          }
                        }
                      } catch (error) {
                        console.error('Error al obtener ID de pieza:', error);
                        setSelectedPieceId(null);
                      }
                    };
                    
                    fetchPieceId();
                  }
                } else if (selectedCell) {
                  const { fila, col } = selectedCell;
                  const movingPunta = boardPieces[fila]?.[col];
                  if (movingPunta !== null) {
                    const ownerPlayerIndex = puntaToPlayerIndex[movingPunta];
                    if (ownerPlayerIndex !== currentPlayerIndex) {
                      setSelectedCell(null);
                      return;
                    }
                    const originKey = `${col}-${fila}`;
                    const originKeyAlt = `${fila}-${col}`;
                    const piezaId = selectedPieceId ?? pieceMapLocal.get(originKey) ?? pieceMapLocal.get(originKeyAlt) ?? pieceByPos.get(originKey) ?? pieceByPos.get(originKeyAlt) ?? null;

                    const next = boardPieces.map((r) => [...r]);
                    next[filaIdx][colIdx] = next[fila][col];
                    next[fila][col] = null;
                    
                    if (!turnStartBoardState && !moveMade) {
                      setTurnStartBoardState(boardPieces);
                      // Guardar snapshot del mapa de piezas al inicio del turno
                      setTurnStartPieceMap(new Map(pieceMapLocal));
                      setTurnStartPositionsList([...positionsList]);
                      console.log('📸 Snapshot guardado al inicio del turno:', { pieceMapLocal, positionsList });
                    }
                    
                    setBoardPieces(next);
                    setMoveHistory((prev) => [...prev, { from: { fila, col }, to: { fila: filaIdx, col: colIdx }, occupant: movingPunta, piezaId }]);
                    setSelectedCell({ fila: filaIdx, col: colIdx });
                    if (onMove) {
                      console.log('➡️ Movimiento realizado desde Board:', { from: { fila, col }, to: { fila: filaIdx, col: colIdx }, occupant: movingPunta, boardState: next, pieza_id: piezaId });
                      setSelectedPieceId(piezaId);
                      onMove({ from: { fila, col }, to: { fila: filaIdx, col: colIdx }, occupant: movingPunta, boardState: boardPieces, pieza_id: piezaId });
                    }
                  } else {
                    setSelectedCell(null);
                  }
                }
              };

              return (
                <div
                  key={hueco.id}
                  className={`board-cell${isSelected ? ' selected' : ''}`}
                  style={{
                    backgroundColor,
                    borderColor,
                  }}
                  title={jugador ? `${jugador.nombre || 'IA'}` : 'Vacío'}
                  onClick={onClick}
                >
                  {jugador && (
                    <div className="cell-content">
                      <img
                        src={jugador.icono === 'Robot-icon.jpg'
                          ? require('./images/Robot-icon.jpg')
                          : require(`./images/icons/${jugador.icono}`)}
                        alt={jugador.nombre || 'IA'}
                        className="cell-icon"
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Board;
