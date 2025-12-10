import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Players.css';

const API_URL = 'http://localhost:8000/api';

function Players() {
  const navigate = useNavigate();
  const [numeroJugadores, setNumeroJugadores] = useState(2);
  const [jugadores, setJugadores] = useState(['', '']);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleNumeroJugadoresChange = (num) => {
    if (num >= 2 && num <= 6) {
      setNumeroJugadores(num);
      const newJugadores = Array(num).fill('');
      for (let i = 0; i < Math.min(jugadores.length, num); i++) {
        newJugadores[i] = jugadores[i];
      }
      setJugadores(newJugadores);
    }
  };

  const handleJugadorChange = (index, valor) => {
    const newJugadores = [...jugadores];
    newJugadores[index] = valor;
    setJugadores(newJugadores);
  };

  const validarJugadores = () => {
    // Verificar que todos los jugadores tengan nombre
    if (jugadores.some(j => j.trim() === '')) {
      setError('Todos los jugadores deben tener un nombre');
      return false;
    }
    
    // Verificar que no haya nombres duplicados
    const nombres = jugadores.map(j => j.trim().toLowerCase());
    if (new Set(nombres).size !== nombres.length) {
      setError('Los nombres de los jugadores no pueden ser duplicados');
      return false;
    }

    return true;
  };

  const handleStartGame = async () => {
    if (!validarJugadores()) {
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Preparar los datos para la API
      const datos = {
        numero_jugadores: numeroJugadores,
      };

      // Agregar los nombres de los jugadores dinámicamente
      jugadores.forEach((nombre, index) => {
        datos[`nombre_jugador${index + 1}`] = nombre;
      });

      const response = await axios.post(`${API_URL}/partidas/start_game/`, datos);
      
      // Pasar la información de la partida como estado de navegación
      navigate('/game', { state: { partidaInicial: response.data } });
    } catch (err) {
      console.error('Error al crear partida:', err);
      setError('Error al crear la partida. Verifica que el servidor esté activo.');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    navigate('/home');
  };

  return (
    <div className="players-container">
      <div className="players-content">
        <h1 className="game-title">CheckerIT</h1>
        <p className="game-subtitle">Configurar Jugadores</p>

        <div className="setup-section">
          {/* Selector de número de jugadores */}
          <div className="player-count-section">
            <label>Número de Jugadores:</label>
            <div className="player-count-buttons">
              {[2, 3, 4, 5, 6].map(num => (
                <button
                  key={num}
                  className={`count-button ${numeroJugadores === num ? 'active' : ''}`}
                  onClick={() => handleNumeroJugadoresChange(num)}
                >
                  {num}
                </button>
              ))}
            </div>
          </div>

          {/* Entrada de nombres de jugadores */}
          <div className="players-input-section">
            <label className="section-label">Nombres de Jugadores:</label>
            <div className="players-list">
              {jugadores.map((nombre, index) => (
                <div key={index} className="player-input-group">
                  <label htmlFor={`jugador-${index}`}>
                    Jugador {index + 1}:
                  </label>
                  <input
                    id={`jugador-${index}`}
                    type="text"
                    placeholder={`Nombre del Jugador ${index + 1}`}
                    value={nombre}
                    onChange={(e) => handleJugadorChange(index, e.target.value)}
                    maxLength="20"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Mensaje de error */}
          {error && (
            <div className="error-message">
              ⚠️ {error}
            </div>
          )}

          {/* Botones de acción */}
          <div className="button-container">
            <button
              className="menu-button start-button"
              onClick={handleStartGame}
              disabled={loading}
            >
              {loading ? 'Creando partida...' : 'Empezar Partida'}
            </button>

            <button
              className="menu-button back-button"
              onClick={handleBack}
              disabled={loading}
            >
              Volver Atrás
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Players;
