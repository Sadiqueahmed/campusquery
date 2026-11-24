import React from 'react';
import { X, Clock, Trash2, ArrowUpRight, CheckCircle2, AlertTriangle, ShieldAlert } from 'lucide-react';

export default function HistoryDrawer({ isOpen, onClose, history, onSelectQuery, onClearHistory }) {
  if (!isOpen) return null;

  const formatTime = (isoString) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-xs transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer panel */}
      <div className="relative w-full max-w-sm sm:max-w-md bg-white dark:bg-gray-900 shadow-2xl flex flex-col h-full border-l border-gray-200 dark:border-gray-800 z-10 transition-transform">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3.5 border-b border-gray-200 dark:border-gray-800">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">Query History</h2>
            {history.length > 0 && (
              <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 border border-indigo-100 dark:border-indigo-900">
                {history.length}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            aria-label="Close history drawer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content list */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
          {history.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center py-12">
              <Clock className="w-12 h-12 text-gray-300 dark:text-gray-700 mb-3" />
              <p className="text-sm font-medium text-gray-600 dark:text-gray-300">No query history yet</p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1 max-w-[220px]">
                Questions you ask will appear here so you can quickly inspect and rerun them.
              </p>
            </div>
          ) : (
            history.map((item) => (
              <div
                key={item.id}
                onClick={() => {
                  onSelectQuery(item.question);
                  onClose();
                }}
                className="group p-3 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/40 hover:bg-indigo-50/50 dark:hover:bg-indigo-950/30 hover:border-indigo-200 dark:hover:border-indigo-800 transition-all cursor-pointer"
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="text-xs font-semibold text-gray-900 dark:text-gray-100 line-clamp-2 group-hover:text-indigo-600 dark:group-hover:text-indigo-400">
                    {item.question}
                  </p>
                  <ArrowUpRight className="w-3.5 h-3.5 text-gray-400 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>

                <div className="flex items-center justify-between gap-2 mt-2 pt-2 border-t border-gray-100 dark:border-gray-800/80 text-[11px] text-gray-500 dark:text-gray-400">
                  <div className="flex items-center gap-1.5">
                    {item.status === 'success' && (
                      <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>{item.row_count} row{item.row_count !== 1 ? 's' : ''}</span>
                      </span>
                    )}
                    {item.status === 'refused' && (
                      <span className="inline-flex items-center gap-1 text-amber-600 dark:text-amber-400">
                        <ShieldAlert className="w-3 h-3" />
                        <span>Refused</span>
                      </span>
                    )}
                    {item.status === 'error' && (
                      <span className="inline-flex items-center gap-1 text-red-600 dark:text-red-400">
                        <AlertTriangle className="w-3 h-3" />
                        <span>Error</span>
                      </span>
                    )}
                  </div>
                  <span>{formatTime(item.timestamp)}</span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        {history.length > 0 && (
          <div className="p-3 border-t border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/60">
            <button
              onClick={onClearHistory}
              className="w-full flex items-center justify-center gap-1.5 text-xs font-medium text-red-600 dark:text-red-400 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/40 border border-red-200 dark:border-red-900/60 rounded-lg py-2 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Clear History
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
