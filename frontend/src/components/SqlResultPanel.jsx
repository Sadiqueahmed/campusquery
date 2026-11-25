import React, { useState, useMemo } from 'react';
import { ChevronDown, ChevronUp, Copy, Check, Table as TableIcon, BarChart3, Code2 } from 'lucide-react';
import DataVisualization from './DataVisualization';

/** Simple keyword highlighter for SQL display */
function highlightSql(sql) {
  const keywords = /\b(SELECT|FROM|WHERE|JOIN|LEFT|RIGHT|INNER|OUTER|ON|AND|OR|NOT|IN|LIKE|AS|ORDER|BY|GROUP|HAVING|LIMIT|DISTINCT|COUNT|AVG|SUM|MIN|MAX|WITH|CASE|WHEN|THEN|ELSE|END|BETWEEN|IS|NULL|ASC|DESC|UNION|ALL|EXISTS|CAST|COALESCE)\b/gi;
  const parts = sql.split(/((?:'[^']*')|(?:\b(?:SELECT|FROM|WHERE|JOIN|LEFT|RIGHT|INNER|OUTER|ON|AND|OR|NOT|IN|LIKE|AS|ORDER|BY|GROUP|HAVING|LIMIT|DISTINCT|COUNT|AVG|SUM|MIN|MAX|WITH|CASE|WHEN|THEN|ELSE|END|BETWEEN|IS|NULL|ASC|DESC|UNION|ALL|EXISTS|CAST|COALESCE)\b))/gi);

  return parts.map((part, i) => {
    if (!part) return null;
    // String literals
    if (part.startsWith("'") && part.endsWith("'")) {
      return <span key={i} className="text-emerald-600 dark:text-emerald-400">{part}</span>;
    }
    // Keywords
    if (keywords.test(part)) {
      keywords.lastIndex = 0; // Reset regex state
      return <span key={i} className="text-indigo-600 dark:text-indigo-400 font-semibold">{part.toUpperCase()}</span>;
    }
    return <span key={i}>{part}</span>;
  });
}

export default function SqlResultPanel({ sql, columns, rows, rowCount }) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState('table'); // 'table' | 'chart' | 'sql'

  // Check if chart is viable (at least one numeric value in data)
  const hasNumericData = useMemo(() => {
    if (!rows || rows.length === 0 || !columns) return false;
    return rows.some(row =>
      row.some(val => val !== null && val !== undefined && val !== '' && !isNaN(Number(val)) && typeof val !== 'boolean')
    );
  }, [columns, rows]);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="border border-gray-200 dark:border-gray-800 rounded-xl overflow-hidden bg-white dark:bg-gray-900 shadow-xs">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center justify-between w-full px-4 py-2.5 text-xs font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800/60 transition-colors"
        aria-expanded={expanded}
        aria-label="Toggle SQL and results drawer"
      >
        <span className="font-semibold text-gray-800 dark:text-gray-200">Inspect Query &amp; Data</span>
        <div className="flex items-center gap-2">
          {hasNumericData && (
            <span className="hidden sm:inline-flex items-center gap-1 text-[11px] text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/60 px-2 py-0.5 rounded-full border border-indigo-100 dark:border-indigo-900">
              <BarChart3 className="w-3 h-3" /> Chart Ready
            </span>
          )}
          {rowCount > 0 && (
            <span className="bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-xs px-2 py-0.5 rounded-full border border-gray-200 dark:border-gray-700">
              {rowCount} row{rowCount !== 1 ? 's' : ''}
            </span>
          )}
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {expanded && (
        <div className="border-t border-gray-200 dark:border-gray-800">
          {/* Sub-navigation tabs */}
          <div className="flex items-center justify-between px-3 py-1.5 bg-gray-50 dark:bg-gray-950 border-b border-gray-200 dark:border-gray-800">
            <div className="flex items-center gap-1">
              <button
                onClick={() => setActiveTab('table')}
                className={`flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-md font-medium transition-colors ${
                  activeTab === 'table'
                    ? 'bg-white dark:bg-gray-800 text-indigo-600 dark:text-indigo-400 shadow-xs'
                    : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                }`}
              >
                <TableIcon className="w-3.5 h-3.5" />
                <span>Table</span>
              </button>

              {hasNumericData && (
                <button
                  onClick={() => setActiveTab('chart')}
                  className={`flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-md font-medium transition-colors ${
                    activeTab === 'chart'
                      ? 'bg-white dark:bg-gray-800 text-indigo-600 dark:text-indigo-400 shadow-xs'
                      : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                  }`}
                >
                  <BarChart3 className="w-3.5 h-3.5" />
                  <span>Chart</span>
                </button>
              )}

              <button
                onClick={() => setActiveTab('sql')}
                className={`flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-md font-medium transition-colors ${
                  activeTab === 'sql'
                    ? 'bg-white dark:bg-gray-800 text-indigo-600 dark:text-indigo-400 shadow-xs'
                    : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                }`}
              >
                <Code2 className="w-3.5 h-3.5" />
                <span>SQL Query</span>
              </button>
            </div>

            {activeTab === 'sql' && (
              <button
                onClick={handleCopy}
                className="flex items-center gap-1 text-[11px] text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 bg-white dark:bg-gray-850 border border-gray-200 dark:border-gray-750 rounded-md px-2 py-0.5 transition-colors shadow-xs"
                aria-label="Copy SQL"
              >
                {copied ? (
                  <>
                    <Check className="w-3 h-3 text-emerald-500" />
                    <span className="text-emerald-600 dark:text-emerald-400">Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3" />
                    <span>Copy</span>
                  </>
                )}
              </button>
            )}
          </div>

          {/* Tab Content: Visual Chart */}
          {activeTab === 'chart' && (
            <DataVisualization columns={columns} rows={rows} />
          )}

          {/* Tab Content: SQL Display */}
          {activeTab === 'sql' && (
            <div className="relative px-4 py-3 bg-gray-50 dark:bg-gray-950">
              <pre className="text-xs font-mono whitespace-pre-wrap break-words text-gray-800 dark:text-gray-200">
                {highlightSql(sql)}
              </pre>
            </div>
          )}

          {/* Tab Content: Results Table */}
          {activeTab === 'table' && (
            <>
              {columns.length > 0 && rows.length > 0 ? (
                <div className="overflow-x-auto max-h-64 overflow-y-auto">
                  <table className="w-full text-xs">
                    <thead className="bg-gray-100 dark:bg-gray-800 sticky top-0">
                      <tr>
                        {columns.map((col) => (
                          <th key={col} className="px-3 py-2 text-left font-semibold text-gray-700 dark:text-gray-200 whitespace-nowrap">
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                      {rows.map((row, ri) => (
                        <tr key={ri} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                          {row.map((cell, ci) => (
                            <td key={ci} className="px-3 py-1.5 text-gray-700 dark:text-gray-300 whitespace-nowrap">
                              {cell ?? <span className="text-gray-400 italic">null</span>}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-4 text-center text-xs text-gray-500">No rows returned.</div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
