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
    <div className="space-y-4 font-sans">
      {/* Header Banner */}
      <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-2xs print:p-0 print:border-none print:shadow-none">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center text-[#0066cc] text-base font-bold shrink-0 print:hidden">
            🎟️
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900 tracking-tight">
              RECOMMENDED EXOTICS & MULTI-RACE TICKETS
            </h2>
            <p className="text-xs text-slate-500 font-medium">
              Multi-race wagers singling +5.0 Gap Solo Locks & spreading top contenders on competitive races.
            </p>
          </div>
        </div>
      </div>

      {!hasAnyTickets ? (
        <div className="bg-white rounded-xl p-6 border border-slate-200 text-center text-xs text-slate-500 shadow-2xs font-medium">
          No multi-race exotic combinations available for this card.
        </div>
      ) : (
        <div className="space-y-4">
          {/* Daily Doubles */}
          {ddList.length > 0 && (
            <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-2xs space-y-2.5 print:border-slate-400 print:shadow-none">
              <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <Flame className="w-3.5 h-3.5 text-amber-500 print:hidden" /> DAILY DOUBLE TICKETS ({ddList.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                {ddList.map((ticket, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-lg bg-amber-50/50 border border-amber-200 text-slate-900 font-medium leading-snug"
                    dangerouslySetInnerHTML={{ __html: typeof ticket === 'string' ? ticket : JSON.stringify(ticket) }}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Pick 3 Plays */}
          {pk3List.length > 0 && (
            <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-2xs space-y-2.5 print:border-slate-400 print:shadow-none">
              <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-[#0066cc] print:hidden" /> SUGGESTED PICK 3 TICKETS ({pk3List.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                {pk3List.map((ticket, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-lg bg-blue-50/50 border border-blue-200 text-slate-900 font-medium leading-snug"
                    dangerouslySetInnerHTML={{ __html: typeof ticket === 'string' ? ticket : JSON.stringify(ticket) }}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Pick 4 Plays */}
          {pk4List.length > 0 && (
            <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-2xs space-y-2.5 print:border-slate-400 print:shadow-none">
              <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <Award className="w-3.5 h-3.5 text-blue-600 print:hidden" /> SUGGESTED PICK 4 TICKETS ({pk4List.length})
              </h3>
              <div className="grid grid-cols-1 gap-2 text-xs">
                {pk4List.map((ticket, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-900 font-medium leading-snug"
                    dangerouslySetInnerHTML={{ __html: typeof ticket === 'string' ? ticket : JSON.stringify(ticket) }}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Pick 5 & Pick 6 Plays */}
          {(pk5List.length > 0 || pk6List.length > 0) && (
            <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-2xs space-y-2.5 print:border-slate-400 print:shadow-none">
              <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <Star className="w-3.5 h-3.5 text-purple-600 print:hidden" /> HIGH-PAYOUT PICK 5 / PICK 6 TICKETS
              </h3>
              <div className="space-y-2 text-xs">
                {pk5List.map((ticket, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-lg bg-purple-50/50 border border-purple-200 text-slate-900 font-medium leading-snug"
                    dangerouslySetInnerHTML={{ __html: typeof ticket === 'string' ? ticket : JSON.stringify(ticket) }}
                  />
                ))}
                {pk6List.map((ticket, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-lg bg-purple-100/60 border border-purple-300 text-slate-900 font-medium leading-snug"
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
