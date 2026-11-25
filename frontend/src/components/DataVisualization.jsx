import React, { useState, useMemo } from 'react';
import { BarChart3, TrendingUp, Award, Layers } from 'lucide-react';

export default function DataVisualization({ columns, rows }) {
  // Analyze columns to find candidate labels and numeric values
  const { labelColIdx, numericColIndices, labelColName } = useMemo(() => {
    if (!columns || !rows || rows.length === 0) {
      return { labelColIdx: -1, numericColIndices: [], labelColName: '' };
    }

    let labelIdx = -1;
    const numIndices = [];

    // Check data types by inspecting the first few non-null rows
    columns.forEach((col, idx) => {
      let isNumeric = true;
      let hasData = false;

      for (let r = 0; r < Math.min(rows.length, 10); r++) {
        const val = rows[r][idx];
        if (val !== null && val !== undefined && val !== '') {
          hasData = true;
          if (typeof val !== 'number' && isNaN(Number(val))) {
            isNumeric = false;
            break;
          }
        }
      }

      if (hasData && isNumeric) {
        numIndices.push(idx);
      } else if (labelIdx === -1) {
        labelIdx = idx;
      }
    });

    // Fallback if no string column was found
    if (labelIdx === -1 && columns.length > 0) {
      labelIdx = 0;
    }

    return {
      labelColIdx: labelIdx,
      numericColIndices: numIndices,
      labelColName: columns[labelIdx] || 'Item',
    };
  }, [columns, rows]);

  const [selectedNumIdx, setSelectedNumIdx] = useState(
    numericColIndices.length > 0 ? numericColIndices[0] : -1
  );

  // Sync state if indices change
  React.useEffect(() => {
    if (numericColIndices.length > 0 && !numericColIndices.includes(selectedNumIdx)) {
      setSelectedNumIdx(numericColIndices[0]);
    }
  }, [numericColIndices, selectedNumIdx]);

  if (numericColIndices.length === 0 || rows.length === 0) {
    return (
      <div className="p-6 text-center text-xs text-gray-500 dark:text-gray-400">
        <BarChart3 className="w-8 h-8 mx-auto mb-2 text-gray-300 dark:text-gray-600" />
        <p>No numeric metrics detected for chart visualization.</p>
        <p className="mt-1 text-[11px] text-gray-400 dark:text-gray-500">
          Visualizations auto-render when queries return counts, averages, or scores.
        </p>
      </div>
    );
  }

  const activeNumIdx = selectedNumIdx !== -1 ? selectedNumIdx : numericColIndices[0];
  const activeMetricName = columns[activeNumIdx] || 'Value';

  // Process data for the active metric
  const chartData = rows.map((row) => {
    const rawVal = row[activeNumIdx];
    const numVal = rawVal !== null && rawVal !== undefined ? Number(rawVal) : 0;
    const label = labelColIdx !== -1 && row[labelColIdx] !== null ? String(row[labelColIdx]) : 'Record';
    return { label, value: numVal };
  });

  const values = chartData.map((d) => d.value).filter((v) => !isNaN(v));
  const maxVal = values.length > 0 ? Math.max(...values, 0) : 1;
  const minVal = values.length > 0 ? Math.min(...values) : 0;
  const avgVal = values.length > 0 ? (values.reduce((a, b) => a + b, 0) / values.length).toFixed(1) : 0;
  const totalVal = values.length > 0 ? values.reduce((a, b) => a + b, 0).toFixed(1) : 0;

  return (
    <div className="p-4 space-y-4 bg-gray-50/60 dark:bg-gray-950/40">
      {/* Metric Selector (if multiple numeric columns) */}
      {numericColIndices.length > 1 && (
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-gray-600 dark:text-gray-300">Metric:</span>
          <div className="flex flex-wrap gap-1">
            {numericColIndices.map((idx) => (
              <button
                key={idx}
                onClick={() => setSelectedNumIdx(idx)}
                className={`text-xs px-2.5 py-1 rounded-md transition-colors ${
                  activeNumIdx === idx
                    ? 'bg-indigo-600 text-white font-medium shadow-xs'
                    : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                {columns[idx]}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Quick Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <div className="p-2.5 rounded-lg bg-white dark:bg-gray-850 border border-gray-200 dark:border-gray-800 shadow-xs">
          <div className="flex items-center gap-1.5 text-gray-500 dark:text-gray-400 text-[11px]">
            <Award className="w-3.5 h-3.5 text-amber-500" />
            <span>Highest</span>
          </div>
          <div className="mt-1 text-sm font-bold text-gray-900 dark:text-gray-100">{maxVal}</div>
        </div>

        <div className="p-2.5 rounded-lg bg-white dark:bg-gray-850 border border-gray-200 dark:border-gray-800 shadow-xs">
          <div className="flex items-center gap-1.5 text-gray-500 dark:text-gray-400 text-[11px]">
            <TrendingUp className="w-3.5 h-3.5 text-indigo-500" />
            <span>Average</span>
          </div>
          <div className="mt-1 text-sm font-bold text-gray-900 dark:text-gray-100">{avgVal}</div>
        </div>

        <div className="p-2.5 rounded-lg bg-white dark:bg-gray-850 border border-gray-200 dark:border-gray-800 shadow-xs">
          <div className="flex items-center gap-1.5 text-gray-500 dark:text-gray-400 text-[11px]">
            <Layers className="w-3.5 h-3.5 text-emerald-500" />
            <span>Total Records</span>
          </div>
          <div className="mt-1 text-sm font-bold text-gray-900 dark:text-gray-100">{chartData.length}</div>
        </div>

        <div className="p-2.5 rounded-lg bg-white dark:bg-gray-850 border border-gray-200 dark:border-gray-800 shadow-xs">
          <div className="flex items-center gap-1.5 text-gray-500 dark:text-gray-400 text-[11px]">
            <BarChart3 className="w-3.5 h-3.5 text-purple-500" />
            <span>Sum</span>
          </div>
          <div className="mt-1 text-sm font-bold text-gray-900 dark:text-gray-100">{totalVal}</div>
        </div>
      </div>

      {/* Horizontal Bar Chart */}
      <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
        {chartData.map((item, i) => {
          const pct = maxVal > 0 ? Math.max((item.value / maxVal) * 100, 2) : 0;
          return (
            <div key={i} className="group text-xs">
              <div className="flex items-center justify-between text-[11px] mb-1">
                <span className="font-medium text-gray-700 dark:text-gray-300 truncate max-w-[240px]" title={item.label}>
                  {item.label}
                </span>
                <span className="font-semibold text-gray-900 dark:text-gray-100 ml-2">
                  {item.value}
                </span>
              </div>
              <div className="w-full h-3 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden p-0.5">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-indigo-600 dark:from-indigo-400 dark:to-indigo-500 transition-all duration-500 group-hover:from-indigo-600 group-hover:to-purple-600"
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
