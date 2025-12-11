import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Players.css';

const API_URL = 'http://localhost:8000/api';

const importarIcono = (nombreIcono) => {
  try {
    if (nombreIcono === 'Robot-icon.jpg') {
      return require('./images/Robot-icon.jpg');
    }
    return require(`./images/icons/${nombreIcono}`);
  } catch (err) {
    console.error(`Error cargando icono: ${nombreIcono}`, err);
    return '';
  }
};

const ICONOS_DISPONIBLES = [
  'icono1.jpg', 'icono2.jpg', 'icono3.jpg', 'icono4.jpg',
  'icono5.jpg', 'icono6.jpg', 'icono7.jpg', 'icono8.jpg',
  'icono9.jpg', 'icono10.jpg', 'icono11.jpg', 'icono12.jpg'
];

const DIFICULTADES_IA = ['Fácil', 'Difícil'];

function Players() {
  const navigate = useNavigate();
  const [numeroJugadores, setNumeroJugadores] = useState(2);
  const [jugadores, setJugadores] = useState([
    { nombre: '', icono: 'icono1.jpg', tipo: 'humano', dificultad: 'Baja' },
    { nombre: '', icono: 'icono2.jpg', tipo: 'humano', dificultad: 'Baja' }
  ]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleNumeroJugadoresChange = (num) => {
    if (num >= 2 && num <= 6) {
      setNumeroJugadores(num);
      const newJugadores = Array(num).fill(null).map((_, index) => {
        if (index < jugadores.length) {
          return jugadores[index];
        }
        return {
          nombre: '',
          icono: ICONOS_DISPONIBLES[index % ICONOS_DISPONIBLES.length],
          tipo: 'humano',
          dificultad: 'Media'
        };
      });
      setJugadores(newJugadores);
    }
  };

  const handleJugadorChange = (index, campo, valor) => {
    const newJugadores = [...jugadores];
    newJugadores[index] = { ...newJugadores[index], [campo]: valor };
    
    if (campo === 'tipo' && valor === 'ia') {
      newJugadores[index].icono = 'Robot-icon.jpg';
      newJugadores[index].nombre = '';
    }
    if (campo === 'tipo' && valor === 'humano' && newJugadores[index].icono === 'Robot-icon.jpg') {
      newJugadores[index].icono = ICONOS_DISPONIBLES[index % ICONOS_DISPONIBLES.length];
    }
    
    setJugadores(newJugadores);
  };

  const validarJugadores = () => {
    const jugadoresHumanos = jugadores.filter(j => j.tipo === 'humano');
    if (jugadoresHumanos.some(j => j.nombre.trim() === '')) {
      setError('Todos los jugadores humanos deben tener un nombre');
      return false;
    }
    
    const nombresHumanos = jugadoresHumanos.map(j => j.nombre.trim().toLowerCase());
    if (new Set(nombresHumanos).size !== nombresHumanos.length) {
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
      const datos = {
        numero_jugadores: numeroJugadores,
      };

      jugadores.forEach((jugador, index) => {
        if (jugador.tipo === 'humano') {
          datos[`nombre_jugador${index + 1}`] = jugador.nombre;
        } else {
          datos[`nombre_jugador${index + 1}`] = `IA ${jugador.dificultad} ${index + 1}`;
        }
      });

      const response = await axios.post(`${API_URL}/partidas/start_game/`, datos);
      
      navigate('/game', { state: { partidaInicial: response.data, jugadoresConfig: jugadores } });
    } catch (err) {
      console.error('Error al crear partida:', err);
      setError('Error al crear la partida. Verifica que el servidor esté activo.');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    navigate('/');
  };

  return (
    <div className="players-container">
      <div className="players-content">
        <h1 className="game-title">CheckerIT</h1>
        <p className="game-subtitle">Selecciona y configura los jugadores antes de jugar</p>

        <div className="setup-section">
          <div className="player-count-section">
            <label>Número de Jugadores:</label>
            <div className="player-count-buttons">
              {[2, 3, 4, 6].map(num => (
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

          <div className="players-input-section">
            <label className="section-label">Configura los jugadores:</label>
            <div className="players-grid" data-players={numeroJugadores}>
              {jugadores.map((jugador, index) => (
                <div key={index} className="player-card">
                  <div className="player-card-header">
                    <h3>Jugador {index + 1}</h3>
                  </div>

                  <div className="player-icon-section">
                    <label>Icono:</label>
                    <div className="icon-preview">
                      <img
                        src={importarIcono(jugador.icono)}
                        alt={`Icono Jugador ${index + 1}`}
                      />
                    </div>
                    {jugador.tipo === 'humano' && (
                      <div className="icon-grid">
                        {ICONOS_DISPONIBLES.map(icono => (
                          <div
                            key={icono}
                            className={`icon-option ${jugador.icono === icono ? 'selected' : ''}`}
                            onClick={() => handleJugadorChange(index, 'icono', icono)}
                          >
                            <img
                              src={importarIcono(icono)}
                              alt={icono}
                            />
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="player-type-section">
                    <label>Tipo:</label>
                    <div className="type-buttons">
                      <button
                        className={`type-button ${jugador.tipo === 'humano' ? 'active' : ''}`}
                        onClick={() => handleJugadorChange(index, 'tipo', 'humano')}
                      >
                        Humano
                      </button>
                      <button
                        className={`type-button ${jugador.tipo === 'ia' ? 'active' : ''}`}
                        onClick={() => handleJugadorChange(index, 'tipo', 'ia')}
                      >
                        IA
                      </button>
                    </div>
                  </div>

                  {jugador.tipo === 'humano' && (
                    <div className="player-name-section">
                      <label htmlFor={`nombre-${index}`}>Nombre:</label>
                      <input
                        id={`nombre-${index}`}
                        type="text"
                        placeholder="Introduce tu nombre"
                        value={jugador.nombre}
                        onChange={(e) => handleJugadorChange(index, 'nombre', e.target.value)}
                        maxLength="20"
                      />
                    </div>
                  )}

                  {jugador.tipo === 'ia' && (
                    <div className="player-difficulty-section">
                      <label>Dificultad:</label>
                      <select
                        className="difficulty-selector"
                        value={jugador.dificultad}
                        onChange={(e) => handleJugadorChange(index, 'dificultad', e.target.value)}
                      >
                        {DIFICULTADES_IA.map(dif => (
                          <option key={dif} value={dif}>{dif}</option>
                        ))}
                      </select>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {error && (
            <div className="error-message">
              ⚠️ {error}
            </div>
          )}

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
