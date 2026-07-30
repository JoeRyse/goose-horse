import React, { useState, useEffect } from 'react';
import { TrendingUp, DollarSign, Award, Target, Flame, Sparkles, Trophy, BarChart2, Filter, RefreshCw, Calendar, MapPin, Layers, CheckCircle, XCircle, FileText } from 'lucide-react';

export default function AnalyticsDashboard() {
  const [filterGroup, setFilterGroup] = useState('US_TIER1');
  const [targetTrack, setTargetTrack] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [surface, setSurface] = useState('ALL');
  const [condition, setCondition] = useState('ALL');
  const [distType, setDistType] = useState('ALL');
  const [raceClass, setRaceClass] = useState('ALL');

  const [availableTracks, setAvailableTracks] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTracks();
  }, []);

  useEffect(() => {
    fetchAnalytics();
  }, [filterGroup, targetTrack, startDate, endDate, surface, condition, distType, raceClass]);

  const fetchTracks = async () => {
    try {
      const res = await fetch('/api/analytics/tracks');
      const data = await res.json();
      if (data.status === 'success' && data.tracks) {
        setAvailableTracks(data.tracks);
      }
    } catch (err) {}
  };

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      let queryParams = new URLSearchParams({
        filter: filterGroup,
        track: targetTrack,
        start_date: startDate,
        end_date: endDate,
        surface,
        condition,
        dist_type: distType,
        race_class: raceClass,
      });

      let data = null;
      try {
        const res = await fetch(`/api/analytics/roi?${queryParams.toString()}`);
        data = await res.json();
      } catch (err) {
        const res = await fetch(`http://127.0.0.1:8085/api/analytics/roi?${queryParams.toString()}`);
        data = await res.json();
      }

      if (data && data.status === 'success' && data.analytics) {
        setAnalytics(data.analytics);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleResetFilters = () => {
    setFilterGroup('US_TIER1');
    setTargetTrack('');
    setStartDate('');
    setEndDate('');
    setSurface('ALL');
    setCondition('ALL');
    setDistType('ALL');
    setRaceClass('ALL');
  };

  return (
    <div className="space-y-6 font-sans">
      {/* Header Banner */}
      <div className="bg-[#003366] text-white rounded-2xl p-5 border-b-4 border-[#10b981] shadow-md font-mono">
        <div className="flex items-center gap-2.5 mb-2">
          <span className="p-2 rounded-xl bg-[#10b981] text-white font-black">
            <BarChart2 className="w-5 h-5" />
          </span>
          <h2 className="text-xl font-black tracking-tight text-white">
            GRANULAR ROI & PERFORMANCE ANALYTICS
          </h2>
        </div>
        <p className="text-xs text-emerald-200 font-medium">
          Filter by Track, Date Range, Dirt vs Turf, Sprint vs Route, Track Condition, and Maiden vs Non-Maiden.
        </p>

        {/* Preset Track Tier Buttons */}
        <div className="flex flex-wrap items-center gap-2 mt-4">
          <button
            onClick={() => { setFilterGroup('US_TIER1'); setTargetTrack(''); }}
            className={`px-3 py-1.5 rounded-xl text-xs font-black transition-all border ${
              filterGroup === 'US_TIER1' && !targetTrack
                ? 'bg-[#10b981] text-white border-[#10b981] shadow-xs'
                : 'bg-blue-950/60 text-emerald-100 border-blue-900 hover:bg-blue-900'
            }`}
          >
            🇺🇸 US TIER-1 PREMIER (Saratoga, Del Mar...)
          </button>

          <button
            onClick={() => { setFilterGroup('AUS_HIGH_HIT'); setTargetTrack(''); }}
            className={`px-3 py-1.5 rounded-xl text-xs font-black transition-all border ${
              filterGroup === 'AUS_HIGH_HIT' && !targetTrack
                ? 'bg-[#10b981] text-white border-[#10b981] shadow-xs'
                : 'bg-blue-950/60 text-emerald-100 border-blue-900 hover:bg-blue-900'
            }`}
          >
            🇦🇺 AUS HIGH HIT RATE (Flemington, Randwick...)
          </button>

          <button
            onClick={() => { setFilterGroup('ALL'); setTargetTrack(''); }}
            className={`px-3 py-1.5 rounded-xl text-xs font-black transition-all border ${
              filterGroup === 'ALL' && !targetTrack
                ? 'bg-[#10b981] text-white border-[#10b981] shadow-xs'
                : 'bg-blue-950/60 text-emerald-100 border-blue-900 hover:bg-blue-900'
            }`}
          >
            🌐 ALL TRACKS
          </button>
        </div>
      </div>

      {/* GRANULAR FILTERS DRAWER / CONTROL PANEL */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs space-y-4 font-mono text-xs text-slate-800">
        <div className="flex items-center justify-between pb-3 border-b border-slate-200">
          <div className="flex items-center gap-2 font-black text-[#003366] uppercase text-sm">
            <Filter className="w-4 h-4 text-[#10b981]" />
            <span>DEEP GRANULAR FILTERS</span>
          </div>
          <button
            onClick={handleResetFilters}
            className="text-[11px] font-bold text-slate-500 hover:text-slate-900 underline"
          >
            Reset Filters
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {/* Individual Track Selector */}
          <div>
            <label className="block text-[11px] font-bold text-slate-500 mb-1 uppercase">
              Racetrack
            </label>
            <select
              value={targetTrack}
              onChange={(e) => { setTargetTrack(e.target.value); setFilterGroup('CUSTOM'); }}
              className="w-full p-2 bg-slate-50 border border-slate-200 rounded-xl font-bold text-slate-900 text-xs focus:ring-2 focus:ring-[#10b981]"
            >
              <option value="">All Racetracks</option>
              {availableTracks.map((t, idx) => (
                <option key={idx} value={t}>{t}</option>
              ))}
            </select>
          </div>

          {/* Date Range Start */}
          <div>
            <label className="block text-[11px] font-bold text-slate-500 mb-1 uppercase">
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full p-2 bg-slate-50 border border-slate-200 rounded-xl font-bold text-slate-900 text-xs focus:ring-2 focus:ring-[#10b981]"
            />
          </div>

          {/* Date Range End */}
          <div>
            <label className="block text-[11px] font-bold text-slate-500 mb-1 uppercase">
              End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full p-2 bg-slate-50 border border-slate-200 rounded-xl font-bold text-slate-900 text-xs focus:ring-2 focus:ring-[#10b981]"
            />
          </div>

          {/* Surface Filter */}
          <div>
            <label className="block text-[11px] font-bold text-slate-500 mb-1 uppercase">
              Surface
            </label>
            <select
              value={surface}
              onChange={(e) => setSurface(e.target.value)}
              className="w-full p-2 bg-slate-50 border border-slate-200 rounded-xl font-bold text-slate-900 text-xs focus:ring-2 focus:ring-[#10b981]"
            >
              <option value="ALL">All Surfaces</option>
              <option value="DIRT">Dirt Only</option>
              <option value="TURF">Turf Only</option>
              <option value="SYNTHETIC">Synthetic Only</option>
            </select>
          </div>

          {/* Distance Filter (Sprint vs Route) */}
          <div>
            <label className="block text-[11px] font-bold text-slate-500 mb-1 uppercase">
              Distance
            </label>
            <select
              value={distType}
              onChange={(e) => setDistType(e.target.value)}
              className="w-full p-2 bg-slate-50 border border-slate-200 rounded-xl font-bold text-slate-900 text-xs focus:ring-2 focus:ring-[#10b981]"
            >
              <option value="ALL">All Distances</option>
              <option value="SPRINT">Sprints (&lt; 8F / 1600m)</option>
              <option value="ROUTE">Routes (&ge; 8F / 1600m)</option>
            </select>
          </div>

          {/* Maiden vs Non-Maiden */}
          <div>
            <label className="block text-[11px] font-bold text-slate-500 mb-1 uppercase">
              Race Class
            </label>
            <select
              value={raceClass}
              onChange={(e) => setRaceClass(e.target.value)}
              className="w-full p-2 bg-slate-50 border border-slate-200 rounded-xl font-bold text-slate-900 text-xs focus:ring-2 focus:ring-[#10b981]"
            >
              <option value="ALL">All Race Classes</option>
              <option value="MAIDEN">Maiden Races Only</option>
              <option value="NON_MAIDEN">Non-Maiden (Allowance/Stakes)</option>
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 font-mono text-slate-600 space-y-3">
          <RefreshCw className="w-8 h-8 text-[#10b981] animate-spin" />
          <span className="text-xs font-bold">Querying Granular Database & Multi-Race Sequences...</span>
        </div>
      ) : analytics ? (
        <div className="space-y-6">
          {/* Main Key Performance Indicators (KPIs) Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono">
            {/* Solo Lock +5.0 Gap KPI */}
            <div className="bg-white rounded-2xl p-4 border border-emerald-300 shadow-xs space-y-2 bg-emerald-50/30">
              <div className="flex items-center justify-between text-xs text-slate-500 font-bold">
                <span>🔥🔥 SOLO LOCK (+5.0 GAP)</span>
                <span className="px-2 py-0.5 rounded bg-[#10b981] text-white font-black text-[10px]">$20 WIN</span>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-black text-[#065f46]">{analytics.solo_lock?.win_rate}%</span>
                <span className="text-sm font-extrabold text-[#10b981]">+{analytics.solo_lock?.roi}% ROI</span>
              </div>
              <div className="text-[11px] text-slate-600 flex justify-between font-semibold">
                <span>Record: {analytics.solo_lock?.wins} / {analytics.solo_lock?.total_bets} Wins</span>
                <span>P&L: <strong className="text-[#065f46]">+${analytics.solo_lock?.pnl}</strong></span>
              </div>
            </div>

            {/* Best Bet +3.0 Gap KPI */}
            <div className="bg-white rounded-2xl p-4 border border-emerald-300 shadow-xs space-y-2 bg-emerald-50/20">
              <div className="flex items-center justify-between text-xs text-slate-500 font-bold">
                <span>🔥 BEST BET (+3.0 GAP)</span>
                <span className="px-2 py-0.5 rounded bg-emerald-600 text-white font-black text-[10px]">$10 WIN</span>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-black text-[#065f46]">{analytics.best_bet?.win_rate}%</span>
                <span className="text-sm font-extrabold text-[#10b981]">+{analytics.best_bet?.roi}% ROI</span>
              </div>
              <div className="text-[11px] text-slate-600 flex justify-between font-semibold">
                <span>Record: {analytics.best_bet?.wins} / {analytics.best_bet?.total_bets} Wins</span>
                <span>P&L: <strong className="text-[#065f46]">+${analytics.best_bet?.pnl}</strong></span>
              </div>
            </div>

            {/* Top Pick Win KPI */}
            <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-500 font-bold">
                <span>🏁 TOP PICK OVERALL</span>
                <span className="px-2 py-0.5 rounded bg-[#003366] text-white font-black text-[10px]">$5 WIN</span>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-black text-[#003366]">{analytics.top_pick_win?.win_rate}%</span>
                <span className="text-sm font-extrabold text-[#10b981]">+{analytics.top_pick_win?.roi}% ROI</span>
              </div>
              <div className="text-[11px] text-slate-600 flex justify-between font-semibold">
                <span>Record: {analytics.top_pick_win?.wins} / {analytics.top_pick_win?.total_bets} Wins</span>
                <span>P&L: <strong className="text-[#065f46]">+${analytics.top_pick_win?.pnl}</strong></span>
              </div>
            </div>

            {/* Total Profit & Loss Summary KPI */}
            <div className="bg-[#003366] text-white rounded-2xl p-4 border-b-4 border-[#10b981] shadow-xs space-y-2">
              <div className="flex items-center justify-between text-xs text-emerald-200 font-bold">
                <span>💰 OVERALL P&L / NET RETURN</span>
                <span className="px-2 py-0.5 rounded bg-[#10b981] text-white font-black text-[10px]">COMBINED</span>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-black text-[#10b981]">+${analytics.overall?.pnl}</span>
                <span className="text-sm font-extrabold text-emerald-300">+{analytics.overall?.roi}% ROI</span>
              </div>
              <div className="text-[11px] text-emerald-200 flex justify-between font-medium">
                <span>Analyzed: {analytics.meetings_analyzed} Cards ({analytics.total_races} Races)</span>
              </div>
            </div>
          </div>

          {/* DETAILED LINE-BY-LINE RACE AUDIT LOG TABLE */}
          {analytics.race_logs && analytics.race_logs.length > 0 && (
            <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs space-y-4 font-mono">
              <div className="flex items-center justify-between pb-2 border-b border-slate-200">
                <div className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-[#10b981]" />
                  <h3 className="text-base font-black text-[#003366] uppercase">
                    DETAILED RACE AUDIT LOG ({analytics.race_logs.length} RACES SHOWN)
                  </h3>
                </div>
                <span className="text-xs text-slate-500 font-sans">
                  Line-by-line race breakdown for exact cross-verification
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-100 text-slate-700 font-black border-b border-slate-200 uppercase text-[11px]">
                      <th className="p-2.5">Date</th>
                      <th className="p-2.5">Track</th>
                      <th className="p-2.5">Race #</th>
                      <th className="p-2.5">Top AI Pick</th>
                      <th className="p-2.5">Rating / Gap</th>
                      <th className="p-2.5">Wager Tag</th>
                      <th className="p-2.5">Result</th>
                      <th className="p-2.5">Payout ($)</th>
                      <th className="p-2.5 text-right">P&L ($)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-semibold text-slate-800">
                    {analytics.race_logs.map((log, i) => (
                      <tr key={i} className="hover:bg-slate-50 transition-colors">
                        <td className="p-2.5 font-bold text-slate-600">{log.date}</td>
                        <td className="p-2.5 font-bold text-[#003366]">{log.track}</td>
                        <td className="p-2.5 font-black text-center">R{log.race_number}</td>
                        <td className="p-2.5">
                          <span className="font-black text-[#003366]">#{log.p1_num}</span> {log.p1_name}
                        </td>
                        <td className="p-2.5 text-slate-600">
                          <span className="font-bold text-[#10b981]">{log.rating}</span> ({log.gap} Gap)
                        </td>
                        <td className="p-2.5">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-black ${
                            log.bet_tag.includes('SOLO') 
                              ? 'bg-emerald-600 text-white' 
                              : log.bet_tag.includes('BEST') 
                              ? 'bg-emerald-100 text-emerald-800' 
                              : 'bg-slate-100 text-slate-700'
                          }`}>
                            {log.bet_tag}
                          </span>
                        </td>
                        <td className="p-2.5">
                          {log.status === 'WIN' ? (
                            <span className="inline-flex items-center gap-1 text-emerald-600 font-black">
                              <CheckCircle className="w-3.5 h-3.5" /> WIN
                            </span>
                          ) : log.status === 'LOSS' ? (
                            <span className="inline-flex items-center gap-1 text-rose-600 font-bold">
                              <XCircle className="w-3.5 h-3.5" /> LOSS
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-amber-600 font-bold bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                              PENDING
                            </span>
                          )}
                        </td>
                        <td className="p-2.5 font-bold text-slate-700">
                          {log.has_result ? `$${log.payout.toFixed(2)}` : '--'}
                        </td>
                        <td className={`p-2.5 text-right font-black ${
                          !log.has_result 
                            ? 'text-slate-400' 
                            : log.pnl > 0 
                            ? 'text-[#065f46]' 
                            : 'text-rose-600'
                        }`}>
                          {!log.has_result ? '$0.00 (Pending)' : log.pnl > 0 ? `+$${log.pnl.toFixed(2)}` : `-$${log.stake.toFixed(2)}`}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TOP 2 CONTENDERS MULTI-RACE STRING TRACKER */}
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs space-y-4 font-mono">
            <div className="flex items-center gap-2.5 pb-2 border-b border-slate-200">
              <Trophy className="w-5 h-5 text-[#10b981]" />
              <div>
                <h3 className="text-base font-black text-[#003366] uppercase">
                  TOP 2 CONTENDERS MULTI-RACE STRING TRACKER
                </h3>
                <p className="text-xs text-slate-500 font-medium font-sans">
                  Hit rate & sequence statistics if stringing together the Top 2 AI Contenders per race leg.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
                <div className="flex items-center justify-between text-xs font-bold text-slate-700">
                  <span>PICK 3 SEQUENCE</span>
                  <span className="px-2 py-0.5 rounded bg-emerald-100 text-[#065f46] text-[10px] font-black">
                    {analytics.multi_race_tracker?.pick_3?.hit_rate}% HIT
                  </span>
                </div>
                <div className="text-xl font-black text-[#003366]">
                  {analytics.multi_race_tracker?.pick_3?.hits} / {analytics.multi_race_tracker?.pick_3?.attempted} <span className="text-xs text-slate-500 font-normal">Hits</span>
                </div>
                <p className="text-[11px] text-slate-500">2 Contenders per Leg (8 Combos)</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
                <div className="flex items-center justify-between text-xs font-bold text-slate-700">
                  <span>PICK 4 SEQUENCE</span>
                  <span className="px-2 py-0.5 rounded bg-emerald-100 text-[#065f46] text-[10px] font-black">
                    {analytics.multi_race_tracker?.pick_4?.hit_rate}% HIT
                  </span>
                </div>
                <div className="text-xl font-black text-[#003366]">
                  {analytics.multi_race_tracker?.pick_4?.hits} / {analytics.multi_race_tracker?.pick_4?.attempted} <span className="text-xs text-slate-500 font-normal">Hits</span>
                </div>
                <p className="text-[11px] text-slate-500">2 Contenders per Leg (16 Combos)</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
                <div className="flex items-center justify-between text-xs font-bold text-slate-700">
                  <span>PICK 5 SEQUENCE</span>
                  <span className="px-2 py-0.5 rounded bg-emerald-100 text-[#065f46] text-[10px] font-black">
                    {analytics.multi_race_tracker?.pick_5?.hit_rate}% HIT
                  </span>
                </div>
                <div className="text-xl font-black text-[#003366]">
                  {analytics.multi_race_tracker?.pick_5?.hits} / {analytics.multi_race_tracker?.pick_5?.attempted} <span className="text-xs text-slate-500 font-normal">Hits</span>
                </div>
                <p className="text-[11px] text-slate-500">2 Contenders per Leg (32 Combos)</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
                <div className="flex items-center justify-between text-xs font-bold text-slate-700">
                  <span>PICK 6 SEQUENCE</span>
                  <span className="px-2 py-0.5 rounded bg-emerald-100 text-[#065f46] text-[10px] font-black">
                    {analytics.multi_race_tracker?.pick_6?.hit_rate}% HIT
                  </span>
                </div>
                <div className="text-xl font-black text-[#003366]">
                  {analytics.multi_race_tracker?.pick_6?.hits} / {analytics.multi_race_tracker?.pick_6?.attempted} <span className="text-xs text-slate-500 font-normal">Hits</span>
                </div>
                <p className="text-[11px] text-slate-500">2 Contenders per Leg (64 Combos)</p>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
