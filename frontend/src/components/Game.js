import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './Game.css';
import { MUSIC_LIST, getRandomMusicIndex } from './musicList';
import Board from './Board';
import Victory from './Victory';
import { buildRoundAdvancePayload, buildSecureMovimientosPayload } from '../security/integrityGuards';

const PLAYER_COLORS = ['#FFFFFF', '#4444FF', '#44DD44', '#000000', '#FF4444', '#FFDD44'];

const getActivePuntas = (numJugadores) => {
  switch (numJugadores) {
    case 2:
      return [0, 3];
    case 3:
      return [0, 4, 5];
    case 4:
      return [1, 2, 4, 5];
    case 6:
      return [0, 1, 2, 3, 4, 5];
    default:
      return [];
  }
};

function Game() {
  const navigate = useNavigate();
  const location = useLocation();
  const { t, i18n } = useTranslation();
  const [partida, setPartida] = useState(null);
  const [loading, setLoading] = useState(true);
  const [elapsed, setElapsed] = useState(0);
  const [showHelp, setShowHelp] = useState(false);

  // Chatbot (Gemini vía backend)
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState([]); // { role: 'user'|'assistant', text: string }
  const [chatbotId, setChatbotId] = useState(null);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState(null);
  const [showChatInfo, setShowChatInfo] = useState(false);
  const [hintMove, setHintMove] = useState(null); // { origen, destino, secuencia?, token }

  const sendChatMessage = async () => {
    const mensaje = (chatInput || '').trim();
    if (!mensaje || chatLoading) return;

    setChatError(null);
    setChatLoading(true);
    setChatMessages((prev) => [...prev, { role: 'user', text: mensaje }]);
    setChatInput('');

    try {
      const res = await fetch('http://localhost:8000/api/chatbot/send_message/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mensaje,
          chatbot_id: chatbotId,
          partida_id: partida?.id_partida || null,
          lang: i18n.resolvedLanguage || i18n.language,
          jugador_id:
            currentPlayerIndex !== null && currentPlayerIndex !== undefined
              ? (dbJugadores?.[currentPlayerIndex]?.id_jugador || null)
              : null,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.error || t('game.chat.errors.send'));
      }

      if (data?.chatbot_id && data.chatbot_id !== chatbotId) {
        setChatbotId(data.chatbot_id);
      }
      setChatMessages((prev) => [...prev, { role: 'assistant', text: data?.respuesta || '' }]);

      if (data?.tipo === 'mostrar_movimiento' && data?.sugerencia) {
        setHintMove({ ...data.sugerencia, token: Date.now() });
      }
    } catch (err) {
      setChatError(err?.message || t('game.chat.errors.send'));
    } finally {
      setChatLoading(false);
    }
  };
  const [isPlayingMusic, setIsPlayingMusic] = useState(false);
  const [currentMusicIndex, setCurrentMusicIndex] = useState(-1);
  const audioRef = useRef(null);
  const [currentPlayerIndex, setCurrentPlayerIndex] = useState(null);
  const [moveMade, setMoveMade] = useState(false);
  const [lockedPiecePos, setLockedPiecePos] = useState(null);
  const [originalPiecePos, setOriginalPiecePos] = useState(null);
  const [undoToOriginalToken, setUndoToOriginalToken] = useState(0);
  const [initialBoardState, setInitialBoardState] = useState(null);
  const [roundCount, setRoundCount] = useState(1);
  const [moveHistory, setMoveHistory] = useState([]);
  const [actualRound, setActualRound] = useState(null);
  const [pieceByPos, setPieceByPos] = useState(new Map());
  const [roundStartPieceByPos, setRoundStartPieceByPos] = useState(null);
  const [dbJugadores, setDbJugadores] = useState([]);
  const [isPaused, setIsPaused] = useState(false);
  const [pausedAccumMs, setPausedAccumMs] = useState(0); // tiempo total en pausa
  const [pauseStartedAt, setPauseStartedAt] = useState(null); // marca de inicio de pausa
  const [showEndConfirm, setShowEndConfirm] = useState(false);
  const [showVictory, setShowVictory] = useState(false);
  const [victoryData, setVictoryData] = useState(null);
  const [aiMoveCmd, setAiMoveCmd] = useState(null);
  const [aiThinking, setAiThinking] = useState(false);
  const [aiAutoFinishToken, setAiAutoFinishToken] = useState(null);
  const [aiError, setAiError] = useState(null);
  const [aiSequence, setAiSequence] = useState(null); // [{fromKey,toKey,piezaId?}, ...]
  const [aiSeqIndex, setAiSeqIndex] = useState(0);
  const aiSeqTokenRef = useRef(null);
  const isPausedRef = useRef(false);

  void aiAutoFinishToken;
  void aiError;

  // Al cambiar de jugador en la misma partida, cambiar también el flujo conversacional.
  useEffect(() => {
    const partidaId = partida?.id_partida;
    const jugadorId =
      currentPlayerIndex !== null && currentPlayerIndex !== undefined
        ? (dbJugadores?.[currentPlayerIndex]?.id_jugador || null)
        : null;

    if (!partidaId || !jugadorId) return;

    let cancelled = false;
    const loadChatbotForContext = async () => {
      try {
        setChatError(null);
        const url = `http://localhost:8000/api/chatbot/for_context/?partida_id=${encodeURIComponent(partidaId)}&jugador_id=${encodeURIComponent(jugadorId)}`;
        const res = await fetch(url);
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data?.error || t('game.chat.errors.loadHistory'));
        }
        if (cancelled) return;

        const convo = Array.isArray(data?.conversaciones) ? data.conversaciones : [];
        const messages = [];
        for (const turn of convo) {
          if (turn?.mensaje) messages.push({ role: 'user', text: String(turn.mensaje) });
          if (turn?.respuesta) messages.push({ role: 'assistant', text: String(turn.respuesta) });
        }

        setChatbotId(data?.chatbot_id || null);
        setChatMessages(messages);
      } catch (err) {
        if (cancelled) return;
        // Si falla, al menos no mezclar conversaciones de jugadores distintos
        setChatbotId(null);
        setChatMessages([]);
        setChatError(err?.message || t('game.chat.errors.loadHistory'));
      }
    };

    loadChatbotForContext();
    return () => {
      cancelled = true;
    };
  }, [partida?.id_partida, currentPlayerIndex, dbJugadores, t]);

  const AI_FIRST_DELAY_MS = 200;
  const AI_CHAIN_DELAY_MS = 200;

  useEffect(() => {
    if (actualRound?.numero) {
      setRoundCount(actualRound.numero);
    }
  }, [actualRound?.numero]);

  useEffect(() => {
    isPausedRef.current = isPaused;
  }, [isPaused]);

  const jugadoresConfig = useMemo(() => location.state?.jugadoresConfig || [], [location.state]);
  const isAITurn = useMemo(() => jugadoresConfig[currentPlayerIndex]?.tipo === 'ia', [jugadoresConfig, currentPlayerIndex]);
  const activePuntas = useMemo(() => getActivePuntas(jugadoresConfig.length), [jugadoresConfig.length]);

  const resolveNombreJugador = (configJugador, jugadorDb) => {
    const nombreDb = jugadorDb?.nombre;
    const nombreDbTrimmed = typeof nombreDb === 'string' ? nombreDb.trim() : '';
    // Si el backend guarda un nombre por defecto para IA (p.ej. "Agente Inteligente"),
    // tratamos ese valor como placeholder y lo traducimos.
    const isAiDefaultName =
      !!nombreDbTrimmed &&
      (nombreDbTrimmed.toLowerCase() === 'agente inteligente' || nombreDbTrimmed.toLowerCase().startsWith('agente inteligente '));

    if (nombreDbTrimmed && !(configJugador?.tipo === 'ia' && isAiDefaultName)) {
      return nombreDbTrimmed;
    }
    const nombreConfig = configJugador?.nombre;
    if (typeof nombreConfig === 'string' && nombreConfig.trim().length > 0) {
      return nombreConfig.trim();
    }
    if (configJugador?.tipo === 'ia') {
      const diff = configJugador?.dificultad;
      const diffKey = String(diff || '').trim().toLowerCase();
      const diffLabel =
        diffKey === 'fácil' || diffKey === 'facil' || diffKey === 'easy' || diffKey === 'bajo' || diffKey === 'baja' || diffKey === 'low'
          ? t('players.aiDifficulty.easy')
          : diffKey === 'difícil' || diffKey === 'dificil' || diffKey === 'hard' || diffKey === 'alto' || diffKey === 'high'
            ? t('players.aiDifficulty.hard')
            : diff;
      const agentLabel = t('players.typeAI');
      return diffLabel ? `${agentLabel} ${diffLabel}` : agentLabel;
    }
    return t('game.player.generic');
  };

  const handlePause = () => {
    setIsPaused(true);
    setPauseStartedAt(Date.now());
    if (isPlayingMusic && audioRef.current) {
      audioRef.current.pause();
    }
  };

  const handleGoBack = () => {
    navigate('/');
  };

  const handleResume = () => {
    if (pauseStartedAt) {
      const newTotal = pausedAccumMs + (Date.now() - pauseStartedAt);
      setPausedAccumMs(newTotal);
      if (partida?.id_partida) {
        const url = `http://localhost:8000/api/partidas/${partida.id_partida}/`;
        fetch(url)
          .then(res => res.json())
          .then(remote => {
            const prev = Number(remote?.tiempo_sobrante || 0);
            const mergedSeconds = prev + Math.floor((Date.now() - pauseStartedAt) / 1000);
               // actualizar estado local con el valor merged
               setPartida((p) => p ? { ...p, tiempo_sobrante: mergedSeconds } : p);
               return fetch(url, {
              method: 'PATCH',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ tiempo_sobrante: mergedSeconds })
            });
          })
          .catch(err => console.error('Error actualizando tiempo_sobrante:', err));
      }
      setPauseStartedAt(null);
    }
    setIsPaused(false);
    if (isPlayingMusic && audioRef.current) {
      audioRef.current.play();
    }
  };

  const handleShowEndConfirm = () => {
    setShowEndConfirm(true);
  };

  const handleCancelEnd = () => {
    setShowEndConfirm(false);
  };

  const handleEndGame = async () => {
    try {
      setIsPlayingMusic(false);
      setCurrentMusicIndex(-1);
      
      if (audioRef.current) {
        try {
          audioRef.current.onerror = null;
          audioRef.current.pause();
          audioRef.current.loop = false;
          audioRef.current.currentTime = 0;
          audioRef.current.removeAttribute('src');
        } catch {}
        audioRef.current = null;
      }

      const deleteUrl = `http://localhost:8000/api/partidas/${partida.id_partida}/`;
      const response = await fetch(deleteUrl, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        console.error('Error al eliminar partida:', response.status);
      }

      navigate('/');
    } catch (error) {
      console.error('Error en handleEndGame:', error);
      navigate('/');
    }
  };

  const checkVictory = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/piezas/?partida_id=${partida.id_partida}`);
      const piezas = await res.json();

      if (!Array.isArray(piezas)) return false;

      // Para cada punta de inicio, definimos las casillas objetivo en la punta opuesta
      const posicionesObjetivo = {
        0: ['3-13', '1-13', '0-14', '2-14', '1-15', '2-13', '0-13', '1-14', '0-15', '0-16'], // Objetivo para quien empieza en punta 0 (opuesto: 3)
        1: ['9-9', '9-11', '10-11', '10-12', '12-12', '9-10', '10-10', '11-11', '9-12', '11-12'], // Objetivo para punta 1 (opuesto: 5)
        2: ['0-9', '0-11', '1-11', '0-12', '2-12', '0-10', '1-10', '2-11', '1-12', '3-12'], // Objetivo para punta 2 (opuesto: 4)
        3: ['0-0', '1-1', '0-3', '1-3', '2-3', '0-1', '0-2', '1-2', '2-2', '3-3'],       // Objetivo para punta 3 (opuesto: 0)
        4: ['12-4', '10-4', '11-5', '9-5', '9-6', '11-4', '9-4', '10-5', '10-6', '9-7'],  // Objetivo para punta 4 (opuesto: 2)
        5: ['0-4', '2-4', '0-5', '2-5', '1-6', '1-4', '3-4', '1-5', '0-6', '0-7']        // Objetivo para punta 5 (opuesto: 1)
      };

      for (let i = 0; i < jugadoresConfig.length; i++) {
        const puntaInicio = activePuntas[i];
        const posicionesObjetivoJugador = posicionesObjetivo[puntaInicio] || [];
        const jugadorId = dbJugadores[i]?.id_jugador;

        // Seleccionamos las piezas del jugador por id de jugador
        const piezasJugador = Array.isArray(piezas)
          ? piezas.filter((p) => (jugadorId ? p.jugador === jugadorId : false))
          : [];

        if (piezasJugador.length === 0) continue;

        const todasEnObjetivo = piezasJugador.every((pieza) =>
          posicionesObjetivoJugador.includes(pieza.posicion)
        );

        if (todasEnObjetivo) {
          const ganador = {
            ...jugadoresConfig[i],
            nombre: resolveNombreJugador(jugadoresConfig[i], dbJugadores[i]),
            punta: puntaInicio
          };

          const perdedores = jugadoresConfig
            .map((j, idx) => ({ jugador: j, idx }))
            .filter(({ idx }) => idx !== i)
            .map(({ jugador, idx }) => ({
              ...jugador,
              nombre: resolveNombreJugador(jugador, dbJugadores[idx]),
              punta: activePuntas[idx]
            }));

          setVictoryData({
            ganador,
            perdedores,
            rondas: roundCount,
            tiempo: elapsed,
            totalJugadores: jugadoresConfig.length
          });

          if (partida?.id_partida) {
            const url = `http://localhost:8000/api/partidas/${partida.id_partida}/`;
            fetch(url, {
              method: 'PATCH',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ fecha_fin: new Date().toISOString(), estado: 'FINALIZADA' })
            }).catch((err) => console.error('Error marcando partida finalizada:', err));
          }

          setShowVictory(true);
          setIsPaused(true);

          if (isPlayingMusic && audioRef.current) {
            audioRef.current.pause();
          }

          return true;
        }
      }

      return false;
    } catch (error) {
      console.error('Error verificando victoria:', error);
      return false;
    }
  };

  useEffect(() => {
    if (partida?.id_partida) {
      fetchJugadoresPartida(partida.id_partida).then(dbJugadores => {
        setDbJugadores(dbJugadores);
        
        fetchPrimeraRonda(partida.id_partida).then(ronda => {
          if (ronda?.id_ronda) {
            setActualRound({ id_ronda: ronda.id_ronda, numero: ronda.numero, inicio: ronda.inicio });
            const rondaJugadorId = ronda.jugador_id || ronda.jugador?.id_jugador || ronda.jugador;
            console.log(`📍 Ronda cargada: numero=${ronda.numero}, jugador=${rondaJugadorId}`);

            if (rondaJugadorId && dbJugadores.length > 0) {
              const jugadorDeLaRonda = dbJugadores.find(j => j.id_jugador === rondaJugadorId);
              if (jugadorDeLaRonda) {
                const idx = dbJugadores.findIndex(j => j.id_jugador === jugadorDeLaRonda.id_jugador);
                if (idx >= 0) {
                  setCurrentPlayerIndex(idx);
                  console.log(`👤 Jugador establecido al jugador ${jugadorDeLaRonda.numero}`);
                }
              }
            }
          }
        });
      });
    }
  }, [partida]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (location.state?.partidaInicial) {
      const partidaData = location.state.partidaInicial;
      setPartida(partidaData);
      setLoading(false);
      
      if (partidaData?.id_partida) {
        // Verificar si la partida ya tiene rondas; si no, inicializar posiciones
        fetch(`http://localhost:8000/api/rondas/?partida_id=${partidaData.id_partida}`)
          .then(res => res.json())
          .then(rondas => {
            const esPrimeraVez = !Array.isArray(rondas) || rondas.length === 0;
            
            if (esPrimeraVez) {
              // Solo actualizar posiciones iniciales si es la primera vez
              return fetch(`http://localhost:8000/api/partidas/${partidaData.id_partida}/actualizar_posiciones_iniciales/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
              })
              .then(res => res.json())
              .then(data => {
                console.log('Posiciones iniciales actualizadas:', data);
              });
            } else {
              console.log('Partida ya tiene rondas, no se resetean posiciones');
            }
          })
          .catch(error => {
            console.error('Error verificando rondas:', error);
          });
      }
    } else {
      handleGoBack();
    }
  }, [location.state]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const loadPartida = async () => {
      if (!partida?.id_partida) return;
      try {
        const res = await fetch(`http://localhost:8000/api/partidas/${partida.id_partida}/`);
        if (!res.ok) return;
        const data = await res.json();
        setPartida((prev) => prev ? { ...prev, tiempo_sobrante: data.tiempo_sobrante } : prev);
        setPausedAccumMs(Number(data.tiempo_sobrante || 0) * 1000);
        setPauseStartedAt(null);
      } catch (e) {
        console.error('Error refrescando partida:', e);
      }
    };
    loadPartida();
  }, [partida?.id_partida]);

  useEffect(() => {
    const startDate = partida?.fecha_inicio ? new Date(partida.fecha_inicio) : null;
    if (!startDate) return; 

    const computeElapsed = () => {
      const now = Date.now();
      const pausedMs = pausedAccumMs + (pauseStartedAt ? now - pauseStartedAt : 0);
      const diffSeconds = Math.max(0, Math.floor((now - startDate.getTime() - pausedMs) / 1000));
      setElapsed(diffSeconds);
    };

    computeElapsed();

    if (isPaused) return; 

    const timerId = setInterval(computeElapsed, 1000);
    return () => clearInterval(timerId);
  }, [isPaused, partida?.fecha_inicio, partida?.tiempo_sobrante, pausedAccumMs, pauseStartedAt]);

  useEffect(() => {
    return () => {
      if (audioRef.current) {
        try {
          audioRef.current.pause();
          audioRef.current.loop = false;
          audioRef.current.currentTime = 0;
          audioRef.current.src = '';
          audioRef.current.load();
        } catch {}
      }
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
      console.warn('No hay canciones en la carpeta music/');
      stopMusic();
      return;
    }

    if (audioRef.current) {
      try {
        audioRef.current.pause();
        audioRef.current.loop = false;
        audioRef.current.currentTime = 0;
        audioRef.current.src = '';
        audioRef.current.load();
      } catch {}
      audioRef.current = null;
    }

    const newIndex = getRandomMusicIndex(currentMusicIndex);
    setCurrentMusicIndex(newIndex);

    try {
      const audio = new Audio(require(`./music/${MUSIC_LIST[newIndex]}`));
      audio.volume = 0.5;
      audio.loop = true;

      audio.onerror = () => {
        console.error(`Error al reproducir: ${MUSIC_LIST[newIndex]}`);
        stopMusic();
      };

      audio.play().catch((error) => {
        console.error('Error al iniciar reproducción:', error);
      });

      audioRef.current = audio;
    } catch (error) {
      console.error(`No se pudo cargar el archivo: ${MUSIC_LIST[newIndex]}`, error);
      stopMusic();
    }
  };

  const stopMusic = () => {
    if (audioRef.current) {
      try {
        audioRef.current.pause();
        audioRef.current.loop = false;
        audioRef.current.currentTime = 0;
        audioRef.current.src = '';
        audioRef.current.load();
      } catch {}
      audioRef.current = null;
    }
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

  const fetchPrimeraRonda = async (partidaId) => {
    const res = await fetch(`http://localhost:8000/api/rondas/?partida_id=${partidaId}`);
    const data = await res.json();
    if (!Array.isArray(data) || data.length === 0) return null;
    const current = data.find(t => !t.fin);
    if (current) return current;
    const sorted = data.sort((a, b) => (b.numero || 0) - (a.numero || 0));
    return sorted[0] || null;
  };

  const fetchJugadoresPartida = async (partidaId) => {
    try {
      const res = await fetch(`http://localhost:8000/api/participaciones/?partida_id=${partidaId}`);
      const data = await res.json();
      if (!Array.isArray(data) || data.length === 0) return [];
      const jugadores = data
        .sort((a, b) => (a.orden_participacion || 0) - (b.orden_participacion || 0))
        .map(p => ({
          id_jugador: p.jugador,
          numero: p.orden_participacion,
          nombre: p.jugador_nombre || 'Desconocido'
        }));
      return jugadores;
    } catch (e) {
      console.error('Error fetching jugadores:', e);
      return [];
    }
  };

  useEffect(() => {
    const loadPieces = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/piezas/');
        const data = await res.json();
        const todasLasPiezas = Array.isArray(data) ? data : [];
        const map = new Map();
        todasLasPiezas.forEach(p => map.set(p.posicion, p.id_pieza));
        setPieceByPos(map);
      } catch (e) {
        console.error('Error cargando piezas:', e);
      }
    };
    if (partida?.id_partida) loadPieces();
  }, [partida]); // eslint-disable-line react-hooks/exhaustive-deps

  const requestAiMove = async () => {
    if (isPausedRef.current) return;
    const jugadorDb = dbJugadores[currentPlayerIndex];
    if (!jugadorDb?.id_jugador || !partida?.id_partida) return;

    setAiThinking(true);
    setAiError(null);
    try {
      const res = await fetch(`http://localhost:8000/api/agentes-inteligentes/${jugadorDb.id_jugador}/sugerir_movimiento/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ partida_id: partida.id_partida, permitir_simples: true })
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Estado ${res.status}: ${text}`);
      }

      const data = await res.json();
      if (!data?.origen || !data?.destino) {
        throw new Error('Respuesta del agente Inteligente sin origen/destino');
      }

      const token = Date.now();
      // Si viene una secuencia (saltos encadenados), la reproducimos paso a paso
      if (Array.isArray(data.secuencia) && data.secuencia.length > 0) {
        const seq = data.secuencia
          .filter((m) => m?.origen && m?.destino)
          .map((m) => ({ fromKey: m.origen, toKey: m.destino, piezaId: data.pieza_id || data.pieza }));

        if (seq.length === 0) {
          throw new Error('Respuesta del agente Inteligente con secuencia vacía');
        }

        aiSeqTokenRef.current = token;
        setAiSequence(seq);
        setAiSeqIndex(0);
        setAiMoveCmd(null);
        setAiAutoFinishToken(null);
      } else {
        // Movimiento único
        setAiSequence(null);
        setAiSeqIndex(0);
        setAiAutoFinishToken(null);
        // No ejecutar instantáneo: esperar un poco
        setTimeout(() => {
          if (isPausedRef.current) return;
          setAiMoveCmd({ token, fromKey: data.origen, toKey: data.destino, piezaId: data.pieza_id || data.pieza });
        }, AI_FIRST_DELAY_MS);
      }
    } catch (error) {
      console.error('Error al solicitar jugada del agente Inteligente:', error);
      setAiError(error.message || 'Fallo al calcular jugada del agente Inteligente');
      setAiMoveCmd(null);
      setAiAutoFinishToken(null);
      setAiSequence(null);
      setAiSeqIndex(0);
      aiSeqTokenRef.current = null;
    } finally {
      setAiThinking(false);
    }
  };

  useEffect(() => {
    if (!isAITurn) return;
    if (showVictory || aiThinking) return;
    if (!partida?.id_partida) return;
    if (!dbJugadores[currentPlayerIndex]?.id_jugador) return;
    if (aiMoveCmd) return;
    if (aiSequence) return; // ya tenemos secuencia pendiente
    if (moveMade) return; // ya se movió esta ronda
    if (isPaused) return;

    requestAiMove();
  }, [isAITurn, showVictory, moveMade, aiThinking, partida?.id_partida, currentPlayerIndex, dbJugadores, aiMoveCmd, aiSequence, isPaused]); // eslint-disable-line react-hooks/exhaustive-deps

  const saveRoundToDatabase = async () => {
    try {
      const url = `http://localhost:8000/api/partidas/${partida.id_partida}/avanzar_ronda/`;
      const securePayload = buildRoundAdvancePayload({
        partidaId: partida.id_partida,
        actualRound,
        dbJugadores,
        currentPlayerIndex,
      });
      if (!securePayload) {
        console.error('No se pudo construir payload seguro para avanzar ronda');
        return null;
      }

      const { oldRound, newRoundCreated, nextNumero } = securePayload;

      console.log(`📊 Nueva ronda a crear: numero=${newRoundCreated.numero}`);
      
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ oldRound, newRoundCreated })
      });
      if (!res.ok) {
        console.error('Error al avanzar ronda:', res.status);
        return null;
      }
      const data = await res.json();
      const nuevaRonda = data?.nueva_ronda || data;
      console.log(`✅ Ronda actualizada en servidor: numero=${nuevaRonda?.numero}`);
      if (nuevaRonda?.id_ronda) {
        setActualRound({ id_ronda: nuevaRonda.id_ronda, numero: nuevaRonda.numero, inicio: nuevaRonda.inicio });
        const nextPlayerIdx = dbJugadores.findIndex(j => j.numero === nextNumero);
        if (nextPlayerIdx >= 0) setCurrentPlayerIndex(nextPlayerIdx);

        // Una vez validado el cambio de ronda/turno, quitar la recomendación visual del movimiento
        setHintMove(null);
      }
      return nuevaRonda;
    } catch (error) {
      console.error('Error en saveRoundToDatabase:', error);
      return null;
    }
  };

  const saveMoveToDatabase = async (moves) => {
    try {
      const jugadorId = dbJugadores[currentPlayerIndex]?.id_jugador;
      const rondaId = actualRound?.id_ronda;
      const allowedPieceIds = new Set(pieceByPos.values());
      const movimientos = buildSecureMovimientosPayload({
        moves,
        partidaId: partida.id_partida,
        jugadorId,
        rondaId,
        allowedPieceIds,
      });

      if (movimientos.length === 0) {
        console.warn('No hay movimientos completos para registrar');
        return;
      }
      console.log('Guardando movimientos IMP:', movimientos);
      const url = `http://localhost:8000/api/partidas/${partida.id_partida}/registrar_movimientos/`; //TODO
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ movimientos })
      });
      if (!response.ok) {
        const text = await response.text();
        console.error('Error al guardar movimientos:', response.status, text);
      }
    } catch (error) {
      console.error('Error en saveMoveToDatabase:', error);
    }
  };

  const handleBoardMove = (move) => {
    if (isPausedRef.current) return;
    setMoveMade(true);
    setLockedPiecePos(move.to);
    if (!originalPiecePos) {
      setOriginalPiecePos(move.from);
    }
    if (!initialBoardState && move.boardState) {
      setInitialBoardState(move.boardState);
    }
    if (!roundStartPieceByPos) {
      setRoundStartPieceByPos(new Map(pieceByPos));
      console.log('📸 Snapshot de pieceByPos guardado en Game.js:', pieceByPos);
    }
    const origenKey = `${move.from.col}-${move.from.fila}`;
    const piezaId = move.pieza_id ?? pieceByPos.get(origenKey) ?? null;

    if (!piezaId) {
      console.warn('Movimiento sin pieza_id; se omite registro de movimiento', { move, origenKey });
    } else {
      const nextMap = new Map(pieceByPos);
      nextMap.delete(origenKey);
      nextMap.set(`${move.to.col}-${move.to.fila}`, piezaId);
      setPieceByPos(nextMap);
    }
    setMoveHistory((prev) => [...prev, {
      from: move.from,
      to: move.to,
      occupant: move.occupant,
      pieza_id: piezaId,
    }]);

    // Si el agente Inteligente está ejecutando una secuencia, avanzar al siguiente paso
    if (isAITurn && aiSequence && aiSeqTokenRef.current) {
      setAiSeqIndex((idx) => idx + 1);
    }
  };

  const undoMove = () => {
    if (isPausedRef.current) return;
    if (!moveMade) return;
    setUndoToOriginalToken((prev) => prev + 1);
    setMoveMade(false);
    setLockedPiecePos(null);
    setOriginalPiecePos(null);
    setMoveHistory([]);
    
    if (roundStartPieceByPos) {
      setPieceByPos(new Map(roundStartPieceByPos));
      console.log('🔄 pieceByPos restaurado desde snapshot en Game.js:', roundStartPieceByPos);
    }
  };

  const continueRound = async () => {
    if (isPausedRef.current) return;
    if (!moveMade) return;
    if (moveHistory.length > 0) {
      await saveMoveToDatabase(moveHistory);
    }
    
    const hasWinner = await checkVictory();
    if (hasWinner) {
      return; 
    }

    await saveRoundToDatabase();
    setMoveMade(false);
    setLockedPiecePos(null);
    setOriginalPiecePos(null);
    setInitialBoardState(null);
    setMoveHistory([]);
    setRoundStartPieceByPos(null);
    setAiMoveCmd(null);
    setAiAutoFinishToken(null);
    setAiSequence(null);
    setAiSeqIndex(0);
    aiSeqTokenRef.current = null;
  };

  // Ejecutar secuencias del agente Inteligente paso a paso con retardo
  useEffect(() => {
    if (!isAITurn) return;
    if (!aiSequence || !aiSeqTokenRef.current) return;
    if (aiThinking) return;
    if (aiSeqIndex >= aiSequence.length) return;
    if (isPaused) return;

    const step = aiSequence[aiSeqIndex];
    const delay = aiSeqIndex === 0 ? AI_FIRST_DELAY_MS : AI_CHAIN_DELAY_MS;

    const timer = setTimeout(() => {
      if (isPausedRef.current) return;
      setAiMoveCmd({ token: Date.now(), ...step });
    }, delay);

    return () => clearTimeout(timer);
  }, [isAITurn, aiSequence, aiSeqIndex, aiThinking, isPaused]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!isAITurn) return;
    if (!moveMade) return;
    if (!moveHistory || moveHistory.length === 0) return;

    // Si hay una secuencia del agente Inteligente en curso, no cerrar ronda aún
    if (aiSequence && aiSeqIndex < (aiSequence?.length || 0)) return;
    if (isPaused) return;

    const autoAdvance = async () => {
      console.log('🤖 Auto-avanzando ronda del agente Inteligente...');
      await continueRound();
    };

    const timer = setTimeout(autoAdvance, 500);
    return () => clearTimeout(timer);
  }, [isAITurn, moveMade, moveHistory, aiSequence, aiSeqIndex, isPaused]); // eslint-disable-line react-hooks/exhaustive-deps

  const passRound = async () => {
    if (isPausedRef.current) return;
    await saveRoundToDatabase();
    setMoveMade(false);
    setLockedPiecePos(null);
    setOriginalPiecePos(null);
    setInitialBoardState(null);
    setMoveHistory([]);
    setRoundStartPieceByPos(null);
    setAiMoveCmd(null);
    setAiAutoFinishToken(null);
    setAiSequence(null);
    setAiSeqIndex(0);
    aiSeqTokenRef.current = null;
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

  if (loading) {
    return (
      <div className="game-container">
        <div className="loading">{t('game.loading')}</div>
      </div>
    );
  }

  return (
    <div className="game-container">
      <div className="game-layout">
        <aside className="turns-panel">
          <h3>{t('game.round.title')}</h3>
          <div className="turn-counter">{t('game.round.current', { round: roundCount })}</div>
          <div className="turns-list">
            {jugadoresConfig.length === 0 && (
              <p className="turns-empty">{t('game.round.noPlayerData')}</p>
            )}
            {jugadoresConfig.map((jugador, idx) => {
              const isCurrent = idx === currentPlayerIndex;
              const punta = activePuntas[idx];
              const colorHex = PLAYER_COLORS[punta];
              const displayName = resolveNombreJugador(jugador, dbJugadores[idx]);
              const keyBase = dbJugadores[idx]?.id_jugador || `${jugador?.nombre || 'Agente Inteligente'}-${idx}`;
              return (
                <div
                  key={keyBase}
                  className={`turn-card ${isCurrent ? 'current' : ''}`}
                >
                  <div className="turn-avatar">
                    <img src={getIconSrc(jugador.icono)} alt={displayName} />
                  </div>
                  <div className="turn-info">
                    <div className="turn-color-dot" style={{ backgroundColor: colorHex }} />
                    <span className="turn-name">{displayName}</span>
                    {isCurrent && <span className="turn-indicator">{t('game.round.currentIndicator')}</span>}
                  </div>
                </div>
              );
            })}
          </div>
        </aside>

        <main className="board-area">
          <div className="board-top">
            <button className="compact-button" onClick={toggleMusic}>
              <i className={`fas ${isPlayingMusic ? 'fa-volume-high' : 'fa-volume-xmark'}`}></i>
            </button>
            <div className="timer">⏱ {formatTime(elapsed)}</div>
            <button className="compact-button" onClick={handlePause}>
              <i className="fas fa-home"></i>
            </button>
          </div>

          <div className="board-container">
            <Board
              jugadoresConfig={jugadoresConfig}
              dbJugadores={dbJugadores}
              currentPlayerIndex={currentPlayerIndex}
              partidaId={partida?.id_partida}
              onMove={handleBoardMove}
              moveMade={moveMade}
              lockedPiecePos={lockedPiecePos}
              undoToOriginalToken={undoToOriginalToken}
              originalPiecePos={originalPiecePos}
              initialBoardState={initialBoardState}
              pieceByPos={pieceByPos}
              aiMove={aiMoveCmd}
              hintMove={hintMove}
              disablePlayerActions={isPaused || isAITurn || aiThinking}
              blockAiMoves={isPaused}
            />
          </div>

          <div className="game-controls">
            {partida?.estado === 'EN_CURSO' && !isAITurn && (
              <>
                {moveMade ? (
                  <>
                    <button className="control-button" onClick={continueRound} disabled={isPaused || isAITurn || aiThinking}>{t('game.controls.continue')}</button>
                    <button className="control-button" onClick={undoMove} disabled={isPaused || isAITurn || aiThinking}>{t('game.controls.undo')}</button>
                  </>
                ) : (
                  <button className="control-button" onClick={passRound} disabled={isPaused || isAITurn || aiThinking}>{t('game.controls.passRound')}</button>
                )}
              </>
            )}
          </div>
        </main>

        <aside className={`help-panel ${showHelp ? 'open' : ''}`}>
          <button
            className="help-toggle"
            onClick={() => {
              setShowHelp((prev) => {
                const next = !prev;
                if (!next) setShowChatInfo(false);
                return next;
              });
            }}
          >
            {showHelp ? t('game.help.close') : t('game.help.open')}
          </button>
          {showHelp && (
            <div className="help-content">
              <div className="help-header">
                <h3>{t('game.help.title')}</h3>
                <button
                  className="chatbot-infoButton"
                  type="button"
                  aria-label={t('game.help.examples.ariaLabel')}
                  aria-expanded={showChatInfo}
                  onClick={() => setShowChatInfo((prev) => !prev)}
                >
                  i
                </button>
              </div>

              {showChatInfo && (
                <div className="chatbot-infoPanel">
                  <div className="chatbot-infoTitle">{t('game.help.examples.title')}</div>
                  <ul className="chatbot-infoList">
                    {t('game.help.examples.questions', { returnObjects: true }).map((q, i) => (
                      <li key={i}>{q}</li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="chatbot">
                <div className="chatbot-messages" aria-live="polite">
                  {chatMessages.length === 0 ? (
                    <p className="help-placeholder">{t('game.help.placeholder')}</p>
                  ) : (
                    chatMessages.map((m, idx) => (
                      <div
                        key={idx}
                        className={`chatbot-message ${m.role === 'user' ? 'user' : 'assistant'}`}
                      >
                        <div className="chatbot-bubble">
                          <div className="chatbot-author">{m.role === 'user' ? t('common.you') : t('game.chat.assistantName')}</div>
                          <div className="chatbot-text">{m.text}</div>
                        </div>
                      </div>
                    ))
                  )}
                </div>

                {chatError && <div className="chatbot-error">{chatError}</div>}

                <div className="chatbot-inputRow">
                  <input
                    className="chatbot-input"
                    type="text"
                    value={chatInput}
                    placeholder={t('game.chat.inputPlaceholder')}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') sendChatMessage();
                    }}
                    disabled={chatLoading}
                  />
                  <button
                    className="chatbot-sendButton"
                    onClick={sendChatMessage}
                    disabled={chatLoading}
                    type="button"
                  >
                    {chatLoading ? t('common.sending') : t('common.send')}
                  </button>
                </div>
              </div>
            </div>
          )}
        </aside>
      </div>

      {isPaused && (
        <div className="pause-overlay">
          <div className="pause-dialog">
            <h2>{t('game.pause.title')}</h2>
            <div className="pause-buttons">
              <button className="pause-button resume-button" onClick={handleResume}>
                <i className="fas fa-play"></i>
                {t('game.pause.resume')}
              </button>
              <button className="pause-button end-button" onClick={handleShowEndConfirm}>
                <i className="fas fa-stop"></i>
                {t('game.pause.end')}
              </button>
            </div>
          </div>
        </div>
      )}

      {showEndConfirm && (
        <div className="confirm-overlay">
          <div className="confirm-dialog">
            <h2>{t('game.confirm.title')}</h2>
            <p className="confirm-question">
              {t('game.confirm.question')}
            </p>
            <p className="confirm-warning">
              {t('game.confirm.warning')}
            </p>
            <div className="confirm-buttons">
              <button className="confirm-button cancel-button" onClick={handleCancelEnd}>
                {t('game.confirm.cancel')}
              </button>
              <button className="confirm-button confirm-end-button" onClick={handleEndGame}>
                {t('game.confirm.backHome')}
              </button>
            </div>
          </div>
        </div>
      )}

      {showVictory && victoryData && (
        <Victory
          ganador={victoryData.ganador}
          perdedores={victoryData.perdedores}
          rondas={victoryData.rondas}
          tiempo={victoryData.tiempo}
          totalJugadores={victoryData.totalJugadores}
          onVolverInicio={handleEndGame}
        />
      )}
    </div>
  );
}

export default Game;