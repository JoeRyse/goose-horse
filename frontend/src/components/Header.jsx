import React, { useState } from 'react';
import { Calendar, MapPin, Search, Printer, Flame, ChevronDown, X, Star, FileText } from 'lucide-react';
import { RegionBadge } from './Badges';

export default function Header({
  activeMeeting,
  meetings = [],
  onSelectMeeting,
  activeView = 'CARDS',
  onSelectView,
}) {
  const [isMeetingDrawerOpen, setIsMeetingDrawerOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('CURRENT');
  const [searchQuery, setSearchQuery] = useState('');

  const currentSavedMeetings = meetings.filter((m) => m.is_published);
  const displayedMeetings = (activeTab === 'CURRENT' ? currentSavedMeetings : meetings).filter((m) =>
    m.track.toLowerCase().includes(searchQuery.toLowerCase()) || m.date.includes(searchQuery)
  );

  return (
    <header className="sticky top-0 z-40 bg-[#003366] text-white border-b-4 border-[#10b981] shadow-md print:hidden">
      <div className="max-w-7xl mx-auto px-4 py-2.5 flex flex-wrap items-center justify-between gap-4">
        {/* Left Branding & High-Visibility Logo */}
        <div className="flex items-center gap-3.5">
          <div className="flex items-center gap-3.5">
            {/* Prominent High-Visibility Logo Box */}
            <div className="w-14 h-14 rounded-2xl bg-white border border-slate-200 p-1 shadow-md flex items-center justify-center relative overflow-hidden shrink-0">
              <img src="/logo.png" alt="Exacta AI Logo" className="w-full h-full object-contain" />
            </div>

            <div>
              <h1 className="text-xl font-black tracking-tight text-white font-mono flex items-center gap-1.5 drop-shadow-sm">
                EXACTA <span className="text-[#10b981] font-black">AI</span>
              </h1>
              <p className="text-[11px] text-emerald-200/90 font-mono font-bold hidden sm:block">
                Professional Handicapping Protocol & Racing Cards
              </p>
            </div>
          </div>

          <div className="h-8 w-px bg-blue-900 mx-1 hidden md:block"></div>

          {/* Current Active Meeting Selector */}
          {activeMeeting && (
            <button
              onClick={() => setIsMeetingDrawerOpen(true)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-blue-950/70 border border-blue-900 hover:border-[#10b981] transition-all text-left group"
            >
              <MapPin className="w-4 h-4 text-[#10b981] shrink-0" />
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-extrabold text-white group-hover:text-[#10b981] transition-colors">
                    {activeMeeting.track}
                  </span>
                  <RegionBadge region={activeMeeting.region} />
                </div>
                <div className="flex items-center gap-2 text-[11px] font-mono text-emerald-200/90 font-bold">
                  <span>📅 {activeMeeting.date}</span>
                  <span>•</span>
                  <span>{activeMeeting.track_condition || 'Standard'}</span>
                </div>
              </div>
              <ChevronDown className="w-4 h-4 text-[#10b981] group-hover:text-white transition-colors ml-1" />
            </button>
          )}
        </div>

        {/* Right Action Buttons */}
        <div className="flex items-center gap-2 font-mono">
          {/* Analytics View Toggle Button */}
          <button
            onClick={() => onSelectView && onSelectView(activeView === 'ANALYTICS' ? 'CARDS' : 'ANALYTICS')}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-black transition-all shadow-sm border ${
              activeView === 'ANALYTICS'
                ? 'bg-[#10b981] text-white border-[#10b981]'
                : 'bg-blue-950 hover:bg-blue-900 text-emerald-200 border-emerald-500/60'
            }`}
          >
            <span>📊 ANALYTICS & ROI</span>
          </button>

          {/* Select Track Button */}
          <button
            onClick={() => setIsMeetingDrawerOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-blue-950 hover:bg-blue-900 text-emerald-200 border border-emerald-500/60 text-xs font-bold transition-all shadow-sm"
          >
            <FileText className="w-3.5 h-3.5 text-[#10b981]" />
            <span>SELECT TRACK</span>
          </button>

          {/* Print PDF Button */}
          <button
            onClick={() => window.print()}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#10b981] hover:bg-emerald-600 text-white font-black text-xs uppercase tracking-wider shadow-md transition-all active:scale-95"
          >
            <Printer className="w-4 h-4" />
            <span>PRINT PDF</span>
          </button>
        </div>
      </div>

      {/* Meeting Selection Drawer Modal */}
      {isMeetingDrawerOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs print:hidden text-slate-900">
          <div className="w-full max-w-2xl bg-white rounded-2xl border border-slate-200 p-6 max-h-[85vh] flex flex-col shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <MapPin className="w-5 h-5 text-[#003366]" />
                <h3 className="text-base font-black text-slate-900 font-mono">Select Race Card / Track</h3>
              </div>
              <button
                onClick={() => setIsMeetingDrawerOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Filter Tabs */}
            <div className="py-3 space-y-3">
              <div className="flex items-center border-b border-slate-200 font-mono text-xs">
                <button
                  onClick={() => setActiveTab('CURRENT')}
                  className={`py-2 px-4 font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                    activeTab === 'CURRENT'
                      ? 'border-[#10b981] text-[#003366] font-black bg-emerald-50/50'
                      : 'border-transparent text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <Star className="w-4 h-4 text-[#10b981] fill-[#10b981]" />
                  CURRENT SAVED CARDS ({currentSavedMeetings.length})
                </button>

                <button
                  onClick={() => setActiveTab('ALL')}
                  className={`py-2 px-4 font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                    activeTab === 'ALL'
                      ? 'border-[#10b981] text-[#003366] font-black bg-emerald-50/50'
                      : 'border-transparent text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <FileText className="w-4 h-4 text-slate-400" />
                  ALL ARCHIVED CARDS ({meetings.length})
                </button>
              </div>

              {/* Search Bar */}
              <div className="relative">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="text"
                  placeholder="Search track name or date (e.g. Finger Lakes, Delaware Park)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-50 border border-slate-300 text-sm text-slate-900 font-mono font-medium focus:outline-none focus:border-[#10b981]"
                />
              </div>
            </div>

            {/* Meeting Grid */}
            <div className="flex-1 overflow-y-auto pr-1 space-y-2">
              {displayedMeetings.length === 0 ? (
                <div className="text-center py-10 text-slate-500 font-mono text-sm">
                  No saved cards found in <code className="bg-slate-100 px-1 py-0.5 rounded border border-slate-200">docs/meetings</code>.
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
                        ? 'bg-emerald-50/80 border-emerald-300 text-slate-950 font-bold shadow-xs'
                        : 'bg-white border-slate-200 hover:bg-slate-50 text-slate-800'
                    }`}
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-extrabold text-sm group-hover:text-[#003366] transition-colors">
                          {m.track}
                        </span>
                        <RegionBadge region={m.region} />
                        {m.is_published && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-100 text-emerald-900 border border-emerald-300">
                            🌟 CURRENT
                          </span>
                        )}
                      </div>
                      <div className="text-xs font-mono text-slate-500 mt-1 flex items-center gap-3">
                        <span>📅 {m.date}</span>
                        <span>•</span>
                        <span>{m.race_count} Races</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 font-mono text-xs">
                      {m.solo_locks_count > 0 && (
                        <span className="px-2.5 py-0.5 rounded-full bg-[#10b981] text-white font-bold">
                          🔥🔥 {m.solo_locks_count} Locks
                        </span>
                      )}
                      {m.best_bets_count > 0 && (
                        <span className="px-2.5 py-0.5 rounded-full bg-emerald-600 text-white font-bold">
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
