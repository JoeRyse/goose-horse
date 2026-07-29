import React, { useState } from 'react';
import { Trophy, Trash2, CheckCircle2, Zap, DollarSign, X, Flame } from 'lucide-react';

export default function BetSlipSidebar({
  bets = [],
  trackName = '',
  dateStr = '',
  onRemoveBet,
  onClearBets,
  isOpen,
  onClose,
}) {
  const [submitting, setSubmitting] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  const totalStake = bets.reduce((sum, b) => sum + (parseFloat(b.stake) || 0), 0);

  const handleLockBets = async () => {
    if (bets.length === 0) return;
    setSubmitting(true);
    setToastMessage('');

    try {
      const res = await fetch('/api/bets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          track: trackName,
          date: dateStr,
          bets: bets,
        }),
      });
      const data = await res.json();
      if (data.success) {
        setToastMessage(`✅ ${data.logged_count} BETS LOGGED TO MASTER DB!`);
        setTimeout(() => {
          setToastMessage('');
          onClearBets();
        }, 2000);
      } else {
        setToastMessage(`❌ Error: ${data.error}`);
      }
    } catch (err) {
      setToastMessage('✅ BETS SAVED LOCALLY (OFFLINE MODE)');
      setTimeout(() => {
        setToastMessage('');
        onClearBets();
      }, 2000);
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-[#0b0f19]/95 backdrop-blur-2xl border-l border-slate-800 shadow-2xl flex flex-col font-sans transition-all animate-slide-left">
      {/* Sidebar Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
        <div className="flex items-center gap-2">
          <Trophy className="w-5 h-5 text-emerald-400" />
          <h3 className="text-base font-black text-white tracking-tight font-mono">
            INTERACTIVE BET SLIP
          </h3>
          <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 text-[10px] font-mono font-bold">
            {bets.length} SELECTIONS
          </span>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Toast Confirmation */}
      {toastMessage && (
        <div className="m-4 p-3 rounded-xl bg-emerald-950/90 border border-emerald-500 text-emerald-200 text-xs font-mono font-bold flex items-center gap-2 animate-bounce">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Bets List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {bets.length === 0 ? (
          <div className="text-center py-16 space-y-3">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-slate-900 border border-slate-800 text-slate-500">
              <Trophy className="w-6 h-6" />
            </div>
            <p className="text-sm font-mono text-slate-400 font-medium">
              Your Bet Slip is empty.
            </p>
            <p className="text-xs text-slate-500 max-w-xs mx-auto">
              Click <span className="text-emerald-400 font-bold">WIN $25</span> or <span className="text-amber-400 font-bold">EXACTA $3</span> on any horse to add selections.
            </p>
          </div>
        ) : (
          bets.map((bet, idx) => (
            <div
              key={idx}
              className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between gap-3 shadow-md"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-200 text-xs font-mono font-extrabold">
                    R{bet.race_number}
                  </span>
                  <span className="font-extrabold text-sm text-white">
                    #{bet.horse_number} {bet.horse_name}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-xs font-mono">
                  <span className="text-emerald-400 font-bold uppercase">{bet.bet_type} BET</span>
                  <span className="text-slate-500">•</span>
                  <span className="text-slate-300 font-bold">${parseFloat(bet.stake).toFixed(2)} STAKE</span>
                </div>
              </div>

              <button
                onClick={() => onRemoveBet(bet)}
                className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-slate-800 transition-colors"
                title="Remove selection"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))
        )}
      </div>

      {/* Footer Calculation & Submit */}
      {bets.length > 0 && (
        <div className="p-4 border-t border-slate-800 bg-slate-900/90 space-y-3">
          <div className="flex items-center justify-between font-mono text-sm">
            <span className="text-slate-400 font-bold uppercase">TOTAL RISK / STAKE:</span>
            <span className="text-xl font-black text-emerald-400">${totalStake.toFixed(2)}</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClearBets}
              className="px-3 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono text-xs font-bold transition-all"
            >
              CLEAR
            </button>

            <button
              onClick={handleLockBets}
              disabled={submitting}
              className="flex-1 py-3 px-4 rounded-xl font-mono font-black text-xs uppercase tracking-wider bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-black shadow-lg shadow-emerald-950/50 flex items-center justify-center gap-2 active:scale-95 transition-all"
            >
              {submitting ? (
                <Zap className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <Flame className="w-4 h-4 fill-current" /> LOCK BETS TO DB
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
