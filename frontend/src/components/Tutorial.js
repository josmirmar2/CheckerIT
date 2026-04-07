import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Tutorial.css';

function Tutorial() {
  const navigate = useNavigate();

  const handleGoBack = () => {
    navigate('/');
  };

  return (
    <div className="tutorial-container">
      <div className="tutorial-content">
        <button className="back-button" onClick={handleGoBack}>
          ← Volver al Inicio
        </button>
        
        <h1 className="tutorial-title">Tutorial - Damas Chinas</h1>
        
        <div className="tutorial-sections">
          <section className="tutorial-section">
            <h2>🎯 Objetivo del Juego</h2>
            <p>
              El objetivo de las Damas Chinas es ser el primero en mover todas 
              tus piezas desde tu zona inicial hasta la zona objetivo opuesta 
              del tablero estrellado.
            </p>
          </section>

          <section className="tutorial-section">
            <h2>📋 Reglas Básicas</h2>
            <ul>
              <li>
                <strong>Movimiento Simple:</strong> Puedes mover una pieza a 
                cualquier casilla adyacente vacía.
              </li>
              <li>
                <strong>Saltos:</strong> Puedes saltar sobre una pieza (tuya o 
                del oponente) a una casilla vacía al otro lado.
              </li>
              <li>
                <strong>Saltos Múltiples:</strong> Si después de un salto puedes 
                realizar otro, puedes continuar saltando en la misma ronda.
              </li>
              <li>
                <strong>No se Captura:</strong> A diferencia de las damas 
                tradicionales, en las Damas Chinas NO se capturan piezas.
              </li>
            </ul>
          </section>

          <section className="tutorial-section">
            <h2>🎮 Cómo Jugar</h2>
            <ol>
              <li>Selecciona una de tus piezas haciendo clic sobre ella</li>
              <li>Haz clic en la casilla destino donde quieres mover la pieza</li>
              <li>Si el movimiento es válido, la pieza se moverá automáticamente</li>
              <li>La ronda pasa al siguiente jugador</li>
            </ol>
          </section>

          <section className="tutorial-section">
            <h2>🏆 Ganar la Partida</h2>
            <p>
              El primer jugador que consiga colocar todas sus piezas en la 
              zona objetivo opuesta del tablero gana la partida.
            </p>
          </section>

          <section className="tutorial-section">
            <h2>💡 Consejos Estratégicos</h2>
            <ul>
              <li>Planifica cadenas de saltos para avanzar más rápido</li>
              <li>No dejes piezas atrás, intenta moverlas todas juntas</li>
              <li>Usa las piezas del oponente como trampolines para saltar</li>
              <li>Controla el centro del tablero para tener más opciones</li>
            </ul>
          </section>
        </div>

        <div className="tutorial-actions">
          <button className="start-playing-button" onClick={() => navigate('/game')}>
            ¡Empezar a Jugar!
          </button>
        </div>
      </div>
    </div>
  );
}

export default Tutorial;
