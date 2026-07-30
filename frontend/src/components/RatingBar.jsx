import React from 'react';

export default function RatingBar({ rating, gap, isTopPick }) {
  const score = Math.min(100, Math.max(0, parseFloat(rating) || 0));

  let barColor = 'bg-[#881337]';
  let scoreColor = 'text-slate-900';

  if (score >= 88) {
    barColor = 'bg-[#881337]';
    scoreColor = 'text-[#881337]';
  } else if (score >= 80) {
    barColor = 'bg-amber-600';
    scoreColor = 'text-amber-700';
  }

  return (
    <div className="w-full space-y-1">
      <div className="flex items-center justify-between text-xs font-mono">
        <span className="text-stone-500 text-[10px] font-bold uppercase tracking-wider">AI SCORE</span>
        <div className="flex items-center gap-1 font-bold">
          <span className={`text-sm font-black ${scoreColor}`}>{score.toFixed(1)}</span>
          {isTopPick && gap >= 5.0 && (
            <span className="px-1.5 py-0.2 rounded text-[10px] bg-[#881337] text-white font-mono font-black border border-amber-400">
              🔥🔥 +{gap.toFixed(1)} GAP
            </span>
          )}
          {isTopPick && gap >= 3.0 && gap < 5.0 && (
            <span className="px-1.5 py-0.2 rounded text-[10px] bg-amber-600 text-white font-mono font-extrabold border border-amber-400">
              🔥 +{gap.toFixed(1)} GAP
            </span>
          )}
          {isTopPick && gap > 0 && gap < 3.0 && (
            <span className="px-1.5 py-0.2 rounded text-[10px] bg-stone-100 text-stone-700 font-mono font-bold border border-stone-300">
              +{gap.toFixed(1)} GAP
            </span>
          )}
        </div>
      </div>
      <div className="w-full bg-stone-200 rounded-full h-1.5 overflow-hidden">
        <div
          className={`h-full rounded-full ${barColor} transition-all duration-300`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}
