import React, { useState, useEffect } from 'react';
import PinGate from './components/PinGate';
import Header from './components/Header';
import RaceNavigator from './components/RaceNavigator';
import RaceCard from './components/RaceCard';
import ExoticsCard from './components/ExoticsCard';
import { RefreshCw, AlertCircle } from 'lucide-react';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [meetings, setMeetings] = useState([]);
  const [activeMeeting, setActiveMeeting] = useState(null);
  const [meetingData, setMeetingData] = useState(null);
  const [activeRaceIndex, setActiveRaceIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('exacta_auth_token');
    if (token) {
      setIsAuthenticated(true);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      loadMeetings();
    }
  }, [isAuthenticated]);

  const loadMeetings = async () => {
    setLoading(true);
    setError('');
    try {
      let res = await fetch('/api/meetings');
      if (!res.ok) {
        res = await fetch('/api/meetings.json');
      }
      let data = await res.json();
      if (data.status === 'success' && data.meetings.length > 0) {
        setMeetings(data.meetings);
        // Default to first published meeting from docs/meetings if available
        const publishedMeetings = data.meetings.filter(m => m.is_published);
        const defaultMeeting = publishedMeetings.length > 0 ? publishedMeetings[0] : data.meetings[0];
        setActiveMeeting(defaultMeeting);
        loadMeetingDetails(defaultMeeting.filename);
      } else {
        setError('No handicapping meetings found.');
      }
    } catch (e) {
      try {
        const fallbackRes = await fetch('/api/meetings.json');
        const fallbackData = await fallbackRes.json();
        if (fallbackData.status === 'success' && fallbackData.meetings.length > 0) {
          setMeetings(fallbackData.meetings);
          const publishedMeetings = fallbackData.meetings.filter(m => m.is_published);
          const defaultMeeting = publishedMeetings.length > 0 ? publishedMeetings[0] : fallbackData.meetings[0];
          setActiveMeeting(defaultMeeting);
          loadMeetingDetails(defaultMeeting.filename);
          return;
        }
      } catch (err) {}
      setError('Unable to connect to backend server or load static cards.');
    } finally {
      setLoading(false);
    }
  };

  const loadMeetingDetails = async (filename) => {
    setLoading(true);
    try {
      let res = await fetch(`/api/output/${filename}`);
      if (!res.ok) {
        res = await fetch(`/api/output/${filename}`);
      }
      let data = await res.json();
      if (data.status === 'success') {
        setMeetingData(data.data);
        setActiveRaceIndex(0);
      } else if (data.races || data.meta) {
        // Direct static JSON payload
        setMeetingData(data);
        setActiveRaceIndex(0);
      } else {
        setError(data.error || 'Failed to parse meeting data.');
      }
    } catch (e) {
      setError('Failed to fetch race details.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectMeeting = (m) => {
    setActiveMeeting(m);
    loadMeetingDetails(m.filename);
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

      {/* Race Tab Switcher */}
      {meetingData?.races && (
        <RaceNavigator
          races={meetingData.races}
          activeRaceIndex={activeRaceIndex}
          onSelectRace={(idx) => setActiveRaceIndex(idx)}
        />
      )}

      {/* Main Body Content (Screen View) */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6 print:hidden">
        {loading ? (
          <div className="py-24 text-center space-y-3 font-mono">
            <RefreshCw className="w-8 h-8 text-emerald-600 animate-spin mx-auto" />
            <p className="text-sm text-slate-600 font-bold">
              LOADING HANDICAPPING RACE CARDS...
            </p>
          </div>
        ) : error ? (
          <div className="max-w-md mx-auto p-6 rounded-2xl bg-white border border-rose-200 text-center space-y-3 font-mono shadow-sm">
            <AlertCircle className="w-8 h-8 text-rose-600 mx-auto" />
            <p className="text-sm font-bold text-rose-900">{error}</p>
            <button
              onClick={loadMeetings}
              className="px-4 py-2 rounded-xl bg-slate-900 text-xs text-white font-bold hover:bg-slate-800"
            >
              RETRY CONNECTION
            </button>
          </div>
        ) : activeRaceIndex === 'EXOTICS' ? (
          <ExoticsCard
            exoticTickets={meetingData?.exotic_tickets}
            dailyDoubles={meetingData?.daily_double_plays}
          />
        ) : (
          <RaceCard
            race={currentRace}
            trackName={activeMeeting?.track}
            dateStr={activeMeeting?.date}
          />
        )}
      </main>

      {/* Full Card Print View (Rendered only on Print for PDF Output) */}
      {meetingData && (
        <div className="hidden print:block max-w-none w-full p-4 bg-white text-black font-sans">
          {/* Print all races sequentially */}
          {allRaces.map((r, i) => (
            <RaceCard
              key={i}
              race={r}
              trackName={activeMeeting?.track}
              dateStr={activeMeeting?.date}
              isPrintAllMode={true}
            />
          ))}

          {/* Print Exotics & Multi-Race Plays Sheet at the end */}
          <div className="mt-8 pt-4 border-t-2 border-slate-900">
            <ExoticsCard
              exoticTickets={meetingData.exotic_tickets}
              dailyDoubles={meetingData.daily_double_plays}
            />
          </div>
        </div>
      )}
    </div>
  );
}
