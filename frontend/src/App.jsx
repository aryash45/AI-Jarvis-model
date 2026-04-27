import { useState, useEffect, useRef } from 'react'
import { Mic, MicOff, Plus, Send, MessageSquare, History, Settings, User, Zap, Globe, Pencil } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

/* ─────────────────────────────────────────
   DESIGN TOKENS — Aether Command System
   ───────────────────────────────────────── */
// bg:          #0c0e13   (the void)
// surface:     #111319   (panel base)
// surface-hi:  #1d2026   (cards / user chip)
// surface-br:  #292c34   (hover / active)
// primary:     #a8a4ff   (violet)
// primary-dim: #675df9
// tertiary:    #ff9dd0   (neural pulse pink)
// text:        #ededf5
// muted:       #aaabb2

/* ─── Glowing Hexagon "J" logo ─── */
function JarvisLogo({ size = 32 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none">
      <polygon
        points="16,2 28,9 28,23 16,30 4,23 4,9"
        fill="none"
        stroke="#a8a4ff"
        strokeWidth="1.5"
        filter="url(#glow)"
      />
      <defs>
        <filter id="glow">
          <feGaussianBlur stdDeviation="1.5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <text
        x="16" y="21"
        textAnchor="middle"
        fontFamily="'Space Grotesk', sans-serif"
        fontSize="13"
        fontWeight="700"
        fill="#a8a4ff"
        letterSpacing="-0.5"
      >
        J
      </text>
    </svg>
  )
}

/* ─── Pulsing orb (welcome state) ─── */
function JarvisOrb() {
  return (
    <div style={{ position: 'relative', width: 120, height: 120, margin: '0 auto 32px' }}>
      {/* Outer pulsing ring */}
      <div style={{
        position: 'absolute', inset: 0,
        borderRadius: '50%',
        border: '1.5px solid rgba(168,164,255,0.3)',
        animation: 'orbPulse 2.8s ease-in-out infinite',
      }} />
      {/* Mid ring */}
      <div style={{
        position: 'absolute', inset: 12,
        borderRadius: '50%',
        border: '1.5px solid rgba(168,164,255,0.5)',
        animation: 'orbPulse 2.8s ease-in-out infinite 0.4s',
      }} />
      {/* Core */}
      <div style={{
        position: 'absolute', inset: 24,
        borderRadius: '50%',
        background: 'radial-gradient(circle, #a8a4ff 0%, #675df9 60%, #3d2fc7 100%)',
        boxShadow: '0 0 40px rgba(168,164,255,0.4), 0 0 80px rgba(103,93,249,0.2)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <span style={{
          fontFamily: "'Space Grotesk', sans-serif",
          fontSize: 22, fontWeight: 700,
          color: '#fff',
          letterSpacing: '-0.5px',
        }}>J</span>
      </div>
      <style>{`
        @keyframes orbPulse {
          0%, 100% { transform: scale(1); opacity: 0.6; }
          50%       { transform: scale(1.08); opacity: 1; }
        }
        @keyframes neuralPing {
          0%, 100% { transform: scale(1); opacity: 1; }
          50%       { transform: scale(1.6); opacity: 0; }
        }
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  )
}

/* ─── Typewriter ─── */
function TypewriterText({ text }) {
  const [shown, setShown] = useState('')
  useEffect(() => {
    let i = 0
    setShown('')
    const id = setInterval(() => {
      setShown(text.substring(0, i))
      i++
      if (i > text.length) clearInterval(id)
    }, 12)
    return () => clearInterval(id)
  }, [text])
  return <span>{shown}</span>
}

/* ─── Neural Pulse tag ─── */
function NeuralPulse() {
  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, marginTop: 8 }}>
      <div style={{ position: 'relative', width: 8, height: 8 }}>
        <div style={{
          position: 'absolute', inset: 0, borderRadius: '50%',
          background: '#ff9dd0',
          animation: 'neuralPing 1.6s ease-in-out infinite',
        }} />
        <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', background: '#ff9dd0' }} />
      </div>
      <span style={{ fontFamily: 'Inter, sans-serif', fontSize: 11, color: '#ff9dd0', letterSpacing: '0.04em' }}>
        Neural Pulse
      </span>
    </div>
  )
}

/* ═══════════════════════════════════════════
   MAIN APP
   ═══════════════════════════════════════════ */
function App() {
  const [status, setStatus] = useState('Disconnected')
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [inputFocused, setInputFocused] = useState(false)
  const ws = useRef(null)
  const endRef = useRef(null)

  useEffect(() => { connectWebSocket(); return () => ws.current?.close() }, [])
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const connectWebSocket = () => {
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/chat'
    ws.current = new WebSocket(wsUrl)
    ws.current.onopen  = () => setStatus('Connected')
    ws.current.onmessage = (e) => {
      const d = JSON.parse(e.data)
      if (d.type === 'response' || d.type === 'error') addMessage(d.text, 'jarvis')
    }
    ws.current.onclose = () => setStatus('Disconnected')
  }

  const addMessage = (text, sender) =>
    setMessages(prev => [...prev, { id: Date.now(), text, sender }])

  const handleSend = (e) => {
    e?.preventDefault()
    const text = inputValue.trim()
    if (!text) return
    addMessage(text, 'user')
    if (ws.current?.readyState === WebSocket.OPEN) ws.current.send(text)
    setInputValue('')
  }

  const handleSuggestion = (text) => {
    setInputValue(text)
    setTimeout(() => {
      addMessage(text, 'user')
      if (ws.current?.readyState === WebSocket.OPEN) ws.current.send(text)
      setInputValue('')
    }, 80)
  }

  const toggleListening = () => {
    if (isListening) { setIsListening(false); return }
    if (!('webkitSpeechRecognition' in window)) return
    const r = new window.webkitSpeechRecognition()
    r.continuous = false; r.lang = 'en-US'
    r.onstart  = () => setIsListening(true)
    r.onresult = (ev) => setInputValue(p => p + ev.results[0][0].transcript)
    r.onerror  = () => setIsListening(false)
    r.onend    = () => setIsListening(false)
    r.start()
  }

  const connected = status === 'Connected'

  /* ── Sidebar icon items ── */
  const sideItems = [
    { icon: <MessageSquare size={20} />, label: 'New Chat',  action: () => setMessages([]) },
    { icon: <History size={20} />,       label: 'History',   action: () => {} },
    { icon: <Settings size={20} />,      label: 'Settings',  action: () => {} },
  ]

  const suggestions = [
    { icon: <Zap size={14} />, text: 'Explain quantum entanglement' },
    { icon: <Globe size={14} />, text: 'What happened in 1969?' },
    { icon: <Pencil size={14} />, text: 'Help me write an email' },
  ]

  /* ── Inline styles ── */
  const S = {
    root: {
      display: 'flex', height: '100vh', width: '100vw',
      background: '#0c0e13', color: '#ededf5',
      fontFamily: 'Inter, sans-serif', overflow: 'hidden',
    },
    sidebar: {
      width: 58, flexShrink: 0,
      background: '#0c0e13',
      borderRight: '1px solid rgba(255,255,255,0.05)',
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', paddingTop: 16, paddingBottom: 16,
      gap: 0,
    },
    sideBtn: (active) => ({
      width: 40, height: 40,
      borderRadius: 10,
      border: 'none',
      background: active ? 'rgba(168,164,255,0.12)' : 'transparent',
      color: active ? '#a8a4ff' : '#6b7280',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      cursor: 'pointer', marginBottom: 4,
      transition: 'all 0.15s ease',
    }),
    main: {
      flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden',
      background: '#0c0e13',
      position: 'relative',
    },
    topBar: {
      position: 'absolute', top: 0, left: 0, right: 0, zIndex: 10,
      display: 'flex', justifyContent: 'flex-end', alignItems: 'center',
      padding: '14px 20px',
      pointerEvents: 'none',
    },
    statusDot: {
      display: 'inline-flex', alignItems: 'center', gap: 6,
      fontFamily: 'Inter, sans-serif', fontSize: 12,
      color: connected ? '#6b7280' : '#6b7280',
      letterSpacing: '0.02em',
    },
    scrollArea: {
      flex: 1, overflowY: 'auto', overflowX: 'hidden',
      paddingTop: 56, paddingBottom: 160,
      scrollbarWidth: 'none',
    },
    chatCol: {
      maxWidth: 720, margin: '0 auto', padding: '0 20px',
    },
    /* Welcome */
    welcome: {
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'center', minHeight: 'calc(100vh - 240px)',
      animation: 'fadeUp 0.5s ease',
    },
    title: {
      fontFamily: "'Space Grotesk', sans-serif",
      fontSize: 42, fontWeight: 700,
      letterSpacing: '-1.5px', color: '#ededf5',
      marginBottom: 6,
    },
    subtitle: {
      fontFamily: 'Inter, sans-serif', fontSize: 13,
      color: '#6b7280', letterSpacing: '0.12em', textTransform: 'uppercase',
      marginBottom: 40,
    },
    chipRow: {
      display: 'flex', gap: 10, flexWrap: 'wrap', justifyContent: 'center',
    },
    chip: {
      display: 'inline-flex', alignItems: 'center', gap: 7,
      padding: '9px 18px',
      border: '1px solid rgba(168,164,255,0.3)',
      borderRadius: 100,
      background: 'rgba(168,164,255,0.05)',
      color: '#aaabb2', fontSize: 13,
      cursor: 'pointer', transition: 'all 0.15s ease',
      fontFamily: 'Inter, sans-serif',
    },
    /* Messages */
    userMsg: {
      display: 'flex', justifyContent: 'flex-end', marginBottom: 20,
      animation: 'fadeUp 0.25s ease',
    },
    userBubble: {
      maxWidth: '70%',
      background: '#1d2026',
      borderRadius: 14,
      padding: '10px 16px',
      fontSize: 14.5, lineHeight: 1.65,
      color: '#ededf5',
      boxShadow: '0 2px 12px rgba(0,0,0,0.25)',
    },
    aiMsg: {
      display: 'flex', alignItems: 'flex-start', gap: 14,
      marginBottom: 28,
      animation: 'fadeUp 0.25s ease',
    },
    aiIconWrap: {
      flexShrink: 0, marginTop: 2,
    },
    aiText: {
      flex: 1, fontSize: 14.5, lineHeight: 1.75,
      color: '#d4d6e0',
      fontFamily: 'Inter, sans-serif',
      whiteSpace: 'pre-wrap',
    },
    /* Input */
    inputBar: {
      position: 'absolute', bottom: 0, left: 0, right: 0,
      padding: '0 0 20px',
      background: 'linear-gradient(to top, #0c0e13 70%, transparent)',
    },
    inputInner: {
      maxWidth: 720, margin: '0 auto', padding: '0 20px',
    },
    inputForm: (focused) => ({
      display: 'flex', alignItems: 'center', gap: 4,
      background: '#111319',
      border: `1px solid ${focused ? 'rgba(168,164,255,0.45)' : 'rgba(255,255,255,0.06)'}`,
      borderRadius: 100,
      padding: '6px 8px 6px 12px',
      boxShadow: focused ? '0 0 0 3px rgba(168,164,255,0.08), 0 4px 20px rgba(168,164,255,0.06)' : 'none',
      transition: 'all 0.2s ease',
    }),
    inputField: {
      flex: 1, background: 'transparent', border: 'none', outline: 'none',
      color: '#ededf5', fontSize: 14, fontFamily: 'Inter, sans-serif',
      padding: '8px 4px',
    },
    iconBtn: (active, color) => ({
      width: 34, height: 34, borderRadius: 100,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      border: 'none', cursor: 'pointer',
      background: active ? 'rgba(239,68,68,0.15)' : 'transparent',
      color: active ? '#ef4444' : (color || '#6b7280'),
      transition: 'all 0.15s ease',
    }),
    sendBtn: {
      width: 34, height: 34, borderRadius: 100,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      border: 'none', cursor: 'pointer',
      background: 'linear-gradient(135deg, #a8a4ff 0%, #675df9 100%)',
      color: '#fff',
      boxShadow: '0 2px 12px rgba(168,164,255,0.3)',
      flexShrink: 0,
    },
    footerNote: {
      textAlign: 'center', fontSize: 11,
      color: '#374151', marginTop: 10,
      fontFamily: 'Inter, sans-serif',
    },
    suggestionRow: {
      display: 'flex', gap: 8, marginTop: 10,
      overflowX: 'auto', scrollbarWidth: 'none',
    },
    suggestionChip: {
      display: 'inline-flex', alignItems: 'center', gap: 6,
      padding: '7px 14px',
      border: '1px solid rgba(255,255,255,0.07)',
      borderRadius: 100,
      background: 'rgba(255,255,255,0.03)',
      color: '#6b7280', fontSize: 12.5,
      cursor: 'pointer', whiteSpace: 'nowrap',
      fontFamily: 'Inter, sans-serif',
      transition: 'all 0.15s ease',
    },
  }

  return (
    <>
      {/* Google Fonts */}
      <link
        rel="preconnect"
        href="https://fonts.googleapis.com"
      />
      <link
        href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@600;700&display=swap"
        rel="stylesheet"
      />

      <div style={S.root}>
        {/* ── SIDEBAR ── */}
        <nav style={S.sidebar}>
          {/* Logo */}
          <div style={{ marginBottom: 20 }}>
            <JarvisLogo size={32} />
          </div>

          {/* Nav items */}
          {sideItems.map(({ icon, label, action }, i) => (
            <button
              key={i}
              style={S.sideBtn(i === 0 && messages.length === 0)}
              onClick={action}
              title={label}
            >
              {icon}
            </button>
          ))}

          {/* Spacer */}
          <div style={{ flex: 1 }} />

          {/* User avatar */}
          <div style={{
            width: 32, height: 32, borderRadius: '50%',
            background: 'linear-gradient(135deg, #675df9, #a8a4ff)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontFamily: "'Space Grotesk', sans-serif",
            fontSize: 13, fontWeight: 700, color: '#fff',
            cursor: 'pointer',
          }}>
            A
          </div>
        </nav>

        {/* ── MAIN AREA ── */}
        <main style={S.main}>
          {/* Status badge */}
          <div style={S.topBar}>
            <div style={S.statusDot}>
              <span style={{
                width: 7, height: 7, borderRadius: '50%',
                background: connected ? '#34d399' : '#6b7280',
                display: 'inline-block',
                boxShadow: connected ? '0 0 6px rgba(52,211,153,0.6)' : 'none',
              }} />
              {connected ? 'Neural Link Active' : 'Offline'}
            </div>
          </div>

          {/* Scroll area */}
          <div style={S.scrollArea}>
            <div style={S.chatCol}>
              {messages.length === 0 ? (
                /* ── Welcome ── */
                <div style={S.welcome}>
                  <JarvisOrb />
                  <h1 style={S.title}>JARVIS</h1>
                  <p style={S.subtitle}>Neural Interface Active</p>
                  <div style={S.chipRow}>
                    {suggestions.map(({ icon, text }) => (
                      <button
                        key={text}
                        style={S.chip}
                        onClick={() => handleSuggestion(text)}
                        onMouseEnter={e => {
                          e.currentTarget.style.borderColor = 'rgba(168,164,255,0.6)'
                          e.currentTarget.style.color = '#ededf5'
                          e.currentTarget.style.background = 'rgba(168,164,255,0.08)'
                        }}
                        onMouseLeave={e => {
                          e.currentTarget.style.borderColor = 'rgba(168,164,255,0.3)'
                          e.currentTarget.style.color = '#aaabb2'
                          e.currentTarget.style.background = 'rgba(168,164,255,0.05)'
                        }}
                      >
                        <span style={{ color: '#675df9' }}>{icon}</span>
                        {text}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                /* ── Messages ── */
                <AnimatePresence initial={false}>
                  {messages.map((msg) => msg.sender === 'user' ? (
                    <motion.div
                      key={msg.id}
                      style={S.userMsg}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <div style={S.userBubble}>{msg.text}</div>
                    </motion.div>
                  ) : (
                    <motion.div
                      key={msg.id}
                      style={S.aiMsg}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <div style={S.aiIconWrap}>
                        <JarvisLogo size={26} />
                      </div>
                      <div>
                        <div style={S.aiText}>
                          <TypewriterText text={msg.text} />
                        </div>
                        <NeuralPulse />
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              )}
              <div ref={endRef} />
            </div>
          </div>

          {/* ── Input bar ── */}
          <div style={S.inputBar}>
            <div style={S.inputInner}>
              <form
                onSubmit={handleSend}
                style={S.inputForm(inputFocused)}
              >
                <input
                  type="text"
                  value={inputValue}
                  onChange={e => setInputValue(e.target.value)}
                  onFocus={() => setInputFocused(true)}
                  onBlur={() => setInputFocused(false)}
                  placeholder="Ask Jarvis anything..."
                  style={{
                    ...S.inputField,
                    '::placeholder': { color: '#374151' },
                  }}
                />
                <button
                  type="button"
                  onClick={toggleListening}
                  style={S.iconBtn(isListening)}
                  title={isListening ? 'Stop' : 'Voice input'}
                >
                  {isListening ? <MicOff size={17} /> : <Mic size={17} />}
                </button>
                {inputValue.trim() && (
                  <motion.button
                    type="submit"
                    style={S.sendBtn}
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0, opacity: 0 }}
                    transition={{ type: 'spring', stiffness: 400, damping: 20 }}
                  >
                    <Send size={15} />
                  </motion.button>
                )}
              </form>

              {/* Quick action chips */}
              {messages.length === 0 && (
                <div style={S.suggestionRow}>
                  {suggestions.map(({ icon, text }) => (
                    <button
                      key={text}
                      style={S.suggestionChip}
                      onClick={() => handleSuggestion(text)}
                      onMouseEnter={e => {
                        e.currentTarget.style.color = '#aaabb2'
                        e.currentTarget.style.borderColor = 'rgba(168,164,255,0.2)'
                      }}
                      onMouseLeave={e => {
                        e.currentTarget.style.color = '#6b7280'
                        e.currentTarget.style.borderColor = 'rgba(255,255,255,0.07)'
                      }}
                    >
                      <span style={{ color: '#675df9' }}>{icon}</span>
                      {text}
                    </button>
                  ))}
                </div>
              )}

              <p style={S.footerNote}>Jarvis may occasionally hallucinate. Verify critical information.</p>
            </div>
          </div>
        </main>
      </div>

      <style>{`
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #0c0e13; }
        input::placeholder { color: #374151; }
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(10px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes orbPulse {
          0%,100% { transform: scale(1); opacity: 0.6; }
          50%     { transform: scale(1.08); opacity: 1; }
        }
        @keyframes neuralPing {
          0%,100% { transform: scale(1); opacity: 1; }
          50%     { transform: scale(1.8); opacity: 0; }
        }
        /* Hide scrollbars globally */
        ::-webkit-scrollbar { display: none; }
        * { scrollbar-width: none; }
      `}</style>
    </>
  )
}

export default App
