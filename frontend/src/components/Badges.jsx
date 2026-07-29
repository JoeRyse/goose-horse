import React from 'react';
import { Flame, ShieldAlert } from 'lucide-react';

export function SoloLockBadge() {
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-black uppercase bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-sm font-mono tracking-wide">
      <Flame className="w-3.5 h-3.5 fill-current text-emerald-200 animate-pulse" />
      SOLO LOCK
    </span>
  );
}

export function BestBetBadge() {
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-black uppercase bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-sm font-mono tracking-wide">
      <Flame className="w-3.5 h-3.5 fill-current text-amber-200" />
      BEST BET
    </span>
  );
}

export function DangerBadge({ text }) {
  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-rose-50 text-rose-700 border border-rose-200 font-mono">
      <ShieldAlert className="w-3 h-3 text-rose-600" />
      {text || 'DANGER'}
    </span>
  );
}

export function RegionBadge({ region }) {
  const colors = {
    USA: 'bg-blue-50 text-blue-800 border-blue-200',
    AUS: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    UK: 'bg-purple-50 text-purple-800 border-purple-200',
    ASIA: 'bg-amber-50 text-amber-800 border-amber-200',
    HARNESS: 'bg-cyan-50 text-cyan-800 border-cyan-200',
  };
  const colorClass = colors[region] || 'bg-slate-100 text-slate-700 border-slate-200';

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-[10px] font-mono font-bold tracking-wider uppercase border ${colorClass}`}>
      {region || 'USA'}
    </span>
  );
}
