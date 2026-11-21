import React from 'react';

const QUESTIONS = [
  'Which students scored above 80% in Mathematics?',
  'List all courses taken by Rahul and his grades.',
  'What is the average marks per course?',
  'Show all students enrolled in Computer Science and give me the CSV.',
];

export default function SampleQuestions({ onSelect, compact = false }) {
  if (compact) {
    return (
      <div className="flex flex-wrap gap-1.5">
        {QUESTIONS.map((q) => (
          <button
            key={q}
            onClick={() => onSelect(q)}
            className="text-xs px-2.5 py-1 rounded-full bg-gray-100 text-gray-600 hover:bg-indigo-50 hover:text-indigo-700 transition-colors truncate max-w-[260px]"
            title={q}
          >
            {q}
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
      {QUESTIONS.map((q) => (
        <button
          key={q}
          onClick={() => onSelect(q)}
          className="text-left text-sm px-4 py-3 rounded-xl border border-gray-200 bg-white hover:border-indigo-300 hover:bg-indigo-50 transition-colors shadow-sm"
        >
          {q}
        </button>
      ))}
    </div>
  );
}
