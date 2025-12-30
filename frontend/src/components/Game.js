import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Game.css';
import { MUSIC_LIST, getRandomMusicIndex } from './musicList';
import Board from './Board';

const PLAYER_COLORS = ['#FFFFFF', '#4444FF', '#44DD44', '#000000', '#FF4444', '#FFDD44'];

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

  const jugadoresConfig = useMemo(() => location.state?.jugadoresConfig || [], [location.state]);

  const handleGoBack = () => {
    navigate('/');
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
    const timerId = setInterval(() => {
      setElapsed((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timerId);
  }, []);

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
    // setLastMove(move);
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
    // setLastMove(null);
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
              return (
                <div
                  key={`${jugador.nombre || 'IA'}-${idx}`}
                  className={`turn-card ${isCurrent ? 'current' : ''}`}
                >
                  <div className="turn-avatar">
                    <img src={getIconSrc(jugador.icono)} alt={jugador.nombre || 'IA'} />
                  </div>
                  <div className="turn-info">
                    <div className="turn-color-dot" style={{ backgroundColor: PLAYER_COLORS[idx] }} />
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
            <button className="compact-button" onClick={handleGoBack}>
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
    </div>
  );
}

export default Game;
