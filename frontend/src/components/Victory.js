import React from 'react';
import './Victory.css';

const Victory = ({ ganador, perdedores, turnos, tiempo, totalJugadores, onVolverInicio }) => {
  const PLAYER_COLORS = ['#FFFFFF', '#4444FF', '#44DD44', '#000000', '#FF4444', '#FFDD44'];
  const COLOR_NAMES = ['Blanco', 'Azul', 'Verde', 'Negro', 'Rojo', 'Amarillo'];

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    if (hours > 0) {
      return `${hours}h ${mins}m ${secs}s`;
    }
    return `${mins}m ${secs}s`;
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

  return (
    <div className="victory-overlay">
      <div className="victory-container">
        <h1 className="victory-title">¡Partida Finalizada!</h1>
        
        <div className="winner-section">
          <div className="trophy-icon">🏆</div>
          <h2 className="winner-label">Ganador</h2>
          <div className="winner-card">
            <img 
              src={getIconSrc(ganador.icono)} 
              alt={ganador.nombre} 
              className="winner-avatar"
              style={{ borderColor: PLAYER_COLORS[ganador.punta] }}
            />
            <div className="winner-info">
              <h3 className="winner-name">{ganador.nombre}</h3>
            </div>
          </div>
        </div>

        <div className="stats-section">
          <h3 className="stats-title">Estadísticas de la Partida</h3>
          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-icon">🕐</span>
              <div className="stat-content">
                <span className="stat-label">Tiempo</span>
                <span className="stat-value">{formatTime(tiempo)}</span>
              </div>
            </div>
            <div className="stat-item stat-item-large">
              <div className="stat-content">
                <span className="stat-label">Número de Jugadores</span>
                <span className="stat-value">{totalJugadores}</span>
              </div>
            </div>
            <div className="stat-item">
              <span className="stat-icon">🎲</span>
              <div className="stat-content">
                <span className="stat-label">Turnos</span>
                <span className="stat-value">{turnos}</span>
              </div>
            </div>
          </div>
        </div>

        {perdedores.length > 0 && (
          <div className="losers-section">
            <h3 className="losers-title">Otros Jugadores</h3>
            <div className="losers-grid">
              {perdedores.map((jugador, idx) => (
                <div key={idx} className="loser-card">
                  <img 
                    src={getIconSrc(jugador.icono)} 
                    alt={jugador.nombre} 
                    className="loser-avatar" 
                    style={{ borderColor: PLAYER_COLORS[jugador.punta] }}
                  />
                  <span className="loser-name">{jugador.nombre}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <button className="victory-button" onClick={onVolverInicio}>
          <i className="fas fa-home"></i>
          Volver al Inicio
        </button>
      </div>
    </div>
  );
};

export default Victory;
