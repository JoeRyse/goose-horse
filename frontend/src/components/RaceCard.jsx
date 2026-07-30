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
      {/* INTERACTIVE NAVY & MINT GREEN SCREEN VIEW LAYOUT              */}
      {/* ------------------------------------------------------------- */}
      <div className="print:hidden space-y-4 relative">
        {/* Race Header Banner - Primary Navy & Mint Green */}
        <div className="bg-[#003366] text-white rounded-2xl p-5 border-b-4 border-[#10b981] shadow-md relative z-10 overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-3">
                <span className="px-3.5 py-1 rounded-xl bg-[#10b981] text-white font-mono font-black text-sm shadow-xs">
                  RACE {rNum}
                </span>
                <h2 className="text-xl font-black text-white tracking-tight font-mono">
                  {distance}
                </h2>
              </div>
              <div className="flex items-center gap-3 text-xs font-mono text-emerald-200 mt-1.5 font-bold">
                <span>SURFACE: <strong className="text-white uppercase">{surface}</strong></span>
                <span>•</span>
                <span>CONFIDENCE: <strong className="text-[#10b981] font-black uppercase">{confidence}</strong></span>
              </div>
            </div>

            {/* Suggested Strategy Box */}
            {suggestedWager && (
              <div className="flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-blue-950/80 border-l-4 border-[#10b981] text-xs font-mono shadow-xs">
                <Ticket className="w-5 h-5 text-[#10b981] shrink-0" />
                <div>
                  <span className="text-[10px] text-emerald-300 block font-bold uppercase tracking-wider">STRATEGY</span>
                  <span className="font-extrabold text-white text-xs">{suggestedWager}</span>
                </div>
              </div>
            )}
          </div>

          {/* Lighter, Friendly Soft Rose Danger Horse Banner */}
          {dangerHorse && dangerHorse.name && (
            <div className="mt-3.5 py-2 px-3.5 rounded-r-xl bg-rose-50 border-l-4 border-rose-400 text-xs font-mono flex items-center gap-2 text-rose-950 shadow-xs">
              <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0" />
              <span className="font-extrabold text-rose-900 shrink-0">⚠️ DANGER: #{dangerHorse.number} {dangerHorse.name}</span>
              <span className="text-rose-700 truncate text-[11px] font-medium">— {dangerHorse.reason || dangerHorse.notes || 'Wildcard threat'}</span>
            </div>
          )}
        </div>

        {/* Handicapper Protocol AI Analysis Summary Box */}
        <div className="bg-[#dbe3eb] rounded-2xl p-4 border border-slate-300 text-[#003366] font-mono text-xs shadow-xs space-y-1">
          <h4 className="font-black uppercase text-xs text-[#003366] tracking-wider flex items-center gap-2">
            <Zap className="w-4 h-4 text-[#10b981]" /> HANDICAPPER PROTOCOL AI ANALYSIS
          </h4>
          <p className="text-slate-700 font-medium leading-relaxed">
            AI Analysis has evaluated race conditions, speed metrics, class ratings, pace scenario, and contender gap spread.
          </p>
        </div>

        {/* Contenders Cards */}
        <div className="space-y-3 relative z-10">
          <div className="space-y-2.5">
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
                  className={`bg-white rounded-2xl p-4 transition-all border shadow-xs relative ${
                    isTopPick
                      ? 'bg-[#d1fae5]/50 border-[#10b981] ring-1 ring-emerald-300'
                      : isSoloLock
                      ? 'border-[#10b981] bg-emerald-50/40'
                      : isBestBet
                      ? 'border-emerald-400 bg-emerald-50/20'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                    {/* Left Info & Reasoning */}
                    <div className="flex items-start gap-3.5 flex-1">
                      {/* Saddle Cloth Number Box - Primary Navy */}
                      <div className="w-9 h-9 rounded-xl bg-[#003366] text-white font-mono font-black text-base flex items-center justify-center shrink-0 shadow-xs border border-[#10b981]">
                        {hNum}
                      </div>

                      <div className="space-y-1.5 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <h4 className="text-base font-black text-slate-900 tracking-tight font-sans">
                            {hName}
                          </h4>
                          {isSoloLock && <SoloLockBadge gap={race.rating_gap} />}
                          {!isSoloLock && isBestBet && <BestBetBadge gap={race.rating_gap} />}
                          {isTopPick && !isSoloLock && !isBestBet && (
                            <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-black bg-[#10b981] text-white uppercase shadow-xs">
                              🏁 TOP PICK
                            </span>
                          )}
                          {horse.features?.is_danger_horse && <DangerBadge text="Wildcard" />}
                        </div>

                        {/* Detailed Reasoning Notes */}
                        <p
                          className="text-xs text-slate-700 leading-relaxed font-sans font-medium"
                          dangerouslySetInnerHTML={{ __html: reason }}
                        />
                      </div>
                    </div>

                    {/* Right Rating Bar */}
                    <div className="w-full md:w-48 shrink-0 pt-1.5 md:pt-0 border-t md:border-t-0 border-slate-200">
                      <RatingBar rating={rating} gap={race.rating_gap} isTopPick={isTopPick} />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Explicit Exacta Combinations & Exotic Tickets Box */}
        {exoticSuggestions && exoticSuggestions.length > 0 && (
          <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs relative z-10 space-y-2">
            <h4 className="text-xs font-mono font-extrabold text-[#003366] uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-[#10b981]" /> EXACTA COMBINATIONS & EXOTIC TICKETS
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 font-mono text-xs">
              {exoticSuggestions.map((sug, i) => (
                <div
                  key={i}
                  className={`p-2.5 rounded-xl border flex items-center justify-between gap-2 shadow-xs ${
                    i === 0 ? 'bg-[#a7f3d0] border-[#10b981] text-[#065f46] font-black' : 'bg-slate-50 border-slate-200 text-slate-900'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-base">{sug.icon}</span>
                    <div>
                      <span className="font-extrabold block">{sug.type}</span>
                      <span className="text-[11px] opacity-90 font-semibold">{sug.ticket}</span>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-[#10b981] text-white text-[10px] font-black shrink-0 shadow-xs">
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
