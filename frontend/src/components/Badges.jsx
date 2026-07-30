import React from 'react';
import { ShieldAlert } from 'lucide-react';

export function SoloLockBadge({ gap }) {
  const gapText = gap ? ` (+${gap.toFixed(1)} GAP)` : '';
  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-[10px] font-black uppercase bg-gradient-to-r from-[#881337] to-[#be123c] text-white border border-amber-400/80 shadow-xs tracking-wider font-mono">
      <span className="text-amber-300">🔥🔥</span> SOLO LOCK{gapText}
    </span>
  );
}

export function BestBetBadge({ gap }) {
  const gapText = gap ? ` (+${gap.toFixed(1)} GAP)` : '';
  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-[10px] font-extrabold uppercase bg-gradient-to-r from-amber-600 to-amber-700 text-white border border-amber-400/60 shadow-xs tracking-wider font-mono">
      <span className="text-amber-200">🔥</span> BEST BET{gapText}
    </span>
  );
}

export function DangerBadge({ text }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold uppercase bg-rose-50 text-[#881337] border border-rose-200 font-mono">
      <ShieldAlert className="w-3 h-3 text-rose-600" />
      {text || 'DANGER'}
    </span>
  );
}

export function RegionBadge({ region }) {
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold tracking-wider uppercase bg-stone-100 text-stone-700 border border-stone-200">
      {region || 'USA'}
    </span>
  );
}
