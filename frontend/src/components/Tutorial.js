import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Tutorial.css';

const API_URL = 'http://localhost:8000/api';

function Tutorial() {
  const navigate = useNavigate();
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
          throw new Error(data?.error || 'No se pudo cargar el historial del chatbot.');
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
  }, [chatbotId]);

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
      throw new Error(data?.error || 'No se pudo iniciar el chatbot.');
    }

    if (!data?.id) {
      throw new Error('No se pudo iniciar el chatbot.');
    }

    setChatbotId(data.id);
    return data.id;
  };

  const sendTutorialChatMessage = async (overrideMessage) => {
    const mensaje = String(overrideMessage ?? chatInput ?? '').trim();
    if (!mensaje || chatLoading) return;

    setChatError('');
    setChatLoading(true);
    setChatMessages((prev) => [...prev, { role: 'user', text: mensaje }]);
    setChatInput('');

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
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.error || 'Error enviando mensaje al chatbot.');
      }

      if (data?.chatbot_id) {
        setChatbotId(data.chatbot_id);
      }

      setChatMessages((prev) => [...prev, { role: 'assistant', text: String(data?.respuesta || '') }]);
    } catch (err) {
      setChatError(err?.message || 'Error enviando mensaje al chatbot.');
    } finally {
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
            { nombre: 'Tú', icono: 'icono1.jpg', tipo: 'humano', dificultad: 'Baja', numero: 1 },
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
        const msg = data?.error || 'Error al crear la partida. Verifica que el servidor esté activo.';
        throw new Error(msg);
      }

      navigate('/game', { state: { partidaInicial: data, jugadoresConfig } });
    } catch (err) {
      setStartError(err?.message || 'Error al crear la partida.');
      setStartingMode(null);
    }
  };

  const pages = [
    {
      key: 'objective-norms-win',
      sections: (
        <>
          <section className="tutorial-section">
            <h2>Objetivo del juego</h2>
            <p>
              El objetivo principal es ser el primer jugador en mover todas tus diez piezas desde
              tu punto de partida (una de las puntas de la estrella) hasta la punta de la estrella
              directamente opuesta a la tuya.
            </p>
          </section>

          <section className="tutorial-section">
            <h2>Normas</h2>
            <ul>
              <li>
                El tablero tiene forma de estrella de seis puntas. En un inicio se crean los
                jugadores, los cuales tienen asignado un color dentro del tablero con sus diez
                piezas colocadas en una de las puntas de la estrella.
              </li>
              <li>
                Estas posiciones estarán predefinidas en el sistema en base a la cantidad de
                jugadores que participan.
              </li>
              <li>
                Solo se mueve una ficha por turno. Se puede alterar el movimiento de la ficha o
                cambiar la ficha que se mueve si se desea antes de validarlo.
              </li>
              <li>
                A diferencia de las damas tradicionales, en las Damas Chinas no se capturan ni se
                eliminan piezas del tablero. Todas las piezas permanecen en juego hasta el final.
              </li>
              <li>
                Las casillas pueden ser ocupadas por cualquier jugador durante la partida, a
                excepción de si ya hay una pieza en esa posición.
              </li>
              <li>
                Los jugadores se turnan para mover una de sus piezas. El orden de los turnos estará
                predefinido en el sistema, siguiendo el orden que se ha establecido al inicio al
                crear los jugadores participantes.
              </li>
              <li>
                Los jugadores pueden bloquear el paso de los oponentes ocupando espacios clave. Sin
                embargo, no puedes ocupar permanentemente los espacios de la base de inicio o destino
                de otro jugador si eso impide que ese jugador complete su objetivo. Puedes moverte a
                través de ellos, pero tu objetivo es llenar tu propia base de destino.
              </li>
            </ul>
          </section>

          <section className="tutorial-section">
            <h2>¿Cómo se puede ganar?</h2>
            <p>
              El primer jugador en mover todas sus diez piezas a los diez espacios de su área de
              destino gana el juego. Si dos jugadores completan sus bases en el mismo turno, se
              puede considerar un empate o establecer una regla de desempate (por ejemplo, el jugador
              cuyo turno era primero).
            </p>
          </section>
        </>
      ),
    },
    {
      key: 'moves-and-strategy',
      sections: (
        <>
          <section className="tutorial-section">
            <h2>Tipos de movimientos</h2>
            <ul>
              <li>
                <strong>Movimiento simple:</strong> Una pieza puede moverse a un espacio adyacente
                vacío en cualquiera de las seis direcciones posibles (adelante, atrás, a los lados,
                o en diagonal).
              </li>
              <li>
                <strong>Salto:</strong> Una pieza puede saltar sobre otra pieza (ya sea propia o del
                oponente) si hay un espacio vacío directamente al otro lado de la pieza sobre la que
                se salta. El salto debe ser en línea recta.
              </li>
              <li>
                <strong>Cadenas de saltos:</strong> Si después de un salto, la pieza se encuentra en
                una posición desde la cual puede realizar otro salto, puede hacerlo en el mismo
                turno. Los saltos múltiples no son obligatorios, pero pueden ser muy ventajosos. Los
                saltos pueden cambiar de dirección en cada salto.
              </li>
            </ul>
          </section>

          <section className="tutorial-section">
            <h2>Consejos estratégicos</h2>
            <ul>
              <li>
                <strong>Prioriza los saltos largos:</strong> Encadenar saltos permite avanzar mucho
                más rápido que los movimientos simples.
              </li>
              <li>
                <strong>Crea “puentes”:</strong> Coloca tus fichas de forma que puedas usarlas como
                apoyo para saltar en turnos futuros.
              </li>
              <li>
                <strong>Evita aislar fichas:</strong> Las fichas solitarias avanzan más lento porque
                no pueden aprovechar saltos.
              </li>
              <li>
                <strong>Avanza en grupo:</strong> Mantener tus fichas relativamente juntas facilita
                movimientos más eficientes.
              </li>
              <li>
                <strong>Aprovecha a los rivales:</strong> También puedes usar sus fichas para saltar,
                así que observa todo el tablero.
              </li>
              <li>
                <strong>Planifica varios turnos:</strong> No pienses solo en el movimiento inmediato;
                intenta preparar cadenas de saltos para turnos futuros.
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
          <h2>¿Qué representa cada elemento en la pantalla?</h2>
          <p>Una partida está compuesta por varios elementos que vamos a explicar a continuación.</p>

          <h3>Tablero</h3>
          <p>
            El tablero, como se ha explicado antes, es una estrella de seis puntas: cada punta con
            un color asignado y un jugador. Se encuentra en el centro de la pantalla y es el
            elemento principal del juego.
          </p>

          <h3>Rondas</h3>
          <p>
            Se encuentra a la izquierda de la pantalla. Muestra los jugadores participantes en el
            juego. Cada jugador puede ser controlado por un agente inteligente o un humano. Cada
            agente inteligente tendrá dos modalidades: Fácil o Difícil. Cada jugador podrá mover
            pieza en base al orden establecido en esa sección. También indica el número de ronda en
            el que se encuentra en ese momento la partida y los colores asignados a cada jugador.
          </p>

          <h3>Temporizador</h3>
          <p>
            Se encuentra en la parte superior de la pantalla. Muestra el tiempo transcurrido de la
            partida. Cuando se pausa la partida ese tiempo deja de contarse, por lo que es el tiempo
            jugado. No hay límite de tiempo ni para hacer cada jugada ni para terminar la partida.
          </p>

          <h3>Música</h3>
          <p>
            Se encuentra a la izquierda del temporizador. Reproduce audios musicales establecidos
            en el sistema a gusto del usuario. Si desea reproducir una canción aleatoria, pulse una
            vez el botón. Para desactivar la música, pulse de nuevo.
          </p>

          <h3>Pausa / Reanudar / Cancelar</h3>
          <p>
            Se encuentra a la derecha del temporizador. Este botón sirve para pausar el transcurso
            de la partida. Una vez pulsado el botón, tiene dos opciones: reanudar la partida desde
            el punto de guardado, pudiendo continuar; o cancelar la partida de forma definitiva,
            eliminando la partida. Una vez que cancele la partida no podrá continuar desde el momento
            en el que lo pausó, ya que toda la información relacionada con esa partida habrá sido
            eliminada.
          </p>

          <h3>Ayuda</h3>
          <p>
            Se encuentra a la derecha de la pantalla. Si necesita asistencia puede acceder a un
            sistema de soporte al pulsar el botón “Abrir Ayuda”. Se mostrará un desplegable con un
            asistente que resuelve dudas relacionadas con la partida. Si tiene dudas sobre qué le
            puede preguntar, hay un botón de información indicando lo que puede responder. Abajo del
            desplegable se encuentra un área de texto donde puede formular su pregunta y enviarla con
            el botón “Enviar”. Cada jugador tendrá disponible un chatbot único por partida.
          </p>

          <h3>Pasar Ronda / Continuar / Deshacer</h3>
          <p>
            Se encuentra en la parte inferior de la pantalla. Si desea pasar de ronda sin realizar
            ningún movimiento, puede pulsar “Pasar Ronda”, asignando el turno al siguiente jugador.
            Si quiere mover una ficha, primero seleccione la pieza que quiera desplazar: se le
            mostrarán en pantalla las diferentes posiciones a las que se puede mover. Tras mover la
            pieza, tendrá dos opciones: “Deshacer”, que revierte el movimiento y permite mover otra
            ficha; y “Continuar”, para validar la jugada y pasar al siguiente jugador.
          </p>
        </section>
      ),
    },
    {
      key: 'finished',
      sections: (
        <section className="tutorial-section">
          <h2>Fin del tutorial</h2>
          <p>Has llegado al final del tutorial. ¿Qué quieres hacer ahora?</p>
          <ul className="tutorial-finish-list">
            <li>
              <strong>Partida rápida:</strong> Una partida donde te podrás enfrentar contra un jugador en modo Fácil.
            </li>
            <li>
              <strong>Demo:</strong> Una partida formada por dos jugadores que se enfrentan entre sí en modo Difícil.
            </li>
            <li>
              <strong>Chatbot:</strong> Si te queda alguna duda antes de empezar a jugar, puedes preguntarle a nuestro agente conversacional al final de esta pantalla.
            </li>
          </ul>

          <div className="tutorial-finish-actions" aria-label="Acciones tras finalizar el tutorial">
            <button
              type="button"
              className="tutorial-finish-button tutorial-finish-primary"
              onClick={() => startPresetGame('quick')}
              disabled={startingMode !== null}
            >
              {startingMode === 'quick' ? 'Creando partida...' : 'Jugar partida rápida'}
            </button>

            <button
              type="button"
              className="tutorial-finish-button tutorial-finish-secondary"
              onClick={() => startPresetGame('demo')}
              disabled={startingMode !== null}
            >
              {startingMode === 'demo' ? 'Creando demo...' : 'Ver demo'}
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

  const stepTitles = [
    'Objetivo y reglas',
    'Movimientos y estrategia',
    'Elementos de la pantalla',
    'Fin del tutorial',
  ];
  const stepSubtitles = [
    'Qué tienes que conseguir y las normas básicas para jugar.',
    'Cómo moverte y qué decisiones suelen dar ventaja.',
    'Qué significa cada control durante una partida.',
    'Elige tu siguiente paso o pregunta lo que necesites.',
  ];

  const stepTitle = stepTitles[currentPage] || 'Tutorial';
  const stepSubtitle = stepSubtitles[currentPage] || '';
  const progressPct = Math.max(0, Math.min(100, Math.round(((currentPage + 1) / totalPages) * 100)));

  const suggestedQuestions = [
    '¿Cómo se mueve una pieza?',
    '¿Qué es una cadena de saltos?',
    '¿Cómo se gana una partida?',
    '¿Para qué sirve el botón de Pausa?',
  ];

  const goPrev = () => setCurrentPage((p) => Math.max(0, p - 1));
  const goNext = () => setCurrentPage((p) => Math.min(totalPages - 1, p + 1));

  return (
    <div className="tutorial-container">
      <div className="tutorial-content">
        <button className="back-button" onClick={handleGoBack}>
          ← Volver al Inicio
        </button>

        <div className="tutorial-hero" role="region" aria-label="Resumen del paso del tutorial">
          <div className="tutorial-hero-top">
            <span className="tutorial-hero-badge">
              Paso {currentPage + 1}/{totalPages}
            </span>
            <span className="tutorial-hero-step">{stepTitle}</span>
          </div>

          <h1 className="tutorial-title">Tutorial - Damas Chinas</h1>
          {stepSubtitle && <p className="tutorial-hero-subtitle">{stepSubtitle}</p>}

          <div className="tutorial-progress" aria-label="Progreso del tutorial">
            <div className="tutorial-progress-track" aria-hidden="true">
              <div className="tutorial-progress-fill" style={{ width: `${progressPct}%` }} />
            </div>
            <div className="tutorial-progress-text">{progressPct}% completado</div>
          </div>
        </div>

        <div className="tutorial-sections">{pages[currentPage].sections}</div>

        <div className="tutorial-pagination" aria-label="Navegación del tutorial">
          <div className="tutorial-pagination-slot tutorial-pagination-left">
            {!isFirstPage && (
              <button
                type="button"
                className="tutorial-nav-button"
                onClick={goPrev}
                aria-label="Página anterior"
              >
                <i className="fas fa-chevron-left" aria-hidden="true" />
              </button>
            )}
          </div>

          <div className="tutorial-page-indicator">
            Página {currentPage + 1} de {totalPages}
          </div>

          <div className="tutorial-pagination-slot tutorial-pagination-right">
            {!isLastPage && (
              <button
                type="button"
                className="tutorial-nav-button"
                onClick={goNext}
                aria-label="Página siguiente"
              >
                <i className="fas fa-chevron-right" aria-hidden="true" />
              </button>
            )}
          </div>
        </div>

        {isLastPage && (
          <div className="tutorial-chatbot" aria-label="Chatbot de ayuda del tutorial">
            <div className="tutorial-chatbot-header">
              <div className="tutorial-chatbot-title">
                <span className="tutorial-chatbot-dot" aria-hidden="true" />
                Chatbot de CheckerIT
              </div>

              <button
                type="button"
                className="tutorial-chatbot-toggle"
                onClick={() => setChatOpen((o) => !o)}
                aria-expanded={chatOpen}
              >
                {chatOpen ? 'Ocultar' : 'Abrir'}
              </button>
            </div>

            {chatOpen && (
              <div className="tutorial-chatbot-body">
                <div className="tutorial-chatbot-hint">
                  Pregunta sobre reglas, movimientos, interfaz o sobre el propio CheckerIT.
                </div>

                <div className="tutorial-chatbot-suggestions" aria-label="Preguntas sugeridas">
                  {suggestedQuestions.map((q) => (
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

                <div className="tutorial-chatbot-messages" role="log" aria-live="polite">
                  {chatMessages.length === 0 ? (
                    <div className="tutorial-chatbot-empty">Escribe una pregunta para empezar.</div>
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
                    placeholder="Escribe tu pregunta…"
                    rows={2}
                    disabled={chatLoading}
                  />
                  <button
                    type="button"
                    className="tutorial-chatbot-send"
                    onClick={() => void sendTutorialChatMessage()}
                    disabled={chatLoading || !chatInput.trim()}
                  >
                    {chatLoading ? 'Enviando...' : 'Enviar'}
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
