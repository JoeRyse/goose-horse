import React, { useState, useEffect } from 'react';
import PinGate from './components/PinGate';
import Header from './components/Header';
import RaceNavigator from './components/RaceNavigator';
import RaceCard from './components/RaceCard';
import ExoticsCard from './components/ExoticsCard';
import { RefreshCw, AlertCircle, ShieldCheck } from 'lucide-react';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [meetings, setMeetings] = useState([]);
  const [activeMeeting, setActiveMeeting] = useState(null);
  const [meetingData, setMeetingData] = useState(null);
  const [activeRaceIndex, setActiveRaceIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = sessionStorage.getItem('exacta_auth_token');
    if (token) {
      setIsAuthenticated(true);
    } else {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      loadMeetings();
    }
  }, [isAuthenticated]);

  const fetchJsonSafely = async (url) => {
    const res = await fetch(url, { cache: 'no-cache' });
    const contentType = res.headers.get('content-type') || '';
    if (!res.ok || (contentType && !contentType.includes('json') && !contentType.includes('javascript') && !contentType.includes('text'))) {
      throw new Error(`Non-JSON response from ${url}`);
    }
    const text = await res.text();
    try {
      return JSON.parse(text);
    } catch (e) {
      throw new Error(`JSON parse error on ${url}`);
    }
  };

  const loadMeetings = async () => {
    setLoading(true);
    setError('');
    try {
      let data = null;
      try {
        data = await fetchJsonSafely('/api/meetings');
      } catch (e) {
        data = await fetchJsonSafely('/api/meetings.json');
      }

      if (data && data.status === 'success' && data.meetings && data.meetings.length > 0) {
        setMeetings(data.meetings);
        const publishedMeetings = data.meetings.filter((m) => m.is_published);
        const defaultMeeting = publishedMeetings.length > 0 ? publishedMeetings[0] : data.meetings[0];
        setActiveMeeting(defaultMeeting);
        await loadMeetingDetails(defaultMeeting.filename);
      } else {
        setError('No handicapping meetings found.');
      }
    } catch (e) {
      try {
        const fallbackData = await fetchJsonSafely('/api/meetings.json');
        if (fallbackData && fallbackData.status === 'success' && fallbackData.meetings && fallbackData.meetings.length > 0) {
          setMeetings(fallbackData.meetings);
          const publishedMeetings = fallbackData.meetings.filter((m) => m.is_published);
          const defaultMeeting = publishedMeetings.length > 0 ? publishedMeetings[0] : fallbackData.meetings[0];
          setActiveMeeting(defaultMeeting);
          await loadMeetingDetails(defaultMeeting.filename);
          return;
        }
      } catch (err) {}
      setError('Unable to load meeting list. Click Clear Cache below to reset.');
    } finally {
      setLoading(false);
    }
  };

  const enrichMeetingRaces = (rawMeetingData) => {
    if (!rawMeetingData || !rawMeetingData.races) return rawMeetingData;
    const enrichedRaces = rawMeetingData.races.map((race) => {
      const contenders = race.all_contenders || race.selections || [];
      let gap = race.rating_gap || 0;
      let hasSoloLock = race.has_solo_lock || false;
      let hasBestBet = race.has_best_bet || false;

      if (contenders.length >= 2) {
        const r1 = parseFloat(contenders[0].rating) || parseFloat(contenders[0].features?.ai_holistic_score) || 0;
        const r2 = parseFloat(contenders[1].rating) || parseFloat(contenders[1].features?.ai_holistic_score) || 0;
        gap = r1 - r2;

        if (r1 >= 88.0 && gap >= 5.0) {
          hasSoloLock = true;
          hasBestBet = true;
          contenders[0].is_solo_lock = true;
        } else if (gap >= 3.0) {
          hasBestBet = true;
          contenders[0].is_best_bet = true;
        }
      }

      return {
        ...race,
        rating_gap: gap,
        has_solo_lock: hasSoloLock,
        has_best_bet: hasBestBet,
        all_contenders: contenders,
      };
    });

    return {
      ...rawMeetingData,
      races: enrichedRaces,
    };
  };

  const loadMeetingDetails = async (filename) => {
    setLoading(true);
    try {
      let data = null;
      try {
        data = await fetchJsonSafely(`/api/output/${filename}`);
      } catch (e) {
        data = await fetchJsonSafely(`/api/output/${filename}`);
      }

      if (data.status === 'success' && data.data) {
        setMeetingData(enrichMeetingRaces(data.data));
        setActiveRaceIndex(0);
      } else if (data.races || data.meta) {
        setMeetingData(enrichMeetingRaces(data));
        setActiveRaceIndex(0);
      } else {
        setError(data.error || 'Failed to parse meeting data.');
      }
    } catch (e) {
      setError('Failed to fetch race details for this track.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectMeeting = (m) => {
    setActiveMeeting(m);
    loadMeetingDetails(m.filename);
  };

  const handleResetStorage = () => {
    localStorage.clear();
    sessionStorage.clear();
    window.location.reload();
  };

  if (!isAuthenticated) {
    return <PinGate onAuthenticated={() => setIsAuthenticated(true)} />;
  }

  const currentRace = activeRaceIndex !== 'EXOTICS' ? (meetingData?.races?.[activeRaceIndex] || null) : null;
  const allRaces = meetingData?.races || [];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      {/* Header Bar */}
      <Header
        activeMeeting={activeMeeting}
        meetings={meetings}
        onSelectMeeting={handleSelectMeeting}
      />

      {/* Sticky Race Navigation Bar */}
      {meetingData && (
        <RaceNavigator
          races={allRaces}
          activeRaceIndex={activeRaceIndex}
          onSelectRace={(idx) => setActiveRaceIndex(idx)}
        />
      )}

      {/* Main Content Body (Screen View) */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6 print:hidden">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-24 space-y-4 font-mono">
            <RefreshCw className="w-8 h-8 text-[#10b981] animate-spin" />
            <div className="text-center">
              <h3 className="text-sm font-bold text-slate-900">LOADING RACE CARDS...</h3>
              <p className="text-xs text-slate-500 mt-1">Retrieving AI handicapping analysis</p>
            </div>
          </div>
        ) : error ? (
          <div className="max-w-md mx-auto py-12 text-center font-mono space-y-4">
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl text-rose-900 text-xs font-bold flex flex-col items-center gap-2">
              <AlertCircle className="w-6 h-6 text-rose-600" />
              <span>{error}</span>
            </div>
            <button
              onClick={handleResetStorage}
              className="px-4 py-2 bg-[#003366] text-white text-xs font-bold rounded-xl shadow-md hover:bg-blue-900"
            >
              🔄 CLEAR LOCAL CACHE & REFRESH
            </button>
          </div>
        ) : activeRaceIndex === 'EXOTICS' ? (
          <ExoticsCard
            exoticTickets={meetingData?.exotic_tickets}
            dailyDoubles={meetingData?.daily_doubles}
          />
        ) : (
          <RaceCard
            race={currentRace}
            trackName={activeMeeting?.track}
            dateStr={activeMeeting?.date}
          />
        )}
      </main>

      {/* PRINT-ONLY FULL CARD CONTAINER (Prints Entire Card: All Races + Exotics Sheet) */}
      {!loading && !error && meetingData && (
        <div className="hidden print:block w-full text-black space-y-6">
          {/* Track Header Line */}
          <div className="border-b-4 border-black pb-2 mb-4">
            <h1 className="text-xl font-black uppercase font-mono tracking-tight">
              {activeMeeting?.track || 'RACETRACK'} — FULL DAILY RACING PROGRAM
            </h1>
            <div className="text-xs font-mono font-bold flex justify-between mt-1">
              <span>DATE: {activeMeeting?.date}</span>
              <span>TRACK CONDITION: {activeMeeting?.track_condition || 'Standard'}</span>
              <span>TOTAL RACES: {allRaces.length}</span>
            </div>
          </div>

          {/* Render All Races Sequentially */}
          {allRaces.map((raceObj, rIdx) => (
            <RaceCard
              key={rIdx}
              race={raceObj}
              trackName={activeMeeting?.track}
              dateStr={activeMeeting?.date}
              isPrintAllMode={true}
            />
          ))}

          {/* Render Multi-Race & Exotics Sheet */}
          <div className="pt-4 border-t-2 border-black">
            <ExoticsCard
              exoticTickets={meetingData?.exotic_tickets}
              dailyDoubles={meetingData?.daily_doubles}
            />
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 px-4 text-center font-mono text-xs text-slate-500 print:hidden flex items-center justify-center justify-between max-w-7xl mx-auto w-full">
        <div>
          EXACTA AI • Professional Sportsbook Handicapping Protocol
        </div>
        <button
          onClick={handleResetStorage}
          className="text-[11px] font-semibold text-slate-400 hover:text-slate-700 underline"
        >
          Reset Session Cache
        </button>
      </footer>
    </div>
  );
}
