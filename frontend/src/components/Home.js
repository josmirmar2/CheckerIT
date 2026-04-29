import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './Home.css';

function Home() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();

  const resolvedLanguage = (i18n.resolvedLanguage || i18n.language || 'es').split('-')[0];
  const currentLanguage = resolvedLanguage === 'en' ? 'en' : 'es';

  const handleLanguageChange = (e) => {
    const next = String(e.target.value || '').toLowerCase();
    void i18n.changeLanguage(next === 'en' ? 'en' : 'es');
  };

  const handleStartGame = () => {
    navigate('/players');
  };

  const handleTutorial = () => {
    navigate('/tutorial');
  };

  return (
    <div className="home-container">
      <div className="home-content">
        <h1 className="game-title">CheckerIT</h1>
        <p className="game-subtitle">{t('home.subtitle')}</p>

        <div className="button-container">
          <button 
            className="menu-button tutorial-button" 
            onClick={handleTutorial}
          >
            {t('home.tutorial')}
          </button>
          <button 
            className="menu-button start-button" 
            onClick={handleStartGame}
          >
            {t('home.newGame')}
          </button>
          <div className="language-selector">
          <label className="language-label" htmlFor="language-select">
            {t('common.language')}
          </label>
          <select
            id="language-select"
            className="language-select"
            value={currentLanguage}
            onChange={handleLanguageChange}
          >
            <option value="es">{t('common.languages.es')}</option>
            <option value="en">{t('common.languages.en')}</option>
          </select>
        </div>
        
        </div>
      </div>
    </div>
  );
}

export default Home;
