import { useState, useEffect, useRef } from 'react'
import { Mic, MicOff, Activity, Terminal } from 'lucide-react'
import { motion } from 'framer-motion'

function App() {
  const [status, setStatus] = useState('Disconnected')
  const [activeAgent, setActiveAgent] = useState('System')
  const [logs, setLogs] = useState([])
  const [isListening, setIsListening] = useState(false)
  const ws = useRef(null)

  useEffect(() => {
    connectWebSocket()
    return () => ws.current?.close()
  }, [])

  const connectWebSocket = () => {
    ws.current = new WebSocket('ws://localhost:8000/ws/chat')
    
    ws.current.onopen = () => {
      setStatus('Connected')
      addLog('System connected to Jarvis Core.')
    }

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'response') {
        addLog(`[${data.agent}] ${data.text}`)
        setActiveAgent(data.agent)
      }
    }

    ws.current.onclose = () => setStatus('Disconnected')
  }

  const addLog = (message) => {
    setLogs(prev => [...prev.slice(-4), message])
  }

  const toggleListening = () => {
    if (isListening) {
      stopListening()
    } else {
      startListening()
    }
  }

  const startListening = () => {
    if (!('webkitSpeechRecognition' in window)) {
      addLog('Error: Browser does not support speech recognition.')
      return
    }

    const recognition = new window.webkitSpeechRecognition()
    recognition.continuous = false
    recognition.lang = 'en-US'
    recognition.interimResults = false

    recognition.onstart = () => {
      setIsListening(true)
      addLog('Listening...')
    }

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      addLog(`You: ${transcript}`)
      if (ws.current && ws.current.readyState === WebSocket.OPEN) {
        ws.current.send(transcript)
      }
    }

    recognition.onerror = (event) => {
      addLog(`Error: ${event.error}`)
      setIsListening(false)
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    recognition.start()
  }

  const stopListening = () => {
    setIsListening(false)
    // Note: webkitSpeechRecognition doesn't have a clean 'stop' method that we can access easily 
    // if we don't store the instance, but since we set continuous=false, it stops automatically after one sentence.
    // For a toggle off, we just update state.
  }

  return (
    <div className="min-h-screen bg-gray-950 text-cyan-500 font-mono p-8 flex flex-col items-center justify-center relative overflow-hidden">
      
      {/* Background Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-cyan-900/20 blur-[100px] rounded-full pointer-events-none" />

      <div className="z-10 w-full max-w-2xl space-y-8">
        
        {/* Header */}
        <header className="flex justify-between items-center border-b border-cyan-900/50 pb-4">
          <h1 className="text-3xl font-bold tracking-tighter flex items-center gap-2">
            <Activity className="w-8 h-8 animate-pulse" />
            JARVIS <span className="text-xs bg-cyan-900/50 px-2 py-1 rounded">V2.0</span>
          </h1>
          <div className="flex items-center gap-2 text-sm">
            <div className={`w-2 h-2 rounded-full ${status === 'Connected' ? 'bg-green-500 shadow-[0_0_10px_#22c55e]' : 'bg-red-500'}`} />
            {status}
          </div>
        </header>

        {/* Active Agent Card */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gray-900/50 backdrop-blur-md border border-cyan-900/50 p-6 rounded-xl relative overflow-hidden group"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <h2 className="text-sm text-cyan-400/60 uppercase tracking-widest mb-2">Active Agent</h2>
          <div className="text-2xl font-bold text-white flex items-center gap-3">
            {activeAgent === 'ResearchAgent' && '🕵️'}
            {activeAgent === 'MediaAgent' && '🎵'}
            {activeAgent === 'SystemAgent' && '⚙️'}
            {activeAgent === 'WebAgent' && '🌐'}
            {activeAgent}
          </div>
        </motion.div>

        {/* Terminal Logs */}
        <div className="bg-black/80 border border-gray-800 rounded-lg p-4 h-64 overflow-y-auto font-mono text-sm shadow-inner">
          {logs.map((log, i) => (
            <motion.div 
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="mb-2 border-l-2 border-cyan-800 pl-2"
            >
              <span className="text-gray-500">[{new Date().toLocaleTimeString()}]</span> {log}
            </motion.div>
          ))}
          {logs.length === 0 && <span className="text-gray-600 italic">Waiting for input...</span>}
        </div>

        {/* Controls */}
        <div className="flex justify-center gap-4">
          <button 
            onClick={toggleListening}
            className={`p-4 rounded-full transition-all duration-300 ${isListening ? 'bg-red-500/20 text-red-500 shadow-[0_0_20px_#ef444455]' : 'bg-cyan-500/20 text-cyan-500 hover:bg-cyan-500/30'}`}
          >
            {isListening ? <MicOff className="w-8 h-8" /> : <Mic className="w-8 h-8" />}
          </button>
        </div>

      </div>
    </div>
  )
}

export default App
