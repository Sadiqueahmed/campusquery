import React, { useState, useRef, useEffect, useCallback } from 'react';
import { GraduationCap, Trash2, History, Send, Loader2 } from 'lucide-react';
import { sendQuestion, fetchHistory, clearHistory } from './api';
import ChatMessage from './components/ChatMessage';
import SampleQuestions from './components/SampleQuestions';
import HistoryDrawer from './components/HistoryDrawer';
import ThemeToggle from './components/ThemeToggle';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [historyList, setHistoryList] = useState([]);
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  // Load history from backend
  const loadHistory = useCallback(async () => {
    try {
      const data = await fetchHistory();
      if (Array.isArray(data)) {
        setHistoryList(data);
      }
    } catch (err) {
      console.warn('Failed to fetch history:', err);
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

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
      // Refresh history log after new question
      loadHistory();
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

  const handleClearChat = () => {
    setMessages([]);
    setInput('');
  };

  const handleClearHistory = async () => {
    try {
      await clearHistory();
      setHistoryList([]);
    } catch (err) {
      alert('Failed to clear history: ' + err.message);
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 transition-colors">
      {/* ── Header ── */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-800 bg-white/90 dark:bg-gray-900/90 backdrop-blur-md sticky top-0 z-10 transition-colors">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-indigo-50 dark:bg-indigo-950/70 border border-indigo-100 dark:border-indigo-900 flex items-center justify-center">
            <GraduationCap className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
          </div>
          <div>
            <h1 className="text-sm sm:text-base font-bold text-gray-900 dark:text-gray-100 leading-tight">
              CampusQuery Assistant
            </h1>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Natural language student records &amp; performance Q&amp;A
            </p>
          </div>
        </div>

        {/* Action icons */}
        <div className="flex items-center gap-1 sm:gap-2">
          {/* History drawer toggle */}
          <button
            onClick={() => {
              loadHistory();
              setHistoryOpen(true);
            }}
            className="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 px-2.5 py-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            title="View query history"
            aria-label="View query history"
          >
            <History className="w-4 h-4" />
            <span className="hidden sm:inline">History</span>
            {historyList.length > 0 && (
              <span className="text-[10px] font-semibold px-1.5 py-0.2 rounded-full bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300">
                {historyList.length}
              </span>
            )}
          </button>

          {/* Theme toggle */}
          <ThemeToggle />

          {/* Clear chat */}
          {messages.length > 0 && (
            <button
              onClick={handleClearChat}
              className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors px-2 py-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-950/40"
              aria-label="Clear chat"
              title="Clear current chat"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Clear</span>
            </button>
          )}
        </div>
      </header>

      {/* ── Chat Feed ── */}
      <main className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {/* Empty state */}
        {messages.length === 0 && !loading && (
          <div className="flex flex-col items-center justify-center h-full text-center py-8">
            <div className="w-16 h-16 rounded-2xl bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-100 dark:border-indigo-900 flex items-center justify-center mb-4">
              <GraduationCap className="w-9 h-9 text-indigo-600 dark:text-indigo-400" />
            </div>
            <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100 mb-2">Welcome to CampusQuery</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-6 max-w-md">
              Ask questions about students, courses, enrollments, and grades. Queries are translated to safe SQL and verified against SQLite.
            </p>
            <SampleQuestions onSelect={handleSend} />
          </div>
        )}

        {/* Message feed */}
        {messages.map((msg, i) => (
          <ChatMessage key={i} message={msg} />
        ))}

        {/* Loading state indicator */}
        {loading && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-950 flex items-center justify-center flex-shrink-0">
              <GraduationCap className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl rounded-tl-xs px-4 py-3 shadow-xs">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-indigo-600 dark:text-indigo-400" />
                <span className="text-xs text-gray-500 dark:text-gray-400">Analyzing schema and synthesizing SQL...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </main>

      {/* ── Input Bar ── */}
      <footer className="p-4 border-t border-gray-200 dark:border-gray-800 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md">
        {messages.length > 0 && (
          <div className="mb-2">
            <SampleQuestions onSelect={handleSend} compact={true} />
          </div>
        )}
        <div className="flex items-end gap-2 bg-gray-50 dark:bg-gray-800/80 rounded-2xl p-2 border border-gray-200 dark:border-gray-700 focus-within:border-indigo-500 dark:focus-within:border-indigo-500 transition-colors">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about students, courses, grades, or department stats..."
            rows={1}
            className="flex-1 bg-transparent resize-none border-none outline-hidden text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 max-h-32 px-2 py-1"
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || loading}
            className="p-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-500 text-white disabled:opacity-40 disabled:hover:bg-indigo-600 transition-colors shadow-xs"
            aria-label="Send query"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
        <p className="text-[11px] text-center text-gray-400 dark:text-gray-500 mt-2">
          Protected by 5-layer SQL sandboxing &amp; formula injection defense.
        </p>
      </footer>

      {/* ── Query History Drawer ── */}
      <HistoryDrawer
        isOpen={historyOpen}
        onClose={() => setHistoryOpen(false)}
        history={historyList}
        onSelectQuery={(q) => handleSend(q)}
        onClearHistory={handleClearHistory}
      />
    </div>
  );
}
