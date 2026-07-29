import React, { useState } from 'react';
import { Calendar, MapPin, Search, Printer, Flame, ChevronDown, X, Star, FileText, UploadCloud, CheckCircle } from 'lucide-react';
import { RegionBadge } from './Badges';

export default function Header({
  activeMeeting,
  meetings = [],
  onSelectMeeting,
}) {
  const [isMeetingDrawerOpen, setIsMeetingDrawerOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('CURRENT');
  const [searchQuery, setSearchQuery] = useState('');
  const [isPublishing, setIsPublishing] = useState(false);
  const [publishStatus, setPublishStatus] = useState('');

  const currentSavedMeetings = meetings.filter((m) => m.is_published);
  const displayedMeetings = (activeTab === 'CURRENT' ? currentSavedMeetings : meetings).filter((m) =>
    m.track.toLowerCase().includes(searchQuery.toLowerCase()) || m.date.includes(searchQuery)
  );

  const handlePublishToGithub = async () => {
    setIsPublishing(true);
    setPublishStatus('Publishing updates to GitHub & Vercel...');
    try {
      const res = await fetch('/api/publish-github', { method: 'POST' });
      const data = await res.json();
      if (data.status === 'success') {
        setPublishStatus('🚀 SUCCESS! Syncing to Vercel...');
        setTimeout(() => setPublishStatus(''), 4000);
      } else {
        setPublishStatus('Publish failed.');
      }
    } catch (e) {
      setPublishStatus('Local server offline.');
    } finally {
      setIsPublishing(false);
    }
  };

  return (
    <header className="sticky top-0 z-40 bg-white text-slate-900 shadow-md border-b border-slate-200 print:hidden">
      <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-4">
        {/* Left Branding & High-Visibility Logo */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-3">
            {/* Crisp Light Logo Container */}
            <div className="w-12 h-12 rounded-xl bg-white border-2 border-slate-200 p-1 shadow-xs flex items-center justify-center relative overflow-hidden group">
              <img src="/logo.png" alt="Exacta AI Logo" className="w-full h-full object-contain" />
            </div>

            <div>
              <h1 className="text-xl font-black tracking-tight text-slate-900 font-mono flex items-center gap-1.5">
                EXACTA <span className="text-amber-600 font-extrabold">AI</span>
              </h1>
              <p className="text-[10px] text-slate-500 font-mono font-bold hidden sm:block">
                Professional Handicapping & Racing Cards
              </p>
            </div>
          </div>

          <div className="h-8 w-px bg-slate-200 mx-1 hidden md:block"></div>

          {/* Current Active Meeting Info Selector */}
          {activeMeeting && (
            <button
              onClick={() => setIsMeetingDrawerOpen(true)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-left transition-all group shadow-xs"
            >
              <MapPin className="w-4 h-4 text-emerald-600 shrink-0" />
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-extrabold text-slate-900 group-hover:text-emerald-700 transition-colors">
                    {activeMeeting.track}
                  </span>
                  <RegionBadge region={activeMeeting.region} />
                </div>
                <div className="flex items-center gap-2 text-[11px] font-mono text-slate-500 font-bold">
                  <span>📅 {activeMeeting.date}</span>
                  <span>•</span>
                  <span>{activeMeeting.track_condition || 'Standard'}</span>
                </div>
              </div>
              <ChevronDown className="w-4 h-4 text-slate-400 group-hover:text-slate-700 transition-colors ml-1" />
            </button>
          )}
        </div>

        {/* Right Action Buttons */}
        <div className="flex items-center gap-2 font-mono">
          {/* 1-Click Push to Vercel / GitHub Button */}
          <button
            onClick={handlePublishToGithub}
            disabled={isPublishing}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-amber-400 border border-slate-900 text-xs font-black transition-all shadow-xs disabled:opacity-50"
            title="Push new track cards to GitHub & Vercel"
          >
            <UploadCloud className={`w-4 h-4 ${isPublishing ? 'animate-bounce text-amber-300' : 'text-amber-400'}`} />
            <span className="hidden sm:inline">{isPublishing ? 'PUSHING...' : 'PUSH TO VERCEL'}</span>
          </button>

          {/* Select Track Button */}
          <button
            onClick={() => setIsMeetingDrawerOpen(true)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-300 text-xs font-black transition-all shadow-xs"
          >
            <FileText className="w-4 h-4 text-amber-600" />
            <span className="hidden sm:inline">SELECT TRACK</span>
          </button>

          {/* Print PDF Button */}
          <button
            onClick={() => window.print()}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-black text-xs uppercase tracking-wider shadow-md transition-all active:scale-95"
          >
            <Printer className="w-4 h-4" />
            <span>PRINT PDF</span>
          </button>
        </div>
      </div>

      {/* Publish Toast Notification */}
      {publishStatus && (
        <div className="bg-amber-100 border-t border-b border-amber-300 py-1.5 px-4 text-center text-xs font-mono font-bold text-amber-950 flex items-center justify-center gap-2">
          <CheckCircle className="w-4 h-4 text-amber-700 animate-pulse" />
          <span>{publishStatus}</span>
        </div>
      )}

      {/* Meeting Selection Drawer Modal */}
      {isMeetingDrawerOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm print:hidden">
          <div className="w-full max-w-2xl bg-white rounded-2xl border border-slate-200 p-6 max-h-[85vh] flex flex-col shadow-2xl text-slate-900">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <MapPin className="w-5 h-5 text-emerald-600" />
                <h3 className="text-lg font-black text-slate-900 font-mono">Select Race Card / Track</h3>
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
                      ? 'border-emerald-600 text-emerald-700 font-black bg-emerald-50/50'
                      : 'border-transparent text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <Star className="w-4 h-4 text-amber-500 fill-amber-500" />
                  CURRENT SAVED CARDS ({currentSavedMeetings.length})
                </button>

                <button
                  onClick={() => setActiveTab('ALL')}
                  className={`py-2 px-4 font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                    activeTab === 'ALL'
                      ? 'border-emerald-600 text-emerald-700 font-black bg-emerald-50/50'
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
                  placeholder="Search track name or date (e.g. Finger Lakes, Delaware Park, 2026-07-29)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-50 border border-slate-300 text-sm text-slate-900 font-mono font-medium focus:outline-none focus:border-emerald-600"
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
                        : 'bg-white border-slate-200 hover:bg-slate-50 hover:border-slate-300 text-slate-800'
                    }`}
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-extrabold text-sm group-hover:text-emerald-700 transition-colors">
                          {m.track}
                        </span>
                        <RegionBadge region={m.region} />
                        {m.is_published && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-100 text-amber-900 border border-amber-300">
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
                        <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-900 border border-emerald-300 font-bold">
                          🔥🔥 {m.solo_locks_count} Locks
                        </span>
                      )}
                      {m.best_bets_count > 0 && (
                        <span className="px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300 font-bold">
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
