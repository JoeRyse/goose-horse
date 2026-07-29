import React from 'react';
import { ShieldAlert } from 'lucide-react';

export function SoloLockBadge() {
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-100 text-emerald-800 border border-emerald-200 tracking-wider">
      🔒 SOLO LOCK
    </span>
  );
}

export function BestBetBadge() {
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-blue-100 text-blue-800 border border-blue-200 tracking-wider">
      ⭐ BEST BET
    </span>
  );
}

export function DangerBadge({ text }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
      <ShieldAlert className="w-3 h-3 text-rose-600" />
      {text || 'DANGER'}
    </span>
  );
}

export function RegionBadge({ region }) {
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold tracking-wider uppercase bg-slate-100 text-slate-700 border border-slate-200">
      {region || 'USA'}
    </span>
  );
}
