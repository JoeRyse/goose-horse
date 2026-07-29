import React from 'react';
import { AlertTriangle, Ticket, Flame, Sparkles, Key, Gem, Zap } from 'lucide-react';
import RatingBar from './RatingBar';
import { SoloLockBadge, BestBetBadge, DangerBadge } from './Badges';

export default function RaceCard({ race, trackName, dateStr, isPrintAllMode = false }) {
  if (!race) return null;

  const rNum = race.number || 1;
  const distance = race.distance || race.distance_surface || 'Standard';
  const surface = race.surface || 'Dirt';
  const confidence = race.confidence_level || 'Medium';
  const rawFeatures = race.raw_features_dump || {};
  const suggestedWager = race.strategy || rawFeatures.suggested_wager || 'Win & Exacta Key';
  const dangerHorse = race.danger_horse || rawFeatures.danger_horse || null;
  const contenders = race.all_contenders || race.selections || [];
  const exoticSuggestions = race.exotic_suggestions || [];

  return (
    <div className={`font-sans ${isPrintAllMode ? 'mb-6 print:mb-6' : 'mb-6'}`}>
      {/* ------------------------------------------------------------- */}
      {/* PRINT-ONLY CLASSIC BLACK & WHITE RACING PROGRAM (NO BOXES)     */}
      {/* ------------------------------------------------------------- */}
      <div className="hidden print:block font-serif text-black space-y-2 text-xs">
        {/* Race Title Line */}
        <div className="border-b-2 border-black pb-1 mb-2">
          <div className="flex justify-between items-baseline">
            <h2 className="text-sm font-black uppercase font-mono tracking-tight">
              RACE {rNum} — {distance} ({surface})
            </h2>
            <span className="text-[10px] font-bold font-mono uppercase">
              CONFIDENCE: {confidence}
            </span>
          </div>
          <div className="text-[11px] font-mono mt-0.5 font-semibold text-slate-900">
            <strong>SUGGESTED STRATEGY:</strong> {suggestedWager}
          </div>
          {dangerHorse && dangerHorse.name && (
            <div className="text-[11px] font-mono text-black mt-0.5">
              <strong>⚠️ DANGER HORSE:</strong> #{dangerHorse.number} {dangerHorse.name} — {dangerHorse.reason || dangerHorse.notes || ''}
            </div>
          )}
        </div>

        {/* Clean Line Table (No rounded boxes or borders) */}
        <table className="w-full text-left font-serif border-collapse text-[11px]">
          <thead>
            <tr className="border-b-2 border-black font-mono text-[10px] uppercase">
              <th className="py-1 pr-2 w-8 text-center">#</th>
              <th className="py-1 pr-4 w-44">HORSE NAME</th>
              <th className="py-1 pr-4 w-20">AI SCORE</th>
              <th className="py-1">HANDICAPPING ANALYSIS & NOTES</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-400">
            {contenders.map((horse, idx) => {
              const hNum = horse.number || horse.program_number || `${idx + 1}`;
              const hName = horse.name || horse.horse_name || 'Unnamed';
              const rating = parseFloat(horse.rating) || parseFloat(horse.features?.ai_holistic_score) || 75.0;
              const isSoloLock = horse.is_solo_lock;
              const isBestBet = horse.is_best_bet;
              const reason = horse.reason || horse.handicapper_notes || '';

              return (
                <tr key={idx} className="align-top py-1">
                  <td className="py-1 pr-2 text-center font-bold font-mono text-xs">
                    {hNum}
                  </td>
                  <td className="py-1 pr-4 font-black uppercase font-sans text-xs">
                    {hName}
                  </td>
                  <td className="py-1 pr-4 font-bold font-mono text-xs">
                    {rating.toFixed(1)}
                    {isSoloLock && <span className="block text-[9px] font-black font-mono uppercase">[SOLO LOCK]</span>}
                    {!isSoloLock && isBestBet && <span className="block text-[9px] font-bold font-mono uppercase">[BEST BET]</span>}
                  </td>
                  <td className="py-1 text-[11px] leading-snug font-serif" dangerouslySetInnerHTML={{ __html: reason }} />
                </tr>
              );
            })}
          </tbody>
        </table>

        {/* Race Separator Line */}
        <div className="border-b border-black pt-2"></div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* INTERACTIVE FANDUEL SLEEK SCREEN VIEW LAYOUT                  */}
      {/* ------------------------------------------------------------- */}
      <div className="print:hidden space-y-3 relative">
        {/* Race Header Banner */}
        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-xs relative z-10">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2.5">
                <span className="px-2.5 py-0.5 rounded-md bg-[#0066cc] text-white font-bold text-xs">
                  RACE {rNum}
                </span>
                <h2 className="text-base font-bold text-slate-900 tracking-tight">
                  {distance}
                </h2>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-500 mt-1 font-medium">
                <span>SURFACE: <strong className="text-slate-800 uppercase">{surface}</strong></span>
                <span>•</span>
                <span>CONFIDENCE: <strong className="text-emerald-700 font-bold uppercase">{confidence}</strong></span>
              </div>
            </div>

            {/* Suggested Strategy Box */}
            {suggestedWager && (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-50 border-l-3 border-[#0066cc] text-xs shadow-2xs">
                <Ticket className="w-4 h-4 text-[#0066cc] shrink-0" />
                <div>
                  <span className="text-[10px] text-slate-400 block font-semibold uppercase tracking-wider">STRATEGY</span>
                  <span className="font-semibold text-slate-900 text-xs">{suggestedWager}</span>
                </div>
              </div>
            )}
          </div>

          {/* Compact FanDuel Danger Horse Banner */}
          {dangerHorse && dangerHorse.name && (
            <div className="mt-2.5 py-1.5 px-3 rounded-r-lg bg-rose-50/80 border-l-3 border-rose-500 text-xs flex items-center gap-2 text-rose-950">
              <AlertTriangle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
              <span className="font-bold text-rose-900 shrink-0">DANGER: #{dangerHorse.number} {dangerHorse.name}</span>
              <span className="text-slate-600 truncate text-[11px] font-medium">— {dangerHorse.reason || dangerHorse.notes || 'Wildcard threat'}</span>
            </div>
          )}
        </div>

        {/* Contenders Cards */}
        <div className="space-y-2 relative z-10">
          <div className="space-y-2">
            {contenders.map((horse, idx) => {
              const hNum = horse.number || horse.program_number || `${idx + 1}`;
              const hName = horse.name || horse.horse_name || 'Unnamed';
              const rating = parseFloat(horse.rating) || parseFloat(horse.features?.ai_holistic_score) || 75.0;
              const isSoloLock = horse.is_solo_lock;
              const isBestBet = horse.is_best_bet;
              const reason = horse.reason || horse.handicapper_notes || '';
              const isTopPick = (idx === 0);

              return (
                <div
                  key={idx}
                  className={`bg-white rounded-xl p-3.5 transition-all border shadow-2xs relative ${
                    isSoloLock
                      ? 'border-emerald-300 bg-emerald-50/20'
                      : isBestBet
                      ? 'border-blue-300 bg-blue-50/20'
                      : isTopPick
                      ? 'border-slate-300 bg-slate-50/40'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex flex-col md:flex-row md:items-start justify-between gap-3">
                    {/* Left Info & Reasoning */}
                    <div className="flex items-start gap-3 flex-1">
                      {/* Saddle Cloth Number Badge */}
                      <div className="w-8 h-8 rounded-lg bg-slate-900 text-white font-bold text-sm flex items-center justify-center shrink-0 shadow-2xs">
                        {hNum}
                      </div>

                      <div className="space-y-1 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <h4 className="text-sm font-bold text-slate-900 tracking-tight">
                            {hName}
                          </h4>
                          {isSoloLock && <SoloLockBadge />}
                          {!isSoloLock && isBestBet && <BestBetBadge />}
                          {isTopPick && !isSoloLock && !isBestBet && (
                            <span className="px-2 py-0.2 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200 uppercase">
                              TOP PICK
                            </span>
                          )}
                          {horse.features?.is_danger_horse && <DangerBadge text="Wildcard" />}
                        </div>

                        {/* Detailed Reasoning Notes */}
                        <p
                          className="text-xs text-slate-600 leading-snug font-medium"
                          dangerouslySetInnerHTML={{ __html: reason }}
                        />
                      </div>
                    </div>

                    {/* Right Rating Bar */}
                    <div className="w-full md:w-44 shrink-0 pt-1 md:pt-0 border-t md:border-t-0 border-slate-100">
                      <RatingBar rating={rating} gap={race.rating_gap} isTopPick={isTopPick} />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Explicit FanDuel Exotic Wager Suggestions Box */}
        {exoticSuggestions && exoticSuggestions.length > 0 && (
          <div className="bg-white rounded-xl p-3.5 border border-slate-200 shadow-2xs relative z-10 space-y-2">
            <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-[#0066cc]" /> EXOTIC TICKETS FOR RACE {rNum}
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              {exoticSuggestions.map((sug, i) => (
                <div
                  key={i}
                  className="p-2 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between gap-2"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm">{sug.icon}</span>
                    <div>
                      <span className="font-bold text-slate-900 block text-xs">{sug.type}</span>
                      <span className="text-[11px] text-slate-600 font-medium">{sug.ticket}</span>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-blue-50 text-[#0066cc] border border-blue-200 text-[10px] font-bold shrink-0">
                    {sug.cost}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
