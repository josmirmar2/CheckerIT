import React, { useState, useEffect } from 'react';
import './Board.css';

const Board = ({ jugadoresConfig, currentPlayerIndex = 0, onMove = null, moveMade = false, lockedPiecePos = null, undoToken = 0, undoToOriginalToken = 0, originalPiecePos = null, initialBoardState = null }) => {
  const BOARD_COLORS = ['#FFFFFF', '#0000ffff', '#00ff00ff', '#000000', '#ff0000ff', '#ffbf00ff'];
  const LIGHT_COLORS = ['#ffffffcf', '#8888ffaf', '#9af89aab', '#666666af', '#ffa2a2a1', '#ffe988b6'];

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
    if (moveMade && !turnStartBoardState) {
      return;
    }
    if (!moveMade) {
      setTurnStartBoardState(null);
    }
  }, [moveMade]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (undoToken === 0 || moveHistory.length === 0) return;
    const last = moveHistory[moveHistory.length - 1];
    const { from, to } = last;
    const next = boardPieces.map((r) => [...r]);
    next[from.fila][from.col] = next[to.fila][to.col];
    next[to.fila][to.col] = null;
    setBoardPieces(next);
    setSelectedCell({ fila: from.fila, col: from.col });
    setMoveHistory((prev) => prev.slice(0, prev.length - 1));
  }, [undoToken]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (undoToOriginalToken === 0 || !initialBoardState) return;
    setBoardPieces(initialBoardState.map((row) => [...row]));
    setSelectedCell(null);
    setMoveHistory([]);
  }, [undoToOriginalToken]); // eslint-disable-line react-hooks/exhaustive-deps

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
                    const next = boardPieces.map((r) => [...r]);
                    next[filaIdx][colIdx] = next[fila][col];
                    next[fila][col] = null;
                    
                    if (!turnStartBoardState && !moveMade) {
                      setTurnStartBoardState(boardPieces);
                    }
                    
                    setBoardPieces(next);
                    setMoveHistory((prev) => [...prev, { from: { fila, col }, to: { fila: filaIdx, col: colIdx }, occupant: movingPunta }]);
                    setSelectedCell({ fila: filaIdx, col: colIdx });
                    if (onMove) {
                      onMove({ from: { fila, col }, to: { fila: filaIdx, col: colIdx }, occupant: movingPunta, boardState: boardPieces });
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
                        src={require(`./images/icons/${jugador.icono}`)} 
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
