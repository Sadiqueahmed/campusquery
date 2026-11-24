import React, { useState } from 'react';
import { Download, Loader2, AlertTriangle, ShieldAlert, GraduationCap, User } from 'lucide-react';
import SqlResultPanel from './SqlResultPanel';
import { exportCsv } from '../api';

export default function ChatMessage({ message }) {
  const [csvLoading, setCsvLoading] = useState(false);

  if (message.role === 'user') {
    return (
      <div className="flex items-start gap-3 justify-end">
        <div className="bg-indigo-600 dark:bg-indigo-700 text-white rounded-2xl rounded-tr-xs px-4 py-2.5 max-w-[80%] shadow-xs">
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        </div>
        <div className="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-950 flex items-center justify-center flex-shrink-0">
          <User className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
        </div>
      </div>
    );
  }

  // Assistant message
  const { answer, sql, columns, rows, row_count, csv_available, error } = message;

  const handleDownloadCsv = async () => {
    if (!sql) return;
    setCsvLoading(true);
    try {
      const blob = await exportCsv(sql);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'query_results.csv';
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert('CSV download failed: ' + err.message);
    } finally {
      setCsvLoading(false);
    }
  };

  // Determine error styling
  const isRefusal = error?.code === 'cannot_answer';
  const isBlocked = error?.code === 'blocked_unsafe_sql';
  const isServerError = error && !isRefusal && !isBlocked;

  return (
    <div className="flex items-start gap-3">
      <div className="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-950 flex items-center justify-center flex-shrink-0">
        <GraduationCap className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
      </div>
      <div className="max-w-[80%] space-y-2">
        {/* Answer bubble */}
        <div className={`rounded-2xl rounded-tl-xs px-4 py-2.5 shadow-xs ${
          isBlocked ? 'bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60' :
          isRefusal ? 'bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60' :
          isServerError ? 'bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60' :
          'bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800'
        }`}>
          {/* Error icon for blocked/refusal */}
          {(isBlocked || isRefusal) && (
            <div className="flex items-center gap-1.5 mb-1.5">
              {isBlocked ? (
                <>
                  <ShieldAlert className="w-4 h-4 text-red-500 dark:text-red-400" />
                  <span className="text-xs font-medium text-red-600 dark:text-red-400">Blocked for safety</span>
                </>
              ) : (
                <>
                  <AlertTriangle className="w-4 h-4 text-amber-500 dark:text-amber-400" />
                  <span className="text-xs font-medium text-amber-600 dark:text-amber-400">Can&apos;t answer this</span>
                </>
              )}
            </div>
          )}
          {isServerError && (
            <div className="flex items-center gap-1.5 mb-1.5">
              <AlertTriangle className="w-4 h-4 text-red-500 dark:text-red-400" />
              <span className="text-xs font-medium text-red-600 dark:text-red-400">Error</span>
            </div>
          )}
          <p className="text-sm whitespace-pre-wrap text-gray-800 dark:text-gray-200">{answer}</p>
        </div>

        {/* SQL & Results panel */}
        {sql && (
          <SqlResultPanel sql={sql} columns={columns} rows={rows} rowCount={row_count} />
        )}

        {/* Download CSV button */}
        {csv_available && row_count > 0 && (
          <button
            onClick={handleDownloadCsv}
            disabled={csvLoading}
            className="flex items-center gap-1.5 text-sm font-medium px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-600 dark:hover:bg-emerald-500 text-white disabled:opacity-50 transition-colors shadow-xs"
            aria-label="Download results as CSV"
          >
            {csvLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Download className="w-4 h-4" />
            )}
            Download CSV
          </button>
        )}
      </div>
    </div>
  );
}
