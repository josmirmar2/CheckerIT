import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Game.css';
import { MUSIC_LIST, getRandomMusicIndex } from './musicList';
import Board from './Board';
import Victory from './Victory';

const PLAYER_COLORS = ['#FFFFFF', '#4444FF', '#44DD44', '#000000', '#FF4444', '#FFDD44'];

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

function Game() {
  const navigate = useNavigate();
  const location = useLocation();
  const [partida, setPartida] = useState(null);
  const [loading, setLoading] = useState(true);
  const [elapsed, setElapsed] = useState(0);
  const [showHelp, setShowHelp] = useState(false);
  const [isPlayingMusic, setIsPlayingMusic] = useState(false);
  const [currentMusicIndex, setCurrentMusicIndex] = useState(-1);
  const audioRef = useRef(null);
  const [currentPlayerIndex, setCurrentPlayerIndex] = useState(null);
  const [moveMade, setMoveMade] = useState(false);
  const [lockedPiecePos, setLockedPiecePos] = useState(null);
  const [originalPiecePos, setOriginalPiecePos] = useState(null);
  const [undoToOriginalToken, setUndoToOriginalToken] = useState(0);
  const [initialBoardState, setInitialBoardState] = useState(null);
  const [turnCount, setTurnCount] = useState(1);
  const [moveHistory, setMoveHistory] = useState([]);
  const [actualTurn, setActualTurn] = useState(null);
  const [pieceByPos, setPieceByPos] = useState(new Map());
  const [turnStartPieceByPos, setTurnStartPieceByPos] = useState(null);
  const [dbJugadores, setDbJugadores] = useState([]);
  const [isPaused, setIsPaused] = useState(false);
  const [showEndConfirm, setShowEndConfirm] = useState(false);
  const [showVictory, setShowVictory] = useState(false);
  const [victoryData, setVictoryData] = useState(null);

  const jugadoresConfig = useMemo(() => location.state?.jugadoresConfig || [], [location.state]);

  const handlePause = () => {
    setIsPaused(true);
    if (isPlayingMusic && audioRef.current) {
      audioRef.current.pause();
    }
  };

  const handleGoBack = () => {
    navigate('/');
  };

  const handleResume = () => {
    setIsPaused(false);
    if (isPlayingMusic && audioRef.current) {
      audioRef.current.play();
    }
  };

  const handleShowEndConfirm = () => {
    setShowEndConfirm(true);
  };

  const handleCancelEnd = () => {
    setShowEndConfirm(false);
  };

  const handleEndGame = async () => {
    try {
      setIsPlayingMusic(false);
      setCurrentMusicIndex(-1);
      
      if (audioRef.current) {
        try {
          audioRef.current.onerror = null; // Remover el listener de error
          audioRef.current.pause();
          audioRef.current.loop = false;
          audioRef.current.currentTime = 0;
          audioRef.current.removeAttribute('src');
        } catch {}
        audioRef.current = null;
      }

      const deleteUrl = `http://localhost:8000/api/partidas/${partida.id_partida}/`;
      const response = await fetch(deleteUrl, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        console.error('Error al eliminar partida:', response.status);
      }

      navigate('/');
    } catch (error) {
      console.error('Error en handleEndGame:', error);
      navigate('/');
    }
  };

  const checkVictory = async () => {
    try {
      // Obtener todas las piezas de la partida
      const res = await fetch(`http://localhost:8000/api/piezas/?partida_id=${partida.id_partida}`);
      const piezas = await res.json();

      if (!Array.isArray(piezas)) return;

      // Posiciones objetivo por punta (las de la punta contraria)
      const posicionesObjetivo = {
        0: ['3-13', '1-13', '0-14', '2-14', '1-15', '2-13', '0-13', '1-14', '0-15', '0-16'], // Punta 3
        1: ['9-9', '9-11', '10-11', '10-12', '12-12', '9-10', '10-10', '11-11', '9-12', '11-12'], // Punta 5
        2: ['0-9', '0-11', '1-11', '0-12', '2-12', '0-10', '1-10', '2-11', '1-12', '3-12'], // Punta 4
        3: ['0-0', '1-1', '0-3', '1-3', '2-3', '0-1', '0-2', '1-2', '2-2', '3-3'], // Punta 0
        4: ['12-4', '10-4', '11-5', '9-5', '9-6', '11-4', '9-4', '10-5', '10-6', '9-7'], // Punta 2
        5: ['0-4', '2-4', '0-5', '2-5', '1-6', '1-4', '3-4', '1-5', '0-6', '0-7'] // Punta 1
      };

      const activePuntas = getActivePuntas(jugadoresConfig.length);

      // Verificar cada jugador
      for (let i = 0; i < jugadoresConfig.length; i++) {
        const punta = activePuntas[i];
        const posicionesObjetivoJugador = posicionesObjetivo[punta];

        // Obtener todas las piezas de este jugador
        const piezasJugador = piezas.filter(p => {
          const tipoPartes = p.tipo.split('-');
          return tipoPartes.length > 0 && parseInt(tipoPartes[0]) === punta;
        });

        // Verificar si todas las piezas del jugador están en la punta contraria
        const todasEnObjetivo = piezasJugador.every(pieza => 
          posicionesObjetivoJugador.includes(pieza.posicion)
        );

        if (todasEnObjetivo && piezasJugador.length === 10) {
          // ¡Este jugador ha ganado!
          const ganador = {
            ...jugadoresConfig[i],
            punta: punta
          };

          const perdedores = jugadoresConfig
            .filter((_, idx) => idx !== i)
            .map((j, idx) => ({
              ...j,
              punta: activePuntas[idx < i ? idx : idx + 1]
            }));

          setVictoryData({
            ganador,
            perdedores,
            turnos: turnCount,
            tiempo: elapsed,
            totalJugadores: jugadoresConfig.length
          });

          setShowVictory(true);
          setIsPaused(true); // Pausar la partida

          // Pausar música
          if (isPlayingMusic && audioRef.current) {
            audioRef.current.pause();
          }

          return true;
        }
      }

      return false;
    } catch (error) {
      console.error('Error verificando victoria:', error);
      return false;
    }
  };

  useEffect(() => {
    if (partida?.id_partida) {
      fetchJugadoresPartida(partida.id_partida).then(dbJugadores => {
      setDbJugadores(dbJugadores);
        if (dbJugadores.length > 0) {
          const primerJugador = dbJugadores.find(j => j.numero === 1);
          if (primerJugador) {
            const idx = dbJugadores.findIndex(j => j.id_jugador === primerJugador.id_jugador);
            if (idx >= 0) {
              setCurrentPlayerIndex(idx);
            }
          }
        }
      });
      
      const embedded = Array.isArray(partida.turnos) ? partida.turnos : [];
      const current = embedded.find(t => !t.fin) || embedded[0] || null;
      if (current?.id_turno) {
        setActualTurn({ id_turno: current.id_turno, numero: current.numero });
      } else {
        fetchPrimerTurno(partida.id_partida).then(turno => {
          if (turno?.id_turno) setActualTurn({ id_turno: turno.id_turno, numero: turno.numero });
        });
      }
    }
  }, [partida]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (location.state?.partidaInicial) {
      setPartida(location.state.partidaInicial);
      setLoading(false);
    } else {
      handleGoBack();
    }
  }, [location.state]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (isPaused) return;
    const timerId = setInterval(() => {
      setElapsed((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timerId);
  }, [isPaused]);

  useEffect(() => {
    return () => {
      if (audioRef.current) {
        try {
          audioRef.current.pause();
          audioRef.current.loop = false;
          audioRef.current.currentTime = 0;
          audioRef.current.src = '';
          audioRef.current.load();
        } catch {}
      }
      setIsPlayingMusic(false);
    };
  }, []);

  const formatTime = (seconds) => {
    const m = String(Math.floor(seconds / 60)).padStart(2, '0');
    const s = String(seconds % 60).padStart(2, '0');
    return `${m}:${s}`;
  };

  const playRandomMusic = () => {
    if (MUSIC_LIST.length === 0) {
      console.warn('No hay canciones en la carpeta music/');
      stopMusic();
      return;
    }

    if (audioRef.current) {
      try {
        audioRef.current.pause();
        audioRef.current.loop = false;
        audioRef.current.currentTime = 0;
        audioRef.current.src = '';
        audioRef.current.load();
      } catch {}
      audioRef.current = null;
    }

    const newIndex = getRandomMusicIndex(currentMusicIndex);
    setCurrentMusicIndex(newIndex);

    try {
      const audio = new Audio(require(`./music/${MUSIC_LIST[newIndex]}`));
      audio.volume = 0.5;
      audio.loop = true;

      audio.onerror = () => {
        console.error(`Error al reproducir: ${MUSIC_LIST[newIndex]}`);
        stopMusic();
      };

      audio.play().catch((error) => {
        console.error('Error al iniciar reproducción:', error);
      });

      audioRef.current = audio;
    } catch (error) {
      console.error(`No se pudo cargar el archivo: ${MUSIC_LIST[newIndex]}`, error);
      stopMusic();
    }
  };

  const stopMusic = () => {
    if (audioRef.current) {
      try {
        audioRef.current.pause();
        audioRef.current.loop = false;
        audioRef.current.currentTime = 0;
        audioRef.current.src = '';
        audioRef.current.load();
      } catch {}
      audioRef.current = null;
    }
    setIsPlayingMusic(false);
    setCurrentMusicIndex(-1);
  };

  const toggleMusic = () => {
    if (isPlayingMusic) {
      stopMusic();
    } else {
      setIsPlayingMusic(true);
      playRandomMusic();
    }
  };

  const fetchPrimerTurno = async (partidaId) => {
    const res = await fetch(`http://localhost:8000/api/turnos/?partida_id=${partidaId}`);
    const data = await res.json();
    if (!Array.isArray(data) || data.length === 0) return null;
    const current = data.find(t => !t.fin);
    const first = current || data.sort((a,b) => (a.numero||0) - (b.numero||0))[0];
    return first || null;
  };

  const fetchJugadoresPartida = async (partidaId) => {
    try {
      const res = await fetch(`http://localhost:8000/api/participaciones/?partida_id=${partidaId}`);
      const data = await res.json();
      if (!Array.isArray(data) || data.length === 0) return [];
      const jugadores = data
        .sort((a, b) => (a.orden_participacion || 0) - (b.orden_participacion || 0))
        .map(p => ({
          id_jugador: p.jugador,
          numero: p.orden_participacion,
          nombre: p.jugador_nombre || 'Desconocido'
        }));
      return jugadores;
    } catch (e) {
      console.error('Error fetching jugadores:', e);
      return [];
    }
  };

  useEffect(() => {
    const loadPieces = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/piezas/');
        const data = await res.json();
        const todasLasPiezas = Array.isArray(data) ? data : [];
        const map = new Map();
        todasLasPiezas.forEach(p => map.set(p.posicion, p.id_pieza));
        setPieceByPos(map);
      } catch (e) {
        console.error('Error cargando piezas:', e);
      }
    };
    if (partida?.id_partida) loadPieces();
  }, [partida]); // eslint-disable-line react-hooks/exhaustive-deps

  const saveTurnToDatabase = async () => {
    try {
      const url = `http://localhost:8000/api/partidas/${partida.id_partida}/avanzar_turno/`;
      const currentJugadorId = dbJugadores[currentPlayerIndex]?.id_jugador;
      
      const currentJugadorNumero = dbJugadores[currentPlayerIndex]?.numero || 1;
      const maxNumero = Math.max(...dbJugadores.map(j => j.numero || 1));
      const nextNumero = currentJugadorNumero >= maxNumero ? 1 : currentJugadorNumero + 1;
      const nextJugador = dbJugadores.find(j => j.numero === nextNumero);
      const nextJugadorId = nextJugador?.id_jugador || dbJugadores[0]?.id_jugador;
      
      const oldTurn = {
        numero: actualTurn?.numero || 0,
        inicio: actualTurn?.inicio,
        final: new Date().toISOString(),
        jugador_id: currentJugadorId,
        partida_id: partida.id_partida,
      };
      const newTurnCreated = {
        numero: (actualTurn?.numero || 0) + 1,
        inicio: new Date().toISOString(),
        jugador_id: nextJugadorId,
        partida_id: partida.id_partida,
      };
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ oldTurn, newTurnCreated })
      });
      if (!res.ok) {
        console.error('Error al avanzar turno:', res.status);
        return null;
      }
      const data = await res.json();
      const nuevoTurno = data?.nuevo_turno || data;
      if (nuevoTurno?.id_turno) {
        setActualTurn({ id_turno: nuevoTurno.id_turno, numero: nuevoTurno.numero, inicio: nuevoTurno.inicio });
        const nextPlayerIdx = dbJugadores.findIndex(j => j.numero === nextNumero);
        if (nextPlayerIdx >= 0) setCurrentPlayerIndex(nextPlayerIdx);
      }
      return nuevoTurno;
    } catch (error) {
      console.error('Error en saveTurnToDatabase:', error);
      return null;
    }
  };

  const saveMoveToDatabase = async (moves) => {
    try {
      const jugadorId = dbJugadores[currentPlayerIndex]?.id_jugador;
      const turnoId = actualTurn?.id_turno;
      const movimientos = moves
        .map(m => ({
          origen: `${m.from.col}-${m.from.fila}`,
          destino: `${m.to.col}-${m.to.fila}`,
          partida_id: partida.id_partida,
          jugador_id: jugadorId,
          turno_id: turnoId,
          pieza_id: m.pieza_id,
        }))
        .filter((m, idx) => {
          const completo = m.origen && m.destino && m.partida_id && m.jugador_id && m.turno_id && m.pieza_id;
          if (!completo) {
            console.warn('Movimiento incompleto, no se enviará', { idx, m });
          }
          return completo;
        });

      if (movimientos.length === 0) {
        console.warn('No hay movimientos completos para registrar');
        return;
      }
      console.log('Guardando movimientos IMP:', movimientos);
      const url = `http://localhost:8000/api/partidas/${partida.id_partida}/registrar_movimientos/`; //TODO
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ movimientos })
      });
      if (!response.ok) {
        const text = await response.text();
        console.error('Error al guardar movimientos:', response.status, text);
      }
    } catch (error) {
      console.error('Error en saveMoveToDatabase:', error);
    }
  };

  const handleBoardMove = (move) => {
    setMoveMade(true);
    setLockedPiecePos(move.to);
    if (!originalPiecePos) {
      setOriginalPiecePos(move.from);
    }
    if (!initialBoardState && move.boardState) {
      setInitialBoardState(move.boardState);
    }
    if (!turnStartPieceByPos) {
      setTurnStartPieceByPos(new Map(pieceByPos));
      console.log('📸 Snapshot de pieceByPos guardado en Game.js:', pieceByPos);
    }
    const origenKey = `${move.from.col}-${move.from.fila}`;
    const piezaId = move.pieza_id ?? pieceByPos.get(origenKey) ?? null;

    if (!piezaId) {
      console.warn('Movimiento sin pieza_id; se omite registro de movimiento', { move, origenKey });
    } else {
      const nextMap = new Map(pieceByPos);
      nextMap.delete(origenKey);
      nextMap.set(`${move.to.col}-${move.to.fila}`, piezaId);
      setPieceByPos(nextMap);
    }
    setMoveHistory((prev) => [...prev, {
      from: move.from,
      to: move.to,
      occupant: move.occupant,
      pieza_id: piezaId,
    }]);
  };

  const undoMove = () => {
    if (!moveMade) return;
    setUndoToOriginalToken((prev) => prev + 1);
    setMoveMade(false);
    setLockedPiecePos(null);
    setOriginalPiecePos(null);
    setMoveHistory([]);
    
    if (turnStartPieceByPos) {
      setPieceByPos(new Map(turnStartPieceByPos));
      console.log('🔄 pieceByPos restaurado desde snapshot en Game.js:', turnStartPieceByPos);
    }
  };

  const continueTurn = async () => {
    if (!moveMade) return;
    if (moveHistory.length > 0) {
      await saveMoveToDatabase(moveHistory);
    }
    
    // Verificar victoria después de guardar los movimientos
    const hasWinner = await checkVictory();
    if (hasWinner) {
      return; // Si hay ganador, detener el flujo
    }

    await saveTurnToDatabase();
    setTurnCount((prev) => prev + 1);
    setMoveMade(false);
    setLockedPiecePos(null);
    setOriginalPiecePos(null);
    setInitialBoardState(null);
    setMoveHistory([]);
    setTurnStartPieceByPos(null);
  };

  const passTurn = async () => {
    await saveTurnToDatabase();
    setTurnCount((prev) => prev + 1);
    setMoveMade(false);
    setLockedPiecePos(null);
    setOriginalPiecePos(null);
    setInitialBoardState(null);
    setMoveHistory([]);
    setTurnStartPieceByPos(null);
  };

  const getIconSrc = (iconName) => {
    try {
      if (iconName === 'Robot-icon.jpg') {
        return require('./images/Robot-icon.jpg');
      }
      return require(`./images/icons/${iconName}`);
    } catch (err) {
      return '';
    }
  };

  if (loading) {
    return (
      <div className="game-container">
        <div className="loading">Cargando partida...</div>
      </div>
    );
  }

  return (
    <div className="game-container">
      <div className="game-layout">
        <aside className="turns-panel">
          <h3>Turno</h3>
          <div className="turn-counter">Actual: {turnCount}</div>
          <div className="turns-list">
            {jugadoresConfig.length === 0 && (
              <p className="turns-empty">Sin datos de jugadores</p>
            )}
            {jugadoresConfig.map((jugador, idx) => {
              const isCurrent = idx === currentPlayerIndex;
              const activePuntas = getActivePuntas(jugadoresConfig.length);
              const punta = activePuntas[idx];
              const colorHex = PLAYER_COLORS[punta];
              return (
                <div
                  key={`${jugador.nombre || 'IA'}-${idx}`}
                  className={`turn-card ${isCurrent ? 'current' : ''}`}
                >
                  <div className="turn-avatar">
                    <img src={getIconSrc(jugador.icono)} alt={jugador.nombre || 'IA'} />
                  </div>
                  <div className="turn-info">
                    <div className="turn-color-dot" style={{ backgroundColor: colorHex }} />
                    <span className="turn-name">{jugador.nombre || `IA ${jugador.dificultad}`}</span>
                    {isCurrent && <span className="turn-indicator">Turno actual</span>}
                  </div>
                </div>
              );
            })}
          </div>
        </aside>

        <main className="board-area">
          <div className="board-top">
            <button className="compact-button" onClick={toggleMusic}>
              <i className={`fas ${isPlayingMusic ? 'fa-volume-high' : 'fa-volume-xmark'}`}></i>
            </button>
            <div className="timer">⏱ {formatTime(elapsed)}</div>
            <button className="compact-button" onClick={handlePause}>
              <i className="fas fa-home"></i>
            </button>
          </div>

          <div className="board-container">
            <Board
              jugadoresConfig={jugadoresConfig}
              dbJugadores={dbJugadores}
              currentPlayerIndex={currentPlayerIndex}
              partidaId={partida?.id_partida}
              onMove={handleBoardMove}
              moveMade={moveMade}
              lockedPiecePos={lockedPiecePos}
              undoToOriginalToken={undoToOriginalToken}
              originalPiecePos={originalPiecePos}
              initialBoardState={initialBoardState}
              pieceByPos={pieceByPos}
            />
          </div>

          <div className="game-controls">
            {partida?.estado === 'EN_CURSO' && (
              <>
                {moveMade ? (
                  <>
                    <button className="control-button" onClick={continueTurn}>Continuar</button>
                    <button className="control-button" onClick={undoMove}>Deshacer</button>
                  </>
                ) : (
                  <button className="control-button" onClick={passTurn}>Pasar Turno</button>
                )}
              </>
            )}
          </div>
        </main>

        <aside className={`help-panel ${showHelp ? 'open' : ''}`}>
          <button className="help-toggle" onClick={() => setShowHelp((prev) => !prev)}>
            {showHelp ? 'Cerrar Ayuda' : 'Abrir Ayuda'}
          </button>
          {showHelp && (
            <div className="help-content">
              <h3>Asistente</h3>
              <p>Chatbot de ayuda</p>
              <p className="help-placeholder">Aquí aparecerán sugerencias y respuestas.</p>
            </div>
          )}
        </aside>
      </div>

      {isPaused && (
        <div className="pause-overlay">
          <div className="pause-dialog">
            <h2>Juego Pausado</h2>
            <div className="pause-buttons">
              <button className="pause-button resume-button" onClick={handleResume}>
                <i className="fas fa-play"></i>
                Reanudar
              </button>
              <button className="pause-button end-button" onClick={handleShowEndConfirm}>
                <i className="fas fa-stop"></i>
                Finalizar
              </button>
            </div>
          </div>
        </div>
      )}

      {showEndConfirm && (
        <div className="confirm-overlay">
          <div className="confirm-dialog">
            <h2>Finalizar Partida</h2>
            <p className="confirm-question">
              ¿Seguro que quieres finalizarla antes de tiempo?
            </p>
            <p className="confirm-warning">
              Esta acción no se podrá deshacer. Perderás el progreso que has conseguido en la partida
            </p>
            <div className="confirm-buttons">
              <button className="confirm-button cancel-button" onClick={handleCancelEnd}>
                Cancelar
              </button>
              <button className="confirm-button confirm-end-button" onClick={handleEndGame}>
                Volver al inicio
              </button>
            </div>
          </div>
        </div>
      )}

      {showVictory && victoryData && (
        <Victory
          ganador={victoryData.ganador}
          perdedores={victoryData.perdedores}
          turnos={victoryData.turnos}
          tiempo={victoryData.tiempo}
          totalJugadores={victoryData.totalJugadores}
          onVolverInicio={handleEndGame}
        />
      )}
    </div>
  );
}

export default Game;
