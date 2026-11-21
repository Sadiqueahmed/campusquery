import React, { useState, useRef, useEffect } from 'react';
import { GraduationCap, Trash2 } from 'lucide-react';
import { sendQuestion } from './api';
import ChatMessage from './components/ChatMessage';
import SampleQuestions from './components/SampleQuestions';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to the latest message
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (text) => {
    const question = (text || input).trim();
    if (!question || loading) return;

    // Add user message
    const userMsg = { role: 'user', content: question };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const data = await sendQuestion(question);
      const assistantMsg = { role: 'assistant', ...data };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          answer: 'Could not reach the server. Make sure the backend is running on port 8000.',
          error: { code: 'network_error', message: err.message },
          columns: [],
          rows: [],
          row_count: 0,
          csv_available: false,
        },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setInput('');
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto">
      {/* ── Header ── */}
      <header className="flex items-center justify-between px-4 py-3 border-b bg-white sticky top-0 z-10">
        <div className="flex items-center gap-2">
          <GraduationCap className="w-7 h-7 text-indigo-600" />
          <div>
            <h1 className="text-lg font-bold text-gray-900">Student Data Q&A Assistant</h1>
            <p className="text-xs text-gray-500">Ask questions about students, courses, and enrollments</p>
          </div>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearChat}
            className="flex items-center gap-1 text-xs text-gray-500 hover:text-red-500 transition-colors px-2 py-1 rounded hover:bg-red-50"
            aria-label="Clear chat history"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Clear Chat
          </button>
        )}
      </header>

      {/* ── Chat Feed ── */}
      <main className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {/* Empty state */}
        {messages.length === 0 && !loading && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <GraduationCap className="w-16 h-16 text-indigo-200 mb-4" />
            <h2 className="text-xl font-semibold text-gray-700 mb-2">Welcome to CampusQuery</h2>
            <p className="text-gray-500 mb-6 max-w-md">
              Ask any question about students, courses, grades, and enrollments.
              Your query will be converted to SQL and run against the database in real-time.
            </p>
            <SampleQuestions onSelect={handleSend} />
          </div>
        )}

        {/* Messages */}
        {messages.map((msg, i) => (
          <ChatMessage key={i} message={msg} />
        ))}

        {/* Typing indicator */}
        {loading && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0">
              <GraduationCap className="w-4 h-4 text-indigo-600" />
            </div>
            <div className="bg-white border rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
              <div className="flex gap-1">
                <span className="typing-dot w-2 h-2 bg-gray-400 rounded-full inline-block" />
                <span className="typing-dot w-2 h-2 bg-gray-400 rounded-full inline-block" />
                <span className="typing-dot w-2 h-2 bg-gray-400 rounded-full inline-block" />
              </div>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </main>

      {/* ── Sample questions (compact row, always visible after first message) ── */}
      {messages.length > 0 && (
        <div className="px-4 pb-1">
          <SampleQuestions onSelect={handleSend} compact />
        </div>
      )}

      {/* ── Input ── */}
      <footer className="border-t bg-white px-4 py-3 sticky bottom-0">
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about student data…"
            disabled={loading}
            rows={1}
            className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Question input"
          />
          <button
            onClick={() => handleSend()}
            disabled={loading || !input.trim()}
            className="px-5 py-2.5 bg-indigo-600 text-white text-sm font-medium rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="Send question"
          >
            Send
          </button>
        </div>
      </footer>
    </div>
  );
}
