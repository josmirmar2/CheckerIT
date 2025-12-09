import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Game.css';

const API_URL = 'http://localhost:8000/api';

function Game() {
  const navigate = useNavigate();
  const [partida, setPartida] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    startNewGame();
  }, []);

  const startNewGame = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${API_URL}/partidas/start_game/`, {
        numero_jugadores: 2,
        nombre_jugador1: 'Jugador 1',
        nombre_jugador2: 'Jugador 2',
        jugador2_ia: false
      });
      setPartida(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error al crear la partida:', error);
      setError('No se pudo conectar con el servidor. Asegúrate de que el backend esté ejecutándose.');
      setLoading(false);
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
        <div className="error-message">
          <p>{error}</p>
          <button className="control-button" onClick={startNewGame}>
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="game-container">
      <div className="game-header">
        <button className="back-button" onClick={handleGoBack}>
          ← Volver al Inicio
        </button>
        <h1>CheckerIT - Partida en Curso</h1>
      </div>

      <div className="game-content">
        <div className="game-info">
          <div className="info-card">
            <h3>Partida</h3>
            <p className="game-id">{partida?.id_partida}</p>
          </div>
          <div className="info-card">
            <h3>Turno Actual</h3>
            <p className="current-player">{partida?.jugador_actual_nombre || 'Cargando...'}</p>
          </div>
          <div className="info-card">
            <h3>Estado</h3>
            <p>{getEstadoTexto(partida?.estado)}</p>
          </div>
          <div className="info-card">
            <h3>Jugadores</h3>
            <p>{partida?.numero_jugadores}</p>
          </div>
        </div>

        <div className="board-container">
          <div className="board-placeholder">
            <p>Tablero de Damas Chinas</p>
            <p className="board-note">
              (Aquí se implementará el tablero del juego)
            </p>
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
              <button className="control-button end-game-button" onClick={handleEndGame}>
                Finalizar Partida
              </button>
            </>
          )}
          <button className="control-button new-game-button" onClick={startNewGame}>
            Nueva Partida
          </button>
        </div>
      </div>
    </div>
  );
}

export default Game;
