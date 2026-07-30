import React, { useState } from 'react';
import { Calendar, MapPin, Search, Printer, Flame, ChevronDown, X, Star, FileText } from 'lucide-react';
import { RegionBadge } from './Badges';

export default function Header({
  activeMeeting,
  meetings = [],
  onSelectMeeting,
}) {
  const [isMeetingDrawerOpen, setIsMeetingDrawerOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('CURRENT');
  const [searchQuery, setSearchQuery] = useState('');

  const currentSavedMeetings = meetings.filter((m) => m.is_published);
  const displayedMeetings = (activeTab === 'CURRENT' ? currentSavedMeetings : meetings).filter((m) =>
    m.track.toLowerCase().includes(searchQuery.toLowerCase()) || m.date.includes(searchQuery)
  );

  return (
    <header className="sticky top-0 z-40 bg-[#881337] text-white border-b-2 border-amber-500 shadow-md print:hidden">
      <div className="max-w-7xl mx-auto px-4 py-2.5 flex flex-wrap items-center justify-between gap-4">
        {/* Left Branding & High-Visibility Logo */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-3">
            {/* Saratoga Crimson Logo Card */}
            <div className="w-10 h-10 rounded-xl bg-white border-2 border-amber-400 p-0.5 shadow-sm flex items-center justify-center relative overflow-hidden">
              <img src="/logo.png" alt="Exacta AI Logo" className="w-full h-full object-contain" />
            </div>

            <div>
              <h1 className="text-lg font-black tracking-tight text-white font-mono flex items-center gap-1.5 drop-shadow-sm">
                EXACTA <span className="text-amber-300 font-black">AI</span>
              </h1>
              <p className="text-[10px] text-amber-200/90 font-mono font-bold hidden sm:block">
                Saratoga Style Handicapping & Racing Cards
              </p>
            </div>
          </div>

          <div className="h-7 w-px bg-rose-900 mx-1 hidden md:block"></div>

          {/* Current Active Meeting Selector */}
          {activeMeeting && (
            <button
              onClick={() => setIsMeetingDrawerOpen(true)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-rose-950/60 hover:bg-rose-950 border border-amber-500/50 text-left transition-all group shadow-sm"
            >
              <MapPin className="w-4 h-4 text-amber-300 shrink-0" />
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-extrabold text-white group-hover:text-amber-300 transition-colors">
                    {activeMeeting.track}
                  </span>
                  <RegionBadge region={activeMeeting.region} />
                </div>
                <div className="flex items-center gap-2 text-[11px] font-mono text-amber-200/90 font-bold">
                  <span>📅 {activeMeeting.date}</span>
                  <span>•</span>
                  <span>{activeMeeting.track_condition || 'Standard'}</span>
                </div>
              </div>
              <ChevronDown className="w-4 h-4 text-amber-300 group-hover:text-white transition-colors ml-1" />
            </button>
          )}
        </div>

        {/* Right Action Buttons */}
        <div className="flex items-center gap-2 font-mono">
          {/* Select Track Button */}
          <button
            onClick={() => setIsMeetingDrawerOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-950 hover:bg-rose-900 text-amber-200 border border-amber-500/60 text-xs font-bold transition-all shadow-sm"
          >
            <FileText className="w-3.5 h-3.5 text-amber-300" />
            <span>SELECT TRACK</span>
          </button>

          {/* Print PDF Button */}
          <button
            onClick={() => window.print()}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-black text-xs uppercase tracking-wider border border-amber-300 shadow-md transition-all active:scale-95"
          >
            <Printer className="w-3.5 h-3.5 text-slate-950" />
            <span>PRINT PDF</span>
          </button>
        </div>
      </div>

      {/* Meeting Selection Drawer Modal */}
      {isMeetingDrawerOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs print:hidden text-slate-900">
          <div className="w-full max-w-2xl bg-white rounded-2xl border border-stone-200 p-6 max-h-[85vh] flex flex-col shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-stone-200">
              <div className="flex items-center gap-2">
                <MapPin className="w-5 h-5 text-[#881337]" />
                <h3 className="text-base font-black text-slate-900 font-mono">Select Race Card / Track</h3>
              </div>
              <button
                onClick={() => setIsMeetingDrawerOpen(false)}
                className="p-1 rounded-lg text-stone-400 hover:text-stone-700 hover:bg-stone-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Filter Tabs */}
            <div className="py-3 space-y-3">
              <div className="flex items-center border-b border-stone-200 font-mono text-xs">
                <button
                  onClick={() => setActiveTab('CURRENT')}
                  className={`py-2 px-4 font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                    activeTab === 'CURRENT'
                      ? 'border-[#881337] text-[#881337] font-black bg-rose-50/50'
                      : 'border-transparent text-stone-500 hover:text-stone-800'
                  }`}
                >
                  <Star className="w-4 h-4 text-amber-500 fill-amber-500" />
                  CURRENT SAVED CARDS ({currentSavedMeetings.length})
                </button>

                <button
                  onClick={() => setActiveTab('ALL')}
                  className={`py-2 px-4 font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                    activeTab === 'ALL'
                      ? 'border-[#881337] text-[#881337] font-black bg-rose-50/50'
                      : 'border-transparent text-stone-500 hover:text-stone-800'
                  }`}
                >
                  <FileText className="w-4 h-4 text-stone-400" />
                  ALL ARCHIVED CARDS ({meetings.length})
                </button>
              </div>

              {/* Search Bar */}
              <div className="relative">
                <Search className="w-4 h-4 text-stone-400 absolute left-3 top-3" />
                <input
                  type="text"
                  placeholder="Search track name or date (e.g. Finger Lakes, Delaware Park)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 rounded-xl bg-stone-50 border border-stone-300 text-sm text-slate-900 font-mono font-medium focus:outline-none focus:border-[#881337]"
                />
              </div>
            </div>

            {/* Meeting Grid */}
            <div className="flex-1 overflow-y-auto pr-1 space-y-2">
              {displayedMeetings.length === 0 ? (
                <div className="text-center py-10 text-stone-500 font-mono text-sm">
                  No saved cards found in <code className="bg-stone-100 px-1 py-0.5 rounded border border-stone-200">docs/meetings</code>.
                </div>
              ) : (
                displayedMeetings.map((m) => (
                  <button
                    key={m.id}
                    onClick={() => {
                      onSelectMeeting(m);
                      setIsMeetingDrawerOpen(false);
                    }}
                    className={`w-full text-left p-3.5 rounded-xl border transition-all flex items-center justify-between group ${
                      activeMeeting?.id === m.id
                        ? 'bg-rose-50/80 border-rose-300 text-slate-950 font-bold shadow-xs'
                        : 'bg-white border-stone-200 hover:bg-stone-50 text-slate-800'
                    }`}
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-extrabold text-sm group-hover:text-[#881337] transition-colors">
                          {m.track}
                        </span>
                        <RegionBadge region={m.region} />
                        {m.is_published && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-100 text-amber-900 border border-amber-300">
                            🌟 CURRENT
                          </span>
                        )}
                      </div>
                      <div className="text-xs font-mono text-stone-500 mt-1 flex items-center gap-3">
                        <span>📅 {m.date}</span>
                        <span>•</span>
                        <span>{m.race_count} Races</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 font-mono text-xs">
                      {m.solo_locks_count > 0 && (
                        <span className="px-2.5 py-0.5 rounded-full bg-[#881337] text-white font-bold border border-amber-400">
                          🔥🔥 {m.solo_locks_count} Locks
                        </span>
                      )}
                      {m.best_bets_count > 0 && (
                        <span className="px-2.5 py-0.5 rounded-full bg-amber-600 text-white font-bold border border-amber-400">
                          🔥 {m.best_bets_count} Best
                        </span>
                      )}
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
