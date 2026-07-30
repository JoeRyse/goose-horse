import React from 'react';
import { ShieldAlert } from 'lucide-react';

export function SoloLockBadge({ gap }) {
  const gapText = gap ? ` (+${gap.toFixed(1)} GAP)` : '';
  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-[10px] font-black uppercase bg-[#10b981] text-white border border-emerald-300 shadow-xs tracking-wider font-mono">
      <span className="text-emerald-100">🔥🔥</span> SOLO LOCK{gapText}
    </span>
  );
}

export function BestBetBadge({ gap }) {
  const gapText = gap ? ` (+${gap.toFixed(1)} GAP)` : '';
  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-[10px] font-extrabold uppercase bg-emerald-600 text-white border border-emerald-400/60 shadow-xs tracking-wider font-mono">
      <span className="text-emerald-200">🔥</span> BEST BET{gapText}
    </span>
  );
}

export function DangerBadge({ text }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold uppercase bg-rose-50 text-rose-700 border border-rose-200 font-mono">
      <ShieldAlert className="w-3 h-3 text-rose-500" />
      {text || 'DANGER'}
    </span>
  );
}

export function RegionBadge({ region }) {
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold tracking-wider uppercase bg-slate-100 text-slate-700 border border-slate-200">
      {region || 'USA'}
    </span>
  );
}
