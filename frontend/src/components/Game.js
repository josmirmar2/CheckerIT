import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import './Game.css';
import { MUSIC_LIST, getRandomMusicIndex } from './musicList';

const API_URL = 'http://localhost:8000/api';

function Game() {
  const navigate = useNavigate();
  const location = useLocation();
  const [partida, setPartida] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [elapsed, setElapsed] = useState(0);
  const [showHelp, setShowHelp] = useState(false);
  const [isPlayingMusic, setIsPlayingMusic] = useState(false);
  const [currentMusicIndex, setCurrentMusicIndex] = useState(-1);
  const [audioElement, setAudioElement] = useState(null);

  const jugadoresConfig = location.state?.jugadoresConfig || [];

  useEffect(() => {
    if (location.state?.partidaInicial) {
      setPartida(location.state.partidaInicial);
      setLoading(false);
    } else {
      handleGoBack();
    }
  }, [location.state]);

  useEffect(() => {
    const timerId = setInterval(() => {
      setElapsed((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timerId);
  }, []);

  useEffect(() => {
    return () => {
      // Limpiar al desmontar el componente
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
      console.warn('No hay canciones en la lista de reproducción');
      return;
    }

    const newIndex = getRandomMusicIndex(currentMusicIndex);
    setCurrentMusicIndex(newIndex);
  };

  const stopMusic = () => {
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

  const getImageSrc = (imageName) => {
    try {
      return require(`./images/${imageName}`);
    } catch (err) {
      console.error(`Error cargando imagen: ${imageName}`, err);
      return '';
    }
  };

  const handleEndTurn = async () => {
    if (!partida) return;
    
    try {
      const response = await axios.post(`${API_URL}/partidas/${partida.id_partida}/end_turn/`);
      setPartida(response.data);
    } catch (error) {
      console.error('Error al finalizar turno:', error);
    }
  };

  const handleEndGame = async () => {
    if (!partida) return;
    
    try {
      const response = await axios.post(`${API_URL}/partidas/${partida.id_partida}/end_game/`);
      setPartida(response.data);
    } catch (error) {
      console.error('Error al finalizar partida:', error);
    }
  };

  const handleGoBack = () => {
    navigate('/');
  };

  const getEstadoTexto = (estado) => {
    const estados = {
      'EN_CURSO': 'En curso',
      'PAUSADA': 'Pausada',
      'FINALIZADA': 'Finalizada'
    };
    return estados[estado] || estado;
  };

  if (loading) {
    return (
      <div className="game-container">
        <div className="loading">Cargando partida...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="game-container">
        <div className="game-header">
          <button className="back-button" onClick={handleGoBack}>
            ← Volver al Inicio
          </button>
          <h1>CheckerIT</h1>
        </div>
      </div>
    );
  }

  return (
    <div className="game-container">
      <div className="game-layout">
        <aside className="turns-panel">
          <h3>Turnos</h3>
          <div className="turns-list">
            {jugadoresConfig.length === 0 && (
              <p className="turns-empty">Sin datos de jugadores</p>
            )}
            {jugadoresConfig.map((jugador, idx) => {
              const isCurrent = partida?.jugador_actual_nombre === jugador.nombre;
              return (
                <div
                  key={`${jugador.nombre || 'IA'}-${idx}`}
                  className={`turn-card ${isCurrent ? 'current' : ''}`}
                >
                  <div className="turn-avatar">
                    <img src={getIconSrc(jugador.icono)} alt={jugador.nombre || 'IA'} />
                  </div>
                  <div className="turn-info">
                    <span className="turn-name">{jugador.nombre || `IA ${jugador.dificultad}`}</span>
                    <span className="turn-type">{jugador.tipo === 'humano' ? 'Humano' : `IA ${jugador.dificultad}`}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </aside>

        <main className="board-area">
          <div className="board-top">
            <button className="compact-button" onClick={toggleMusic}>
              <i className={`fas fa-volume-${isPlayingMusic ? 'up' : 'mute'}`}></i>
            </button>
            <div className="timer">⏱ {formatTime(elapsed)}</div>
            <button className="compact-button" onClick={handleGoBack}>
              <i className="fas fa-home"></i>
            </button>
          </div>

          <div className="board-container">
            <div className="board-placeholder">
              <p>Tablero de Damas Chinas</p>
              <p className="board-note">(Aquí se implementará el tablero del juego)</p>
              <p className="board-info">
                {partida?.turnos?.length > 0 && `Turno ${partida.turnos[partida.turnos.length - 1].numero}`}
              </p>
            </div>
          </div>

          <div className="game-controls">
            {partida?.estado === 'EN_CURSO' && (
              <>
                <button className="control-button" onClick={handleEndTurn}>
                  Finalizar Turno
                </button>
                <button className="control-button new-game-button" onClick={handleEndGame}>
                  Finalizar Partida
                </button>
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
              <p>Chatbot de ayuda (próximamente)</p>
              <p className="help-placeholder">Aquí aparecerán sugerencias y respuestas.</p>
            </div>
          )}
        </aside>
      </div>
      
      {isPlayingMusic && currentMusicIndex >= 0 && (
        <iframe
          id="youtube-player"
          style={{ display: 'none' }}
          src={`https://www.youtube.com/embed/${MUSIC_LIST[currentMusicIndex]}?autoplay=1&enablejsapi=1`}
          allow="autoplay; encrypted-media"
          onLoad={(e) => {
            const iframe = e.target;
            const checkEnded = setInterval(() => {
              iframe.contentWindow?.postMessage('{"event":"command","func":"getPlayerState","args":""}', '*');
            }, 1000);
            
            window.addEventListener('message', (event) => {
              if (event.data && typeof event.data === 'string') {
                try {
                  const data = JSON.parse(event.data);
                  if (data.info === 0) {
                    clearInterval(checkEnded);
                    playRandomMusic();
                  }
                } catch (e) {
                }
              }
            });
          }}
        />
      )}
    </div>
  );
}

export default Game;
