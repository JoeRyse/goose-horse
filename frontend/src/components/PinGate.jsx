import React, { useState } from 'react';
import { Lock, ShieldCheck, Zap, AlertCircle } from 'lucide-react';

export default function PinGate({ onAuthenticated }) {
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!pin) return;
    setLoading(true);
    setError('');

    try {
      const res = await fetch('/api/verify-pin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pin }),
      });
      const data = await res.json();
      if (data.success) {
        localStorage.setItem('exacta_auth_token', data.token);
        onAuthenticated();
      } else {
        setError('ACCESS DENIED: INVALID PIN CODE');
      }
    } catch (err) {
      if (pin === '7777') {
        localStorage.setItem('exacta_auth_token', 'local_token_7777');
        onAuthenticated();
      } else {
        setError('ACCESS DENIED: INVALID PIN CODE');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (num) => {
    if (pin.length < 6) {
      setPin((prev) => prev + num);
    }
  };

  const handleClear = () => setPin('');
  const handleDelete = () => setPin((prev) => prev.slice(0, -1));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950 p-4 font-mono">
      <div className="w-full max-w-md bg-white rounded-2xl border border-slate-200 p-8 shadow-2xl relative overflow-hidden text-slate-900">
        {/* Prominent Logo */}
        <div className="text-center mb-6">
          <div className="w-20 h-20 mx-auto mb-3 rounded-2xl bg-white border border-slate-200 p-2 shadow-md flex items-center justify-center">
            <img src="/logo.png" alt="Exacta AI Logo" className="w-full h-full object-contain" />
          </div>

          <h2 className="text-2xl font-black tracking-tight text-slate-900 flex items-center justify-center gap-1.5">
            EXACTA <span className="text-amber-600 font-extrabold">AI</span>
          </h2>
          <p className="text-xs font-bold text-slate-500 mt-1 uppercase">
            Private Racing Form Access
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* PIN Indicator dots */}
          <div className="flex justify-center items-center gap-3 py-3 bg-slate-50 rounded-xl border border-slate-200">
            {[0, 1, 2, 3].map((idx) => (
              <div
                key={idx}
                className={`w-4 h-4 rounded-full transition-all duration-300 border border-slate-300 ${
                  pin.length > idx
                    ? 'bg-emerald-600 scale-110 shadow-xs'
                    : 'bg-slate-200'
                }`}
              />
            ))}
          </div>

          {error && (
            <div className="flex items-center gap-2 p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-900 text-xs font-bold">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
              <span>{error}</span>
            </div>
          )}

          {/* Keypad */}
          <div className="grid grid-cols-3 gap-2.5 font-mono">
            {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((num) => (
              <button
                key={num}
                type="button"
                onClick={() => handleKeyPress(num.toString())}
                className="h-12 text-lg font-black rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-900 active:scale-95 shadow-xs transition-all"
              >
                {num}
              </button>
            ))}
            <button
              type="button"
              onClick={handleClear}
              className="h-12 text-xs font-bold uppercase rounded-xl bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-600 active:scale-95 transition-all"
            >
              CLR
            </button>
            <button
              type="button"
              onClick={() => handleKeyPress('0')}
              className="h-12 text-lg font-black rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-900 active:scale-95 shadow-xs transition-all"
            >
              0
            </button>
            <button
              type="button"
              onClick={handleDelete}
              className="h-12 text-xs font-bold uppercase rounded-xl bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-600 active:scale-95 transition-all"
            >
              DEL
            </button>
          </div>

          <button
            type="submit"
            disabled={loading || pin.length < 4}
            className="w-full py-3.5 px-4 rounded-xl font-black uppercase text-xs tracking-wider bg-emerald-600 hover:bg-emerald-500 text-white shadow-md disabled:opacity-50 disabled:cursor-not-allowed active:scale-95 transition-all flex items-center justify-center gap-2"
          >
            {loading ? (
              <Zap className="w-5 h-5 animate-spin" />
            ) : (
              <>
                <ShieldCheck className="w-5 h-5" /> UNLOCK FORM
              </>
            )}
          </button>
        </form>

        <div className="mt-5 pt-3 border-t border-slate-200 text-center">
          <p className="text-[11px] font-mono text-slate-500 font-bold">
            Access PIN: <span className="text-emerald-700 font-black">7777</span>
          </p>
        </div>
      </div>
    </div>
  );
}
