import React from 'react';
import { Ticket, Flame, Sparkles, Award, Star } from 'lucide-react';

export default function ExoticsCard({ exoticTickets = {}, dailyDoubles = [] }) {
  const ddList = (exoticTickets && exoticTickets.daily_doubles && exoticTickets.daily_doubles.length > 0)
    ? exoticTickets.daily_doubles
    : (dailyDoubles || []);

  const pk3List = exoticTickets?.pick_3 || [];
  const pk4List = exoticTickets?.pick_4 || [];
  const pk5List = exoticTickets?.pick_5 || [];
  const pk6List = exoticTickets?.pick_6 || [];

  const hasAnyTickets = ddList.length > 0 || pk3List.length > 0 || pk4List.length > 0 || pk5List.length > 0 || pk6List.length > 0;

  return (
    <div className="space-y-6 font-sans">
      {/* Header Banner */}
      <div className="bg-[#003366] text-white rounded-2xl p-5 border-b-4 border-[#10b981] shadow-md print:p-0 print:border-none print:shadow-none">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[#10b981] text-white flex items-center justify-center text-lg font-black shrink-0 print:hidden shadow-xs">
            🎟️
          </div>
          <div>
            <h2 className="text-lg font-black text-white tracking-tight font-mono">
              EXACTA COMBINATIONS & MULTI-RACE TICKETS
            </h2>
            <p className="text-xs text-emerald-200 font-mono font-medium">
              Multi-race wagers singling +5.0 Gap Solo Locks & spreading top contenders on competitive races.
            </p>
          </div>
        </div>
      </div>

      {!hasAnyTickets ? (
        <div className="bg-white rounded-2xl p-8 border border-slate-200 text-center font-mono text-xs text-slate-500 shadow-xs">
          No multi-race exotic combinations available for this card.
        </div>
      ) : (
        <div className="space-y-5">
          {/* Daily Doubles */}
          {ddList.length > 0 && (
            <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs space-y-3 print:border-slate-400 print:shadow-none">
              <h3 className="text-xs font-mono font-extrabold text-[#003366] uppercase tracking-wider flex items-center gap-2">
                <Flame className="w-4 h-4 text-[#10b981] print:hidden" /> DAILY DOUBLE TICKETS ({ddList.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 font-mono text-xs">
                {ddList.map((ticket, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-[#d1fae5]/60 border border-emerald-300 text-[#065f46] font-bold leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: typeof ticket === 'string' ? ticket : JSON.stringify(ticket) }}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Pick 3 Plays */}
          {pk3List.length > 0 && (
            <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs space-y-3 print:border-slate-400 print:shadow-none">
              <h3 className="text-xs font-mono font-extrabold text-[#003366] uppercase tracking-wider flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-[#10b981] print:hidden" /> SUGGESTED PICK 3 TICKETS ({pk3List.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 font-mono text-xs">
                {pk3List.map((ticket, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-slate-900 font-bold leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: typeof ticket === 'string' ? ticket : JSON.stringify(ticket) }}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Pick 4 Plays */}
          {pk4List.length > 0 && (
            <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs space-y-3 print:border-slate-400 print:shadow-none">
              <h3 className="text-xs font-mono font-extrabold text-[#003366] uppercase tracking-wider flex items-center gap-2">
                <Award className="w-4 h-4 text-[#10b981] print:hidden" /> SUGGESTED PICK 4 TICKETS ({pk4List.length})
              </h3>
              <div className="grid grid-cols-1 gap-2.5 font-mono text-xs">
                {pk4List.map((ticket, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 font-bold leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: typeof ticket === 'string' ? ticket : JSON.stringify(ticket) }}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Pick 5 & Pick 6 Plays */}
          {(pk5List.length > 0 || pk6List.length > 0) && (
            <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs space-y-3 print:border-slate-400 print:shadow-none">
              <h3 className="text-xs font-mono font-extrabold text-[#003366] uppercase tracking-wider flex items-center gap-2">
                <Star className="w-4 h-4 text-[#10b981] print:hidden" /> HIGH-PAYOUT PICK 5 / PICK 6 TICKETS
              </h3>
              <div className="space-y-2.5 font-mono text-xs">
                {pk5List.map((ticket, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-emerald-50/70 border border-emerald-200 text-slate-900 font-bold leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: typeof ticket === 'string' ? ticket : JSON.stringify(ticket) }}
                  />
                ))}
                {pk6List.map((ticket, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-[#d1fae5] border border-emerald-400 text-[#065f46] font-bold leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: typeof ticket === 'string' ? ticket : JSON.stringify(ticket) }}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
