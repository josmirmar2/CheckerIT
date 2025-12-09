import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Home.css';

function Home() {
  const navigate = useNavigate();

  const handleStartGame = () => {
    navigate('/game');
  };

  const handleTutorial = () => {
    navigate('/tutorial');
  };

  return (
    <div className="home-container">
      <div className="home-content">
        <h1 className="game-title">CheckerIT</h1>
        <p className="game-subtitle">Damas Chinas</p>
        
        <div className="button-container">
          <button 
            className="menu-button start-button" 
            onClick={handleStartGame}
          >
            Empezar Partida
          </button>
          
          <button 
            className="menu-button tutorial-button" 
            onClick={handleTutorial}
          >
            Tutorial
          </button>
        </div>
      </div>
    </div>
  );
}

export default Home;
