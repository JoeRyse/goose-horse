import React from 'react';

export default function RatingBar({ rating, gap, isTopPick }) {
  const score = Math.min(100, Math.max(0, parseFloat(rating) || 0));

  let barGradient = 'from-blue-500 to-indigo-500';
  let scoreColor = 'text-slate-900';

  if (score >= 88) {
    barGradient = 'from-emerald-500 to-teal-500';
    scoreColor = 'text-emerald-700';
  } else if (score >= 80) {
    barGradient = 'from-amber-500 to-orange-500';
    scoreColor = 'text-amber-700';
  }

  return (
    <div className="w-full space-y-1">
      <div className="flex items-center justify-between text-xs font-mono">
        <span className="text-slate-400 text-[10px] font-bold uppercase tracking-wider">AI RATING</span>
        <div className="flex items-center gap-1.5 font-bold">
          <span className={`text-sm font-black ${scoreColor}`}>{score.toFixed(1)}</span>
          {isTopPick && gap > 0 && (
            <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold">
              +{gap.toFixed(1)} GAP
            </span>
          )}
        </div>
      </div>
      <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden border border-slate-200 shadow-inner">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${barGradient} transition-all duration-500`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}
