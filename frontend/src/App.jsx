import { useState, useEffect, useRef } from 'react'
import { Mic, MicOff, Activity, Send, Bot, User } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

function App() {
  const [status, setStatus] = useState('Disconnected')
  const [activeAgent, setActiveAgent] = useState('System')
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isListening, setIsListening] = useState(false)
  const ws = useRef(null)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    connectWebSocket()
    return () => ws.current?.close()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const connectWebSocket = () => {
    ws.current = new WebSocket('ws://localhost:8000/ws/chat')
    
    ws.current.onopen = () => {
      setStatus('Connected')
      addMessage('System connected to Jarvis Core.', 'system')
    }

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'response' || data.type === 'error') {
        addMessage(data.text, 'jarvis')
        if (data.agent) setActiveAgent(data.agent)
      }
    }

    ws.current.onclose = () => setStatus('Disconnected')
  }

  const addMessage = (text, sender) => {
    setMessages(prev => [...prev, { id: Date.now(), text, sender }])
  }

  const handleSendMessage = (e) => {
    e.preventDefault()
    if (!inputValue.trim()) return

    const text = inputValue.trim()
    addMessage(text, 'user')
    
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(text)
    }
    
    setInputValue('')
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
      addMessage('Error: Browser does not support speech recognition.', 'system')
      return
    }

    const recognition = new window.webkitSpeechRecognition()
    recognition.continuous = false
    recognition.lang = 'en-US'
    recognition.interimResults = false

    recognition.onstart = () => {
      setIsListening(true)
    }

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      addMessage(transcript, 'user')
      if (ws.current && ws.current.readyState === WebSocket.OPEN) {
        ws.current.send(transcript)
      }
    }

    recognition.onerror = (event) => {
      addMessage(`Voice Error: ${event.error}`, 'system')
      setIsListening(false)
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    recognition.start()
  }

  const stopListening = () => {
    setIsListening(false)
  }

  return (
    <div className="min-h-screen bg-gray-950 text-cyan-500 font-mono p-4 md:p-8 flex flex-col items-center justify-center relative overflow-hidden">
      
      {/* Background Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-cyan-900/20 blur-[100px] rounded-full pointer-events-none" />

      <div className="z-10 w-full max-w-3xl flex flex-col h-[90vh] bg-gray-900/40 backdrop-blur-md border border-cyan-900/50 rounded-2xl overflow-hidden shadow-2xl">
        
        {/* Header */}
        <header className="flex justify-between items-center p-4 border-b border-cyan-900/50 bg-gray-900/80">
          <div className="flex items-center gap-3">
            <Activity className="w-6 h-6 animate-pulse text-cyan-400" />
            <h1 className="text-xl font-bold tracking-tighter text-white">
              JARVIS <span className="text-xs bg-cyan-900/50 px-2 py-1 rounded text-cyan-300 ml-1">V2.0</span>
            </h1>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2 text-cyan-400/80 bg-gray-800/50 px-3 py-1 rounded-full border border-gray-700/50">
              <Bot className="w-4 h-4" />
              <span>{activeAgent}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${status === 'Connected' ? 'bg-green-500 shadow-[0_0_10px_#22c55e]' : 'bg-red-500'}`} />
              <span className="hidden sm:inline text-gray-400">{status}</span>
            </div>
          </div>
        </header>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-gray-500 opacity-50">
              <Activity className="w-16 h-16 mb-4" />
              <p>Jarvis is online. How can I help you?</p>
            </div>
          )}
          <AnimatePresence initial={false}>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                className={`flex w-full ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex gap-3 max-w-[85%] ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                  
                  {/* Avatar */}
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    msg.sender === 'user' 
                      ? 'bg-blue-600/20 text-blue-400' 
                      : msg.sender === 'system'
                        ? 'bg-gray-800 text-gray-400'
                        : 'bg-cyan-600/20 text-cyan-400 border border-cyan-500/30'
                  }`}>
                    {msg.sender === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
                  </div>

                  {/* Message Bubble */}
                  <div className={`px-4 py-3 rounded-2xl text-sm md:text-base leading-relaxed whitespace-pre-wrap ${
                    msg.sender === 'user'
                      ? 'bg-blue-600/20 border border-blue-500/30 text-blue-100 rounded-tr-sm'
                      : msg.sender === 'system'
                        ? 'bg-transparent text-gray-500 italic text-xs'
                        : 'bg-gray-800/60 border border-gray-700 text-gray-200 rounded-tl-sm'
                  }`}>
                    {msg.text}
                  </div>

                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 bg-gray-900/80 border-t border-cyan-900/50">
          <form onSubmit={handleSendMessage} className="flex gap-2 items-end">
            <div className="flex-1 relative">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Message Jarvis..."
                className="w-full bg-black/50 border border-gray-700 text-white rounded-xl px-4 py-4 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all"
              />
            </div>
            
            <button
              type="button"
              onClick={toggleListening}
              className={`p-4 rounded-xl transition-all duration-300 flex-shrink-0 flex items-center justify-center border ${
                isListening 
                  ? 'bg-red-500/20 text-red-500 border-red-500/50 shadow-[0_0_15px_#ef444455]' 
                  : 'bg-gray-800 text-cyan-500 border-gray-700 hover:bg-gray-700'
              }`}
            >
              {isListening ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
            </button>

            <button
              type="submit"
              disabled={!inputValue.trim()}
              className="p-4 bg-cyan-600/20 text-cyan-400 border border-cyan-500/50 rounded-xl hover:bg-cyan-600/40 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex-shrink-0 flex items-center justify-center"
            >
              <Send className="w-6 h-6" />
            </button>
          </form>
        </div>

      </div>
    </div>
  )
}

export default App

