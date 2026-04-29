import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './Tutorial.css';

import tutorialMoveSimple from './images/tutorial/Movimiento simple.gif';
import tutorialJump from './images/tutorial/Salto.gif';
import tutorialJumpChain from './images/tutorial/Salto en cadena.gif';

import tutorialBoard from './images/tutorial/Tablero.gif';
import tutorialPlayers from './images/tutorial/Jugadores.png';
import tutorialTurns from './images/tutorial/Turnos.gif';
import tutorialTimer from './images/tutorial/Temporizador.gif';
import tutorialMusic from './images/tutorial/Musica.gif';
import tutorialPause from './images/tutorial/Pausa.png';
import tutorialHome from './images/tutorial/Hogar.png';
import tutorialHelp from './images/tutorial/Ayuda.gif';
import tutorialPassRound from './images/tutorial/Pasar Ronda.gif';
import tutorialContinue from './images/tutorial/Cotinuar.gif';
import tutorialUndo from './images/tutorial/Deshacer.gif';

const API_URL = 'http://localhost:8000/api';
const TUTORIAL_CHAT_MAX_CHARS = 400;
const TUTORIAL_CHAT_TIMEOUT_MS = 12000;

function Tutorial() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [currentPage, setCurrentPage] = useState(0);
  const [startingMode, setStartingMode] = useState(null); // 'quick' | 'demo' | null
  const [startError, setStartError] = useState('');

  // Chatbot (antes de empezar partida)
  const [chatOpen, setChatOpen] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState([]); // { role: 'user'|'assistant', text: string }
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState('');
  const [chatbotId, setChatbotId] = useState(() => {
    try {
      const raw = window.sessionStorage.getItem('tutorial_chatbot_id');
      const n = raw ? Number(raw) : null;
      return Number.isFinite(n) ? n : null;
    } catch {
      return null;
    }
  });
  const chatEndRef = useRef(null);

  const handleGoBack = () => {
    navigate('/');
  };

  useEffect(() => {
    if (!chatbotId) return;
    try {
      window.sessionStorage.setItem('tutorial_chatbot_id', String(chatbotId));
    } catch {
      // ignore
    }
  }, [chatbotId]);

  useEffect(() => {
    if (!chatbotId) return;

    let cancelled = false;
    const loadHistory = async () => {
      try {
        const res = await fetch(`${API_URL}/chatbot/${encodeURIComponent(String(chatbotId))}/`);
        let data = null;
        try {
          data = await res.json();
        } catch {
          data = null;
        }

        if (res.status === 404) {
          if (!cancelled) {
            setChatbotId(null);
            setChatMessages([]);
          }
          try {
            window.sessionStorage.removeItem('tutorial_chatbot_id');
          } catch {
            // ignore
          }
          return;
        }

        if (!res.ok) {
          throw new Error(data?.error || t('tutorial.chat.errors.loadHistory'));
        }

        const convo = Array.isArray(data?.memoria?.conversaciones) ? data.memoria.conversaciones : [];
        const messages = [];
        for (const turn of convo) {
          if (turn?.mensaje) messages.push({ role: 'user', text: String(turn.mensaje) });
          if (turn?.respuesta) messages.push({ role: 'assistant', text: String(turn.respuesta) });
        }

        if (!cancelled) setChatMessages(messages);
      } catch {
        // Si falla, no bloquea el tutorial; el chat seguirá funcionando al enviar.
      }
    };

    loadHistory();
    return () => {
      cancelled = true;
    };
  }, [chatbotId, t]);

  useEffect(() => {
    if (!chatOpen) return;
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [chatMessages, chatOpen]);

  const ensureTutorialChatbotId = async () => {
    if (chatbotId) return chatbotId;

    const res = await fetch(`${API_URL}/chatbot/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });

    let data = null;
    try {
      data = await res.json();
    } catch {
      data = null;
    }

    if (!res.ok) {
      throw new Error(data?.error || t('tutorial.chat.errors.start'));
    }

    if (!data?.id) {
      throw new Error(t('tutorial.chat.errors.start'));
    }

    setChatbotId(data.id);
    return data.id;
  };

  const sendTutorialChatMessage = async (overrideMessage) => {
    const mensaje = String(overrideMessage ?? chatInput ?? '').trim();
    if (!mensaje || chatLoading) return;

    if (mensaje.length > TUTORIAL_CHAT_MAX_CHARS) {
      setChatError(t('tutorial.chat.errors.tooLong'));
      return;
    }

    setChatError('');
    setChatLoading(true);
    setChatMessages((prev) => [...prev, { role: 'user', text: mensaje }]);
    setChatInput('');

    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), TUTORIAL_CHAT_TIMEOUT_MS);

    try {
      let id = chatbotId;
      try {
        id = await ensureTutorialChatbotId();
      } catch {
        // Si falla la creación explícita, el endpoint de send_message crea/elige un chatbot igualmente.
        id = null;
      }

      const payload = { mensaje };
      if (id) payload.chatbot_id = id;

      const res = await fetch(`${API_URL}/chatbot/send_message/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        const serverMessage = String(data?.error || t('tutorial.chat.errors.send'));
        if (serverMessage.includes('demasiado largo')) {
          throw new Error(t('tutorial.chat.errors.tooLongShort'));
        }
        throw new Error(serverMessage || t('tutorial.chat.errors.send'));
      }

      if (data?.chatbot_id) {
        setChatbotId(data.chatbot_id);
      }

      setChatMessages((prev) => [...prev, { role: 'assistant', text: String(data?.respuesta || '') }]);
    } catch (err) {
      if (err?.name === 'AbortError') {
        setChatError(t('tutorial.chat.errors.timeout'));
      } else {
        setChatError(err?.message || t('tutorial.chat.errors.send'));
      }
    } finally {
      window.clearTimeout(timeoutId);
      setChatLoading(false);
    }
  };

  const handleChatKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void sendTutorialChatMessage();
    }
  };

  const startPresetGame = async (mode) => {
    if (startingMode) return;

    setStartError('');
    setStartingMode(mode);

    const jugadoresConfig =
      mode === 'quick'
        ? [
            { nombre: t('common.you'), icono: 'icono1.jpg', tipo: 'humano', dificultad: 'Baja', numero: 1 },
            { nombre: '', icono: 'Robot-icon.jpg', tipo: 'ia', dificultad: 'Fácil', numero: 2 },
          ]
        : [
            { nombre: '', icono: 'Robot-icon.jpg', tipo: 'ia', dificultad: 'Difícil', numero: 1 },
            { nombre: '', icono: 'Robot-icon.jpg', tipo: 'ia', dificultad: 'Difícil', numero: 2 },
          ];

    try {
      const res = await fetch(`${API_URL}/partidas/start_game/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ numero_jugadores: 2, jugadores: jugadoresConfig }),
      });

      let data = null;
      try {
        data = await res.json();
      } catch {
        data = null;
      }

      if (!res.ok) {
        const msg = data?.error || t('players.errors.createGame');
        throw new Error(msg);
      }

      navigate('/game', { state: { partidaInicial: data, jugadoresConfig } });
    } catch (err) {
      setStartError(err?.message || t('players.errors.createGame'));
      setStartingMode(null);
    }
  };

  const pages = [
    {
      key: 'objective-norms-win',
      sections: (
        <>
          <section className="tutorial-section">
            <h2>{t('tutorial.sections.objective.title')}</h2>
            <div className="tutorial-uiItem tutorial-uiItem--objective">
              <div className="tutorial-uiText">
                <p>
                  {t('tutorial.sections.objective.p1')}
                </p>
                <p>
                  {t('tutorial.sections.objective.p2')}
                </p>
              </div>
              <div className="tutorial-uiMedia">
                <img
                  className="tutorial-uiImage tutorial-uiImage--objective"
                  src={tutorialBoard}
                  alt={t('tutorial.sections.objective.boardAlt')}
                  loading="lazy"
                />
              </div>
            </div>
          </section>

          <section className="tutorial-section">
            <h2>{t('tutorial.sections.norms.title')}</h2>
            <ul>
              <li>
                {t('tutorial.sections.norms.item1')}
              </li>
              <li>
                {t('tutorial.sections.norms.item2')}
              </li>
              <li>
                {t('tutorial.sections.norms.item3')}
              </li>
              <li>
                {t('tutorial.sections.norms.item4')}
              </li>
              <li>
                {t('tutorial.sections.norms.item5')}
              </li>
              <li>
                {t('tutorial.sections.norms.item6')}
              </li>
              <li>
                {t('tutorial.sections.norms.item7')}
                <div className="tutorial-turnOrderVisual" aria-label={t('tutorial.sections.norms.turnOrderAria')}>
                  <div className="tutorial-turnOrderCard">
                    <img
                      className="tutorial-turnOrderImage"
                      src={tutorialPlayers}
                      alt={t('tutorial.sections.norms.playersAlt')}
                      loading="lazy"
                    />
                  </div>

                  <div className="tutorial-turnOrderArrow" aria-hidden="true">
                    →
                  </div>

                  <div className="tutorial-turnOrderCard">
                    <img
                      className="tutorial-turnOrderImage"
                      src={tutorialTurns}
                      alt={t('tutorial.sections.norms.turnsAlt')}
                      loading="lazy"
                    />
                  </div>
                </div>
              </li>
            </ul>
          </section>
        </>
      ),
    },
    {
      key: 'moves-and-strategy',
      sections: (
        <>
          <section className="tutorial-section">
            <h2>{t('tutorial.sections.moves.title')}</h2>
            <ul>
              <li>
                <strong>{t('tutorial.sections.moves.simpleLabel')}:</strong> {t('tutorial.sections.moves.simpleDesc')}
              </li>
              <li>
                <strong>{t('tutorial.sections.moves.jumpLabel')}:</strong> {t('tutorial.sections.moves.jumpDesc')}
              </li>
              <li>
                <strong>{t('tutorial.sections.moves.chainLabel')}:</strong> {t('tutorial.sections.moves.chainDesc')}
              </li>
            </ul>

            <div className="tutorial-moveGallery" aria-label={t('tutorial.sections.moves.galleryAria')}>
              <figure className="tutorial-moveCard">
                <img
                  className="tutorial-moveImage tutorial-moveImage--simple"
                  src={tutorialMoveSimple}
                  alt={t('tutorial.sections.moves.simpleAlt')}
                  loading="lazy"
                />
                <figcaption className="tutorial-moveCaption">
                  <strong>{t('tutorial.sections.moves.simpleLabel')}</strong>
                </figcaption>
              </figure>

              <figure className="tutorial-moveCard">
                <img
                  className="tutorial-moveImage tutorial-moveImage--jump"
                  src={tutorialJump}
                  alt={t('tutorial.sections.moves.jumpAlt')}
                  loading="lazy"
                />
                <figcaption className="tutorial-moveCaption">
                  <strong>{t('tutorial.sections.moves.jumpLabel')}</strong>
                </figcaption>
              </figure>

              <figure className="tutorial-moveCard">
                <img
                  className="tutorial-moveImage tutorial-moveImage--jumpChain"
                  src={tutorialJumpChain}
                  alt={t('tutorial.sections.moves.chainAlt')}
                  loading="lazy"
                />
                <figcaption className="tutorial-moveCaption">
                  <strong>{t('tutorial.sections.moves.chainLabel')}</strong>
                </figcaption>
              </figure>
            </div>
          </section>

          <section className="tutorial-section">
            <h2>{t('tutorial.sections.strategy.title')}</h2>
            <ul>
              <li>
                <strong>{t('tutorial.sections.strategy.item1b')}</strong> {t('tutorial.sections.strategy.item1')}
              </li>
              <li>
                <strong>{t('tutorial.sections.strategy.item2b')}</strong> {t('tutorial.sections.strategy.item2')}
              </li>
              <li>
                <strong>{t('tutorial.sections.strategy.item3b')}</strong> {t('tutorial.sections.strategy.item3')}
              </li>
              <li>
                <strong>{t('tutorial.sections.strategy.item4b')}</strong> {t('tutorial.sections.strategy.item4')}
              </li>
              <li>
                <strong>{t('tutorial.sections.strategy.item5b')}</strong> {t('tutorial.sections.strategy.item5')}
              </li>
              <li>
                <strong>{t('tutorial.sections.strategy.item6b')}</strong> {t('tutorial.sections.strategy.item6')}
              </li>
            </ul>
          </section>
        </>
      ),
    },
    {
      key: 'ui-elements',
      sections: (
        <section className="tutorial-section">
          <h2>{t('tutorial.sections.ui.title')}</h2>
          <p>{t('tutorial.sections.ui.intro')}</p>

          <div className="tutorial-uiList" aria-label={t('tutorial.sections.ui.listAria')}>
            <div className="tutorial-uiItem is-right tutorial-uiItem--board">
              <div className="tutorial-uiText">
                <h3>{t('tutorial.sections.ui.board.title')}</h3>
                <p>
                  {t('tutorial.sections.ui.board.p1')}
                </p>
                <p>
                  {t('tutorial.sections.ui.board.p2')}
                </p>
              </div>
              <div className="tutorial-uiMedia">
                <img
                  className="tutorial-uiImage tutorial-uiImage--board"
                  src={tutorialBoard}
                  alt={t('tutorial.sections.ui.board.alt')}
                  loading="lazy"
                />
              </div>
            </div>

            <div className="tutorial-uiItem is-left tutorial-uiItem--rounds">
              <div className="tutorial-uiText">
                <h3>{t('tutorial.sections.ui.rounds.title')}</h3>
                <p>
                  {t('tutorial.sections.ui.rounds.p1')}
                </p>
              </div>
              <div className="tutorial-uiMedia">
                <img
                  className="tutorial-uiImage tutorial-uiImage--turns"
                  src={tutorialTurns}
                  alt={t('tutorial.sections.ui.rounds.alt')}
                  loading="lazy"
                />
              </div>
            </div>

            <div className="tutorial-uiItem is-below">
              <div className="tutorial-uiText">
                <h3>{t('tutorial.sections.ui.timer.title')}</h3>
                <p>
                  {t('tutorial.sections.ui.timer.p1')}
                </p>
              </div>
              <div className="tutorial-uiMedia">
                <img
                  className="tutorial-uiImage tutorial-uiImage--timer"
                  src={tutorialTimer}
                  alt={t('tutorial.sections.ui.timer.alt')}
                  loading="lazy"
                />
              </div>
            </div>

            <div className="tutorial-uiDoubleRow" aria-label={t('tutorial.sections.ui.topControlsAria')}>
              <div className="tutorial-uiItem tutorial-uiItem--compact tutorial-uiItem--compactReverse">
                <div className="tutorial-uiMedia">
                  <img
                    className="tutorial-uiImage tutorial-uiImage--music"
                    src={tutorialMusic}
                    alt={t('tutorial.sections.ui.music.alt')}
                    loading="lazy"
                  />
                </div>
                <div className="tutorial-uiText">
                  <h3>{t('tutorial.sections.ui.music.title')}</h3>
                  <p>
                    {t('tutorial.sections.ui.music.p1')}
                  </p>
                </div>
              </div>

              <div className="tutorial-uiItem tutorial-uiItem--compact">
                <div className="tutorial-uiText">
                  <h3>{t('tutorial.sections.ui.pause.title')}</h3>
                  <p>
                    {t('tutorial.sections.ui.pause.p1')}
                  </p>
                </div>
                <div className="tutorial-uiMedia">
                  <img
                    className="tutorial-uiImage tutorial-uiImage--home"
                    src={tutorialHome}
                    alt={t('tutorial.sections.ui.pause.homeAlt')}
                    loading="lazy"
                  />
                </div>
              </div>
            </div>

            <div className="tutorial-uiItem is-left tutorial-uiItem--pauseResume">
              <div className="tutorial-uiText">
                <h3>{t('tutorial.sections.ui.pausePanel.title')}</h3>
                <p>
                  {t('tutorial.sections.ui.pausePanel.p1')}
                </p>
              </div>
              <div className="tutorial-uiMedia">
                <img
                  className="tutorial-uiImage tutorial-uiImage--pause"
                  src={tutorialPause}
                  alt={t('tutorial.sections.ui.pausePanel.alt')}
                  loading="lazy"
                />
              </div>
            </div>

            <div className="tutorial-uiTripleRow" aria-label={t('tutorial.sections.ui.turnActionsAria')}>
              <div className="tutorial-uiItem tutorial-uiItem--action">
                <div className="tutorial-uiText">
                  <h3>{t('tutorial.sections.ui.undo.title')}</h3>
                  <p>
                    {t('tutorial.sections.ui.undo.p1')}
                  </p>
                </div>
                <div className="tutorial-uiMedia">
                  <img
                    className="tutorial-uiImage tutorial-uiImage--undo"
                    src={tutorialUndo}
                    alt={t('tutorial.sections.ui.undo.alt')}
                    loading="lazy"
                  />
                </div>
              </div>

              <div className="tutorial-uiItem tutorial-uiItem--action">
                <div className="tutorial-uiText">
                  <h3>{t('tutorial.sections.ui.passRound.title')}</h3>
                  <p>
                    {t('tutorial.sections.ui.passRound.p1')}
                  </p>
                </div>
                <div className="tutorial-uiMedia">
                  <img
                    className="tutorial-uiImage tutorial-uiImage--passRound"
                    src={tutorialPassRound}
                    alt={t('tutorial.sections.ui.passRound.alt')}
                    loading="lazy"
                  />
                </div>
              </div>

              <div className="tutorial-uiItem tutorial-uiItem--action">
                <div className="tutorial-uiText">
                  <h3>{t('tutorial.sections.ui.continue.title')}</h3>
                  <p>
                    {t('tutorial.sections.ui.continue.p1')}
                  </p>
                </div>
                <div className="tutorial-uiMedia">
                  <img
                    className="tutorial-uiImage tutorial-uiImage--continue"
                    src={tutorialContinue}
                    alt={t('tutorial.sections.ui.continue.alt')}
                    loading="lazy"
                  />
                </div>
              </div>
            </div>

            <div className="tutorial-uiItem is-left tutorial-uiItem--help">
              <div className="tutorial-uiText">
                <h3>{t('tutorial.sections.ui.help.title')}</h3>
                <p>
                  {t('tutorial.sections.ui.help.p1')}
                </p>
                <p>
                  {t('tutorial.sections.ui.help.p2')}
                </p>
              </div>
              <div className="tutorial-uiMedia">
                <img
                  className="tutorial-uiImage tutorial-uiImage--help"
                  src={tutorialHelp}
                  alt={t('tutorial.sections.ui.help.alt')}
                  loading="lazy"
                />
              </div>
            </div>
          </div>
        </section>
      ),
    },
    {
      key: 'finished',
      sections: (
        <section className="tutorial-section">
          <h2>{t('tutorial.sections.finish.title')}</h2>
          <p>{t('tutorial.sections.finish.intro')}</p>
          <ul className="tutorial-finish-list">
            <li>
              <strong>{t('tutorial.sections.finish.quick.label')}</strong> {t('tutorial.sections.finish.quick.desc')}
            </li>
            <li>
              <strong>{t('tutorial.sections.finish.demo.label')}</strong> {t('tutorial.sections.finish.demo.desc')}
            </li>
            <li>
              <strong>{t('tutorial.sections.finish.chatbot.label')}</strong> {t('tutorial.sections.finish.chatbot.desc')}
            </li>
          </ul>

          <div className="tutorial-finish-actions" aria-label={t('tutorial.sections.finish.actionsAria')}>
            <button
              type="button"
              className="tutorial-finish-button tutorial-finish-primary"
              onClick={() => startPresetGame('quick')}
              disabled={startingMode !== null}
            >
              {startingMode === 'quick' ? t('tutorial.sections.finish.creatingGame') : t('tutorial.sections.finish.quickCta')}
            </button>

            <button
              type="button"
              className="tutorial-finish-button tutorial-finish-secondary"
              onClick={() => startPresetGame('demo')}
              disabled={startingMode !== null}
            >
              {startingMode === 'demo' ? t('tutorial.sections.finish.creatingDemo') : t('tutorial.sections.finish.demoCta')}
            </button>
          </div>

          {startError && (
            <div className="tutorial-finish-error" role="alert">
              {startError}
            </div>
          )}
        </section>
      ),
    },
  ];

  const totalPages = pages.length;
  const isFirstPage = currentPage === 0;
  const isLastPage = currentPage === totalPages - 1;

  useEffect(() => {
    if (!isLastPage) setChatOpen(false);
  }, [isLastPage]);

  const stepTitles = t('tutorial.steps.titles', { returnObjects: true });
  const stepSubtitles = t('tutorial.steps.subtitles', { returnObjects: true });

  const stepTitle = Array.isArray(stepTitles) ? (stepTitles[currentPage] || t('tutorial.steps.defaultTitle')) : t('tutorial.steps.defaultTitle');
  const stepSubtitle = Array.isArray(stepSubtitles) ? (stepSubtitles[currentPage] || '') : '';
  const progressPct = Math.max(0, Math.min(100, Math.round(((currentPage + 1) / totalPages) * 100)));

  const suggestedQuestions = t('tutorial.chat.suggestedQuestions', { returnObjects: true });
  const suggestedQuestionList = Array.isArray(suggestedQuestions) ? suggestedQuestions : [];

  const goPrev = () => setCurrentPage((p) => Math.max(0, p - 1));
  const goNext = () => setCurrentPage((p) => Math.min(totalPages - 1, p + 1));

  return (
    <div className="tutorial-container">
      <div className="tutorial-content">
        <button className="back-button" onClick={handleGoBack}>
          {t('common.backToHome')}
        </button>

        <div className="tutorial-hero" role="region" aria-label={t('tutorial.hero.summaryAria')}>
          <div className="tutorial-hero-top">
            <span className="tutorial-hero-badge">
              {t('tutorial.hero.step', { current: currentPage + 1, total: totalPages })}
            </span>
            <span className="tutorial-hero-step">{stepTitle}</span>
          </div>

          <h1 className="tutorial-title">{t('tutorial.hero.title')}</h1>
          {stepSubtitle && <p className="tutorial-hero-subtitle">{stepSubtitle}</p>}

          <div className="tutorial-progress" aria-label={t('tutorial.hero.progressAria')}>
            <div className="tutorial-progress-track" aria-hidden="true">
              <div className="tutorial-progress-fill" style={{ width: `${progressPct}%` }} />
            </div>
            <div className="tutorial-progress-text">{t('tutorial.hero.progress', { pct: progressPct })}</div>
          </div>
        </div>

        <div className="tutorial-sections">{pages[currentPage].sections}</div>

        <div className="tutorial-pagination" aria-label={t('tutorial.pagination.aria')}>
          <div className="tutorial-pagination-slot tutorial-pagination-left">
            {!isFirstPage && (
              <button
                type="button"
                className="tutorial-nav-button"
                onClick={goPrev}
                aria-label={t('tutorial.pagination.previousAria')}
              >
                <i className="fas fa-chevron-left" aria-hidden="true" />
              </button>
            )}
          </div>

          <div className="tutorial-page-indicator">
            {t('tutorial.pagination.pageIndicator', { current: currentPage + 1, total: totalPages })}
          </div>

          <div className="tutorial-pagination-slot tutorial-pagination-right">
            {!isLastPage && (
              <button
                type="button"
                className="tutorial-nav-button"
                onClick={goNext}
                aria-label={t('tutorial.pagination.nextAria')}
              >
                <i className="fas fa-chevron-right" aria-hidden="true" />
              </button>
            )}
          </div>
        </div>

        {isLastPage && (
          <div className="tutorial-chatbot" aria-label={t('tutorial.chat.containerAria')}>
            <div className="tutorial-chatbot-header">
              <div className="tutorial-chatbot-title">
                <span className="tutorial-chatbot-dot" aria-hidden="true" />
                {t('tutorial.chat.title')}
              </div>

              <button
                type="button"
                className="tutorial-chatbot-toggle"
                onClick={() => setChatOpen((o) => !o)}
                aria-expanded={chatOpen}
              >
                {chatOpen ? t('tutorial.chat.toggle.close') : t('tutorial.chat.toggle.open')}
              </button>
            </div>

            {chatOpen && (
              <div className="tutorial-chatbot-body">
                <div className="tutorial-chatbot-hint">
                  {t('tutorial.chat.hint')}
                </div>

                <div className="tutorial-chatbot-suggestions" aria-label={t('tutorial.chat.suggestionsAria')}>
                  {suggestedQuestionList.map((q) => (
                    <button
                      key={q}
                      type="button"
                      className="tutorial-chatbot-chip"
                      onClick={() => void sendTutorialChatMessage(q)}
                      disabled={chatLoading}
                    >
                      {q}
                    </button>
                  ))}
                </div>

                <div className="tutorial-chatbot-messages" role="log" aria-live="polite" aria-label={t('tutorial.chat.messages.aria')}>
                  {chatMessages.length === 0 ? (
                    <div className="tutorial-chatbot-empty">{t('tutorial.chat.messages.empty')}</div>
                  ) : (
                    chatMessages.map((m, idx) => (
                      <div
                        key={`${m.role}-${idx}`}
                        className={`tutorial-chatbot-bubble ${m.role === 'user' ? 'is-user' : 'is-assistant'}`}
                      >
                        {m.text}
                      </div>
                    ))
                  )}
                  <div ref={chatEndRef} />
                </div>

                {chatError && (
                  <div className="tutorial-chatbot-error" role="alert">
                    {chatError}
                  </div>
                )}

                <div className="tutorial-chatbot-inputRow">
                  <textarea
                    className="tutorial-chatbot-input"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={handleChatKeyDown}
                    placeholder={t('tutorial.chat.input.placeholder')}
                    rows={2}
                    disabled={chatLoading}
                  />
                  <button
                    type="button"
                    className="tutorial-chatbot-send"
                    onClick={() => void sendTutorialChatMessage()}
                    disabled={chatLoading || !chatInput.trim()}
                  >
                    {chatLoading ? t('common.sending') : t('common.send')}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default Tutorial;
