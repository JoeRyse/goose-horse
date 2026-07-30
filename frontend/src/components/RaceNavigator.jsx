import React from 'react';
import { Ticket } from 'lucide-react';

export default function RaceNavigator({ races = [], activeRaceIndex, onSelectRace }) {
  if (!races || races.length === 0) return null;

  return (
    <div className="w-full bg-[#003366] border-b-2 border-[#10b981] py-2.5 px-4 sticky top-[57px] z-30 shadow-md print:hidden">
      <div className="max-w-7xl mx-auto flex items-center gap-1.5 overflow-x-auto scrollbar-none font-mono">
        {races.map((race, idx) => {
          const rNum = race.number || idx + 1;
          const isActive = activeRaceIndex === idx;
          const gap = parseFloat(race.rating_gap) || 0;
          const hasSoloLock = race.has_solo_lock || gap >= 5.0;
          const hasBestBet = race.has_best_bet || gap >= 3.0;

          return (
            <button
              key={idx}
              onClick={() => onSelectRace(idx)}
              className={`relative px-4 py-2 rounded-xl text-xs font-black transition-all whitespace-nowrap flex items-center gap-1.5 border active:scale-95 ${
                isActive
                  ? 'bg-[#10b981] text-white border-[#10b981] font-black shadow-md scale-105 z-10'
                  : 'bg-blue-950/60 text-emerald-100 border-blue-900 hover:bg-blue-900 hover:text-white'
              }`}
            >
              <span>RACE {rNum}</span>

              {hasSoloLock && (
                <span
                  className="inline-flex items-center text-[10px] text-emerald-200 font-extrabold"
                  title="+5.0 Gap Solo Lock"
                >
                  🔥🔥
                </span>
              )}

              {!hasSoloLock && hasBestBet && (
                <span
                  className="inline-flex items-center text-[10px] text-emerald-300 font-extrabold"
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
              ? 'bg-[#10b981] text-white border-[#10b981] font-black shadow-md scale-105 z-10'
              : 'bg-emerald-950/60 text-emerald-200 border-emerald-900 hover:bg-emerald-900'
          }`}
        >
          <Ticket className="w-4 h-4 shrink-0 text-[#10b981]" />
          <span>🎟️ EXOTICS & MULTI-RACE</span>
        </button>
      </div>
    </div>
  );
}
