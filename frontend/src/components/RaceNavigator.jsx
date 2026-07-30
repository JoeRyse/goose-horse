import React from 'react';
import { Ticket } from 'lucide-react';

export default function RaceNavigator({ races = [], activeRaceIndex, onSelectRace }) {
  if (!races || races.length === 0) return null;

  return (
    <div className="w-full bg-white border-b border-stone-200 py-2.5 px-4 sticky top-[57px] z-30 shadow-xs print:hidden">
      <div className="max-w-7xl mx-auto flex items-center gap-1.5 overflow-x-auto scrollbar-none font-mono">
        {races.map((race, idx) => {
          const rNum = race.number || idx + 1;
          const isActive = activeRaceIndex === idx;
          const hasSoloLock = race.has_solo_lock;
          const hasBestBet = race.has_best_bet;

          return (
            <button
              key={idx}
              onClick={() => onSelectRace(idx)}
              className={`relative px-4 py-2 rounded-xl text-xs font-black transition-all whitespace-nowrap flex items-center gap-1.5 border active:scale-95 ${
                isActive
                  ? 'bg-[#881337] text-white border-[#881337] font-black shadow-md scale-105 z-10'
                  : 'bg-stone-50 text-stone-700 border-stone-200 hover:bg-rose-50/50 hover:text-slate-900'
              }`}
            >
              <span>RACE {rNum}</span>

              {hasSoloLock && (
                <span
                  className="inline-flex items-center text-[10px] text-amber-300 font-extrabold"
                  title="+5.0 Gap Solo Lock"
                >
                  🔥🔥
                </span>
              )}

              {!hasSoloLock && hasBestBet && (
                <span
                  className="inline-flex items-center text-[10px] text-amber-500 font-extrabold"
                  title="+3.0 Gap Best Bet"
                >
                  🔥
                </span>
              )}
            </button>
          );
        })}

        {/* Dedicated Exotics Tab */}
        <button
          onClick={() => onSelectRace('EXOTICS')}
          className={`relative px-4 py-2 rounded-xl text-xs font-black transition-all whitespace-nowrap flex items-center gap-1.5 border active:scale-95 ${
            activeRaceIndex === 'EXOTICS'
              ? 'bg-amber-600 text-white border-amber-600 font-black shadow-md scale-105 z-10'
              : 'bg-amber-50 text-amber-900 border-amber-300 hover:bg-amber-100'
          }`}
        >
          <Ticket className="w-4 h-4 shrink-0 text-amber-600" />
          <span>🎟️ EXOTICS & MULTI-RACE</span>
        </button>
      </div>
    </div>
  );
}
