import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Copy, Check } from 'lucide-react';

/** Simple keyword highlighter for SQL display */
function highlightSql(sql) {
  const keywords = /\b(SELECT|FROM|WHERE|JOIN|LEFT|RIGHT|INNER|OUTER|ON|AND|OR|NOT|IN|LIKE|AS|ORDER|BY|GROUP|HAVING|LIMIT|DISTINCT|COUNT|AVG|SUM|MIN|MAX|WITH|CASE|WHEN|THEN|ELSE|END|BETWEEN|IS|NULL|ASC|DESC|UNION|ALL|EXISTS|CAST|COALESCE)\b/gi;
  const parts = sql.split(/((?:'[^']*')|(?:\b(?:SELECT|FROM|WHERE|JOIN|LEFT|RIGHT|INNER|OUTER|ON|AND|OR|NOT|IN|LIKE|AS|ORDER|BY|GROUP|HAVING|LIMIT|DISTINCT|COUNT|AVG|SUM|MIN|MAX|WITH|CASE|WHEN|THEN|ELSE|END|BETWEEN|IS|NULL|ASC|DESC|UNION|ALL|EXISTS|CAST|COALESCE)\b))/gi);

  return parts.map((part, i) => {
    if (!part) return null;
    // String literals
    if (part.startsWith("'") && part.endsWith("'")) {
      return <span key={i} className="text-emerald-600">{part}</span>;
    }
    // Keywords
    if (keywords.test(part)) {
      keywords.lastIndex = 0; // Reset regex state
      return <span key={i} className="text-indigo-600 font-semibold">{part.toUpperCase()}</span>;
    }
    return <span key={i}>{part}</span>;
  });
}

export default function SqlResultPanel({ sql, columns, rows, rowCount }) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="border rounded-xl overflow-hidden bg-white shadow-sm">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center justify-between w-full px-4 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50 transition-colors"
        aria-expanded={expanded}
        aria-label="Toggle SQL and raw results"
      >
        <span>View SQL & Raw Results</span>
        <div className="flex items-center gap-2">
          {rowCount > 0 && (
            <span className="bg-indigo-100 text-indigo-700 text-xs px-2 py-0.5 rounded-full">
              {rowCount} row{rowCount !== 1 ? 's' : ''}
            </span>
          )}
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {expanded && (
        <div className="border-t">
          {/* SQL display */}
          <div className="relative px-4 py-3 bg-gray-50">
            <pre className="text-xs font-mono whitespace-pre-wrap break-words text-gray-800 pr-16">
              {highlightSql(sql)}
            </pre>
            <button
              onClick={handleCopy}
              className="absolute top-2 right-2 flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 bg-white border rounded-md px-2 py-1 transition-colors"
              aria-label="Copy SQL to clipboard"
            >
              {copied ? <><Check className="w-3 h-3 text-emerald-500" /> Copied!</> : <><Copy className="w-3 h-3" /> Copy SQL</>}
            </button>
          </div>

          {/* Results table */}
          {columns.length > 0 && rows.length > 0 && (
            <div className="overflow-x-auto max-h-64 overflow-y-auto">
              <table className="w-full text-xs">
                <thead className="bg-gray-100 sticky top-0">
                  <tr>
                    {columns.map((col) => (
                      <th key={col} className="px-3 py-2 text-left font-semibold text-gray-700 whitespace-nowrap">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {rows.map((row, ri) => (
                    <tr key={ri} className="hover:bg-gray-50">
                      {row.map((cell, ci) => (
                        <td key={ci} className="px-3 py-1.5 text-gray-700 whitespace-nowrap">
                          {cell ?? <span className="text-gray-400 italic">null</span>}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
