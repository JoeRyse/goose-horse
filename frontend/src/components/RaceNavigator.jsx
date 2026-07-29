import React from 'react';
import { Flame, Ticket } from 'lucide-react';

export default function RaceNavigator({ races = [], activeRaceIndex, onSelectRace }) {
  if (!races || races.length === 0) return null;

  return (
    <div className="w-full bg-white border-b border-slate-200 py-2 px-4 sticky top-[57px] z-30 shadow-xs print:hidden">
      <div className="max-w-7xl mx-auto flex items-center gap-1.5 overflow-x-auto scrollbar-none">
        {races.map((race, idx) => {
          const rNum = race.number || idx + 1;
          const isActive = activeRaceIndex === idx;
          const hasSoloLock = race.has_solo_lock;
          const hasBestBet = race.has_best_bet;

          return (
            <button
              key={idx}
              onClick={() => onSelectRace(idx)}
              className={`relative px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap flex items-center gap-1 border active:scale-95 ${
                isActive
                  ? 'bg-[#0066cc] text-white border-[#0066cc] font-bold shadow-xs'
                  : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100 hover:text-slate-900'
              }`}
            >
              <span>RACE {rNum}</span>

              {hasSoloLock && (
                <span
                  className={`inline-flex items-center text-[10px] ${
                    isActive ? 'text-emerald-200' : 'text-emerald-600'
                  }`}
                  title="Contains Solo Lock"
                >
                  🔒
                </span>
              )}

              {!hasSoloLock && hasBestBet && (
                <span
                  className={`inline-flex items-center text-[10px] ${
                    isActive ? 'text-blue-200' : 'text-blue-600'
                  }`}
                  title="Contains Best Bet"
                >
                  ⭐
                </span>
              )}
            </button>
          );
        })}

        {/* Dedicated Exotics Tab */}
        <button
          onClick={() => onSelectRace('EXOTICS')}
          className={`relative px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap flex items-center gap-1 border active:scale-95 ${
            activeRaceIndex === 'EXOTICS'
              ? 'bg-slate-900 text-white border-slate-900 font-bold shadow-xs'
              : 'bg-slate-100 text-slate-800 border-slate-200 hover:bg-slate-200'
          }`}
        >
          <Ticket className="w-3.5 h-3.5 shrink-0 text-amber-500" />
          <span>🎟️ EXOTICS & MULTI-RACE</span>
        </button>
      </div>
    </div>
  );
}
