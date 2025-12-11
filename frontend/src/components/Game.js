import React, { useState, useEffect, useRef } from 'react';
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
  const [currentPlayerIndex, setCurrentPlayerIndex] = useState(0);
  const [moveMade, setMoveMade] = useState(false);
  // eslint-disable-next-line no-unused-vars
  const [lastMove, setLastMove] = useState(null);
  const [lockedPiecePos, setLockedPiecePos] = useState(null);
  const [originalPiecePos, setOriginalPiecePos] = useState(null);
  const [undoToOriginalToken, setUndoToOriginalToken] = useState(0);
  // eslint-disable-next-line no-unused-vars
  const [boardResetKey, setBoardResetKey] = useState(0);
  // eslint-disable-next-line no-unused-vars
  const [undoToken, setUndoToken] = useState(0);
  const [initialBoardState, setInitialBoardState] = useState(null);
  const [turnCount, setTurnCount] = useState(1);

  const jugadoresConfig = location.state?.jugadoresConfig || [];

  const handleGoBack = () => {
    navigate('/');
  };

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

  const handleBoardMove = (move) => {
    setLastMove(move);
    setMoveMade(true);
    setLockedPiecePos(move.to);
    if (!originalPiecePos) {
      setOriginalPiecePos(move.from);
    }
    if (!initialBoardState && move.boardState) {
      setInitialBoardState(move.boardState);
    }
  };

  const undoMove = () => {
    if (!moveMade) return;
    setUndoToOriginalToken((prev) => prev + 1);
    setLastMove(null);
    setMoveMade(false);
    setLockedPiecePos(null);
    setOriginalPiecePos(null);
  };

  const continueTurn = () => {
    if (!moveMade) return;
    setCurrentPlayerIndex((prev) => (prev + 1) % jugadoresConfig.length);
    setTurnCount((prev) => prev + 1);
    setLastMove(null);
    setMoveMade(false);
    setLockedPiecePos(null);
    setOriginalPiecePos(null);
    setInitialBoardState(null);
  };
  const passTurn = () => {
    setCurrentPlayerIndex((prev) => (prev + 1) % jugadoresConfig.length);
    setTurnCount((prev) => prev + 1);
    setLastMove(null);
    setMoveMade(false);
    setLockedPiecePos(null);
    setOriginalPiecePos(null);
    setInitialBoardState(null);
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
            <Board jugadoresConfig={jugadoresConfig} currentPlayerIndex={currentPlayerIndex} onMove={handleBoardMove} moveMade={moveMade} lockedPiecePos={lockedPiecePos} undoToken={undoToken} undoToOriginalToken={undoToOriginalToken} originalPiecePos={originalPiecePos} initialBoardState={initialBoardState} key={boardResetKey} />
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
