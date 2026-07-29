import React from 'react';

export default function RatingBar({ rating, gap, isTopPick }) {
  const score = Math.min(100, Math.max(0, parseFloat(rating) || 0));

  let barColor = 'bg-[#0066cc]';
  let scoreColor = 'text-slate-900';

  if (score >= 88) {
    barColor = 'bg-emerald-600';
    scoreColor = 'text-emerald-700';
  } else if (score >= 80) {
    barColor = 'bg-[#0066cc]';
    scoreColor = 'text-[#0066cc]';
  }

  return (
    <div className="w-full space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-slate-500 text-[10px] font-semibold uppercase tracking-wider">AI SCORE</span>
        <div className="flex items-center gap-1.5 font-semibold">
          <span className={`text-sm font-bold ${scoreColor}`}>{score.toFixed(1)}</span>
          {isTopPick && gap > 0 && (
            <span className="px-1.5 py-0.2 rounded text-[10px] bg-slate-100 text-slate-700 font-semibold border border-slate-200">
              +{gap.toFixed(1)} GAP
            </span>
          )}
        </div>
      </div>
      <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
        <div
          className={`h-full rounded-full ${barColor} transition-all duration-300`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}
