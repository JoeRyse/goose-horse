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
    <header className="sticky top-0 z-40 bg-white text-slate-900 border-b border-slate-200 print:hidden shadow-xs">
      <div className="max-w-7xl mx-auto px-4 py-2.5 flex flex-wrap items-center justify-between gap-4">
        {/* Left Branding & High-Visibility Logo */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-white border border-slate-200 p-0.5 shadow-xs flex items-center justify-center relative overflow-hidden">
              <img src="/logo.png" alt="Exacta AI Logo" className="w-full h-full object-contain" />
            </div>

            <div>
              <h1 className="text-base font-bold tracking-tight text-slate-900 flex items-center gap-1">
                EXACTA <span className="text-[#0066cc] font-extrabold">AI</span>
              </h1>
              <p className="text-[10px] text-slate-500 font-medium hidden sm:block">
                Sportsbook Handicapping Intelligence
              </p>
            </div>
          </div>

          <div className="h-6 w-px bg-slate-200 mx-1 hidden md:block"></div>

          {/* Current Active Meeting Selector */}
          {activeMeeting && (
            <button
              onClick={() => setIsMeetingDrawerOpen(true)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 text-left transition-all group"
            >
              <MapPin className="w-3.5 h-3.5 text-[#0066cc] shrink-0" />
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-900 group-hover:text-[#0066cc] transition-colors">
                    {activeMeeting.track}
                  </span>
                  <RegionBadge region={activeMeeting.region} />
                </div>
                <div className="flex items-center gap-2 text-[10px] text-slate-500 font-medium">
                  <span>📅 {activeMeeting.date}</span>
                  <span>•</span>
                  <span>{activeMeeting.track_condition || 'Standard'}</span>
                </div>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-700 transition-colors ml-1" />
            </button>
          )}
        </div>

        {/* Right Action Buttons */}
        <div className="flex items-center gap-2">
          {/* Select Track Button */}
          <button
            onClick={() => setIsMeetingDrawerOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-200 text-xs font-semibold transition-all"
          >
            <FileText className="w-3.5 h-3.5 text-[#0066cc]" />
            <span>SELECT TRACK</span>
          </button>

          {/* Print PDF Button */}
          <button
            onClick={() => window.print()}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-[#0066cc] hover:bg-blue-700 text-white font-semibold text-xs transition-all shadow-xs active:scale-95"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>PRINT PDF</span>
          </button>
        </div>
      </div>

      {/* Meeting Selection Drawer Modal */}
      {isMeetingDrawerOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs print:hidden">
          <div className="w-full max-w-2xl bg-white rounded-xl border border-slate-200 p-5 max-h-[85vh] flex flex-col shadow-xl text-slate-900">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-[#0066cc]" />
                <h3 className="text-sm font-bold text-slate-900">Select Race Card / Track</h3>
              </div>
              <button
                onClick={() => setIsMeetingDrawerOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Filter Tabs */}
            <div className="py-2.5 space-y-2.5">
              <div className="flex items-center border-b border-slate-200 text-xs font-medium">
                <button
                  onClick={() => setActiveTab('CURRENT')}
                  className={`py-2 px-3 font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
                    activeTab === 'CURRENT'
                      ? 'border-[#0066cc] text-[#0066cc]'
                      : 'border-transparent text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <Star className="w-3.5 h-3.5 text-amber-500 fill-amber-500" />
                  CURRENT SAVED CARDS ({currentSavedMeetings.length})
                </button>

                <button
                  onClick={() => setActiveTab('ALL')}
                  className={`py-2 px-3 font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
                    activeTab === 'ALL'
                      ? 'border-[#0066cc] text-[#0066cc]'
                      : 'border-transparent text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <FileText className="w-3.5 h-3.5 text-slate-400" />
                  ALL ARCHIVED CARDS ({meetings.length})
                </button>
              </div>

              {/* Search Bar */}
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search track name or date (e.g. Finger Lakes, Delaware Park)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-900 font-medium focus:outline-none focus:border-[#0066cc]"
                />
              </div>
            </div>

            {/* Meeting Grid */}
            <div className="flex-1 overflow-y-auto pr-1 space-y-1.5">
              {displayedMeetings.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-xs">
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
                    className={`w-full text-left p-3 rounded-lg border transition-all flex items-center justify-between group ${
                      activeMeeting?.id === m.id
                        ? 'bg-blue-50/60 border-blue-200 text-slate-950 font-semibold'
                        : 'bg-white border-slate-200 hover:bg-slate-50 text-slate-800'
                    }`}
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-xs group-hover:text-[#0066cc] transition-colors">
                          {m.track}
                        </span>
                        <RegionBadge region={m.region} />
                        {m.is_published && (
                          <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-amber-50 text-amber-900 border border-amber-200">
                            🌟 CURRENT
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-slate-500 mt-0.5 flex items-center gap-2">
                        <span>📅 {m.date}</span>
                        <span>•</span>
                        <span>{m.race_count} Races</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5 text-[11px]">
                      {m.solo_locks_count > 0 && (
                        <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 font-semibold">
                          🔒 {m.solo_locks_count} Locks
                        </span>
                      )}
                      {m.best_bets_count > 0 && (
                        <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-800 border border-blue-200 font-semibold">
                          ⭐ {m.best_bets_count} Best
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
