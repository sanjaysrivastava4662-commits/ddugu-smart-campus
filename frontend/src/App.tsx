import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { BrowserRouter as Router, Link, Navigate, Route, Routes } from 'react-router-dom';
import axios from 'axios';
import { Activity, AlertCircle, BookOpen, Building2, CalendarDays, CheckCircle, GraduationCap, KeyRound, LayoutGrid, LogOut, MapPinned, ShieldCheck, UserRound, Users, Clock3, DoorOpen, Bell, Search, MoveRight, Radio, Sparkles } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';

const API = axios.create({ baseURL: '/api' });

const roleMeta = {
  admin: { label: 'Administrator', accent: 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/20' },
  faculty: { label: 'Faculty', accent: 'bg-sky-500/15 text-sky-300 border border-sky-500/20' },
  student: { label: 'Student', accent: 'bg-violet-500/15 text-violet-300 border border-violet-500/20' },
};

type User = {
  id: number;
  name: string;
  email: string;
  role: 'admin' | 'faculty' | 'student';
  branch?: string;
  year?: number;
  section?: string;
  roll_number?: string;
};

type DashboardData = {
  role: string;
  summary: Record<string, number | string>;
  timetable?: any[];
  exams?: any[];
  announcements?: any[];
  library_passes?: any[];
  rooms?: any[];
  requests?: any[];
  reports?: any[];
};

type WorkspaceTab = 'Overview' | 'Timetable' | 'Rooms' | 'Room Assistant' | 'Requests' | 'Exams' | 'Announcements' | 'Campus Explorer' | 'Library Passes' | 'Reports' | 'Users' | 'Audit history';

const getToken = () => localStorage.getItem('ddugu_token');
const saveToken = (token: string) => localStorage.setItem('ddugu_token', token);
const clearToken = () => localStorage.removeItem('ddugu_token');

const authHeaders = () => ({
  Authorization: `Bearer ${getToken()}`,
});

const statusTone = (status: string) => {
  if (status === 'approved') return 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30';
  if (status === 'rejected') return 'bg-red-500/10 text-red-300 border border-red-500/30';
  return 'bg-yellow-500/10 text-yellow-300 border border-yellow-500/30';
};

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/dashboard" element={<ProtectedDashboard />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

function LandingPage() {
  const isLoggedIn = !!getToken();
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  useEffect(() => {
    let active = true;
    const checkApi = async () => {
      try {
        await API.get('/health', { timeout: 5000 });
        if (active) setApiStatus('online');
      } catch {
        if (active) setApiStatus('offline');
      }
    };

    checkApi();
    const interval = window.setInterval(checkApi, 15000);
    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  const statusLabel = {
    checking: 'Checking…',
    online: 'System online',
    offline: 'API unavailable',
  }[apiStatus];
  const statusClass = apiStatus === 'online'
    ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
    : apiStatus === 'offline'
      ? 'border-red-500/30 bg-red-500/10 text-red-300'
      : 'border-slate-500/30 bg-slate-500/10 text-slate-300';

  return (
    <div className="app-page landing-page min-h-screen bg-slate-950 text-slate-100">
      <nav className="landing-nav mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
        <div className="flex items-center gap-3">
          <div className="brand-mark rounded-xl bg-sky-500/15 p-2 text-sky-300"><Building2 size={22} /></div>
          <div>
            <h1 className="text-lg font-bold">DDUGU Smart Campus</h1>
            <p className="text-xs uppercase tracking-[0.18em] text-slate-400">Campus intelligence system</p>
          </div>
        </div>
        <div className="flex gap-3">
          {isLoggedIn ? (
            <Link to="/dashboard" className="primary-link rounded-lg border border-sky-500/30 bg-sky-500/10 px-4 py-2 text-sm font-medium text-sky-200">Open Dashboard <MoveRight size={15} /></Link>
          ) : (
            <Link to="/login" className="primary-link rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-medium">Access portal <MoveRight size={15} /></Link>
          )}
        </div>
      </nav>

      <main className="landing-main mx-auto max-w-7xl px-6 pb-16 pt-8">
        <section className="landing-hero grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
          <div>
            <div className="eyebrow mb-4 inline-flex items-center gap-2 rounded-full border border-violet-500/20 bg-violet-500/10 px-3 py-1 text-xs font-medium text-violet-200">
              <Sparkles size={14} /> DIGITAL CAMPUS · DDUGU IET
            </div>
            <h2 className="hero-title max-w-xl text-5xl font-extrabold leading-tight tracking-tight text-white">A smarter campus. <span>In sync.</span></h2>
            <p className="mt-5 max-w-xl text-lg text-slate-300">A complete demo application helping students, faculty, and administrators manage room bookings, timetables, exams, and academic announcements in a single campus system.</p>
            <div className="mt-8 flex flex-wrap gap-4">
              <Link to="/login" className="hero-cta rounded-xl bg-sky-500 px-5 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-sky-500/20">Enter campus <MoveRight size={17} /></Link>
              <a href="#features" className="rounded-xl border border-slate-700 bg-slate-900 px-5 py-3 text-sm font-semibold text-slate-200">Explore Features</a>
            </div>
            <div className="mt-10 grid gap-4 sm:grid-cols-3">
              {[
                ['30+ Rooms', 'Across IET and Deeksha Bhawan'],
                ['3 roles', 'Student, Faculty, Admin'],
                ['Real workflows', 'Inline bookings and exam allocation'],
              ].map(([title, text]) => (
                <div key={title} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 backdrop-blur-sm">
                  <div className="text-xl font-bold text-white">{title}</div>
                  <div className="mt-1 text-sm text-slate-400">{text}</div>
                </div>
              ))}
            </div>
          </div>
          <div className="system-panel rounded-3xl border border-slate-800 bg-slate-900/80 p-6 shadow-2xl shadow-slate-950/40">
            <div className="mb-4 flex items-center justify-between">
              <div><p className="panel-kicker">SYSTEM OVERVIEW</p><h3 className="text-xl font-semibold text-white">Campus telemetry</h3></div>
              <span className={`status-pill rounded-full border px-2 py-1 text-xs ${statusClass}`}><Radio size={12} />{statusLabel}</span>
            </div>
            <div className="space-y-4">
              {[
                { label: 'Building coverage', value: 'IET + Deeksha Bhawan', icon: Building2 },
                { label: 'Academic schedule engine', value: 'Conflict checks enabled', icon: CalendarDays },
                { label: 'Exam release system', value: '1-hour student visibility window', icon: CheckCircle },
                { label: 'AI assistant', value: 'Room finder for faculty/admin', icon: Search },
              ].map(({ label, value, icon: Icon }) => (
                <div key={label} className="flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-950/60 p-3">
                  <div className="flex items-center gap-3"><div className="rounded-lg bg-sky-500/10 p-2 text-sky-300"><Icon size={16} /></div><span className="text-sm text-slate-300">{label}</span></div>
                  <span className="text-xs text-slate-200">{value}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="features" className="mt-20 grid gap-6 md:grid-cols-3">
          {[
            ['Classroom Management', 'Search vacant rooms, handle overlapping requests, and coordinate academic usage across both buildings.'],
            ['Examination Workflow', 'Create exams, allocate seats, and release room details only at the correct time.'],
            ['Announcements & Passes', 'Publish notices, issue library passes, and help students track official information.'],
          ].map(([title, text]) => (
            <div key={title} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
              <div className="mb-3 inline-flex rounded-xl bg-sky-500/10 p-2 text-sky-300"><Activity size={18} /></div>
              <h3 className="text-xl font-semibold text-white">{title}</h3>
              <p className="mt-2 text-sm text-slate-400">{text}</p>
            </div>
          ))}
        </section>
      </main>
    </div>
  );
}

function LoginPage() {
  const [email, setEmail] = useState('admin@ddugu.ac.in');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { data } = await API.post('/auth/login', { email, password });
      saveToken(data.access_token);
      window.location.href = '/dashboard';
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page flex min-h-screen items-center justify-center bg-slate-950 px-4">
      <div className="auth-card w-full max-w-md rounded-3xl border border-slate-800 bg-slate-900/80 p-8 shadow-2xl shadow-slate-950/50">
        <Link to="/" className="auth-home"><Building2 size={17} /> DDUGU CAMPUS <span>·</span> RETURN HOME</Link>
        <div className="mb-6 flex items-center justify-between">
          <div>
            <p className="text-sm text-sky-300">Access portal</p>
            <h2 className="text-2xl font-bold text-white">Secure sign in</h2>
          </div>
          <div className="brand-mark rounded-xl bg-sky-500/10 p-3 text-sky-300"><KeyRound size={18} /></div>
        </div>
        <form onSubmit={handleLogin} className="space-y-5">
          <div>
            <label className="mb-2 block text-sm text-slate-300">Email</label>
            <input value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-xl border border-slate-700 bg-slate-950/70 px-3 py-2.5 text-white outline-none ring-0 placeholder:text-slate-500" placeholder="admin@ddugu.ac.in" />
          </div>
          <div>
            <label className="mb-2 block text-sm text-slate-300">Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full rounded-xl border border-slate-700 bg-slate-950/70 px-3 py-2.5 text-white outline-none ring-0 placeholder:text-slate-500" placeholder="••••••••" />
          </div>
          {error && <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-200">{error}</div>}
          <button disabled={loading} type="submit" className="w-full rounded-xl bg-sky-500 px-4 py-3 font-semibold text-slate-950 transition hover:bg-sky-400 disabled:opacity-60">{loading ? 'Signing in...' : 'Login'}</button>
        </form>
        <div className="mt-5 rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-xs text-slate-400">
          Demo accounts: <span className="text-slate-200">admin@ddugu.ac.in / admin123</span>, <span className="text-slate-200">faculty@ddugu.ac.in / faculty123</span>, <span className="text-slate-200">student@ddugu.ac.in / student123</span>
        </div>
      </div>
    </div>
  );
}

function ProtectedDashboard() {
  const [user, setUser] = useState<User | null>(null);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<WorkspaceTab>('Overview');
  const [refreshVersion, setRefreshVersion] = useState(0);
  const [loadError, setLoadError] = useState('');
  const [sessionExpired, setSessionExpired] = useState(false);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setLoadError('');
      const token = getToken();
      if (!token) {
        setSessionExpired(true);
        setLoading(false);
        return;
      }
      try {
        const [{ data: userData }, { data: dashData }] = await Promise.all([
          API.get('/me', { headers: authHeaders() }),
          API.get('/dashboard', { headers: authHeaders() }),
        ]);
        setUser(userData);
        setDashboard(dashData);
        setSessionExpired(false);
      } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 401) {
          clearToken();
          setSessionExpired(true);
        } else {
          const detail = axios.isAxiosError(error) ? error.response?.data?.detail : null;
          setLoadError(typeof detail === 'string' ? detail : 'Could not load the dashboard. Check your connection and try again.');
        }
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [refreshVersion]);

  const handleLogout = () => {
    clearToken();
    window.location.href = '/login';
  };
  const refreshDashboard = useCallback(() => {
    setRefreshVersion((version) => version + 1);
  }, []);

  const tabs: { label: WorkspaceTab; icon: typeof LayoutGrid }[] = [
    { label: 'Overview', icon: LayoutGrid },
    { label: 'Timetable', icon: CalendarDays },
    { label: 'Rooms', icon: Building2 },
    ...(user?.role === 'faculty' ? [{ label: 'Room Assistant' as const, icon: Search }, { label: 'Requests' as const, icon: Clock3 }] : []),
    { label: 'Exams', icon: BookOpen },
    { label: 'Announcements', icon: Bell },
    { label: 'Campus Explorer', icon: MapPinned },
    ...(user?.role !== 'faculty' ? [{ label: 'Library Passes' as const, icon: KeyRound }] : []),
    ...(user?.role === 'student' ? [{ label: 'Reports' as const, icon: AlertCircle }] : []),
    ...(user?.role === 'admin' ? [{ label: 'Requests' as const, icon: Clock3 }, { label: 'Reports' as const, icon: AlertCircle }] : []),
    ...(user?.role === 'admin' ? [{ label: 'Users' as const, icon: Users }] : []),
    ...(user?.role === 'admin' ? [{ label: 'Audit history' as const, icon: ShieldCheck }] : []),
  ];

  if (loading) {
    return <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-200">Loading dashboard...</div>;
  }

  if (sessionExpired) {
    return <Navigate to="/login" replace />;
  }

  if (loadError) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 text-slate-100">
        <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <h1 className="text-xl font-semibold">Dashboard unavailable</h1>
          <p className="mt-2 text-sm text-red-200">{loadError}</p>
          <button onClick={refreshDashboard} className="mt-5 rounded-xl bg-sky-500 px-4 py-2.5 text-sm font-semibold text-slate-950">Retry</button>
        </div>
      </div>
    );
  }

  if (!user || !dashboard) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="app-page dashboard-page min-h-screen bg-slate-950 text-slate-100">
      <aside className="app-sidebar fixed inset-y-0 left-0 w-72 border-r border-slate-800 bg-slate-900/90 p-5 backdrop-blur-xl">
        <div className="flex items-center gap-3 border-b border-slate-800 pb-5">
          <div className="brand-mark rounded-xl bg-sky-500/10 p-2 text-sky-300"><GraduationCap size={20} /></div>
          <div>
            <div className="font-bold text-white">DDUGU Smart Campus</div>
            <div className="text-xs text-slate-400">{roleMeta[user.role].label}</div>
          </div>
        </div>

        <nav className="app-nav mt-6 space-y-2 text-sm text-slate-300">
          {tabs.map(({ label, icon: Icon }) => (
            <button key={label} onClick={() => setActiveTab(label)} className={`app-nav-link flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left ${activeTab === label ? 'is-active bg-sky-500/10 text-sky-200' : 'hover:bg-slate-800/80'}`}><Icon size={16} />{label}</button>
          ))}
        </nav>

        <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-950/50 p-4">
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-slate-800 p-2"><UserRound size={18} /></div>
            <div>
              <div className="font-medium text-white">{user.name}</div>
              <div className="text-xs text-slate-400">{user.email}</div>
            </div>
          </div>
          <div className={`mt-4 inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${roleMeta[user.role].accent}`}>{roleMeta[user.role].label}</div>
        </div>

        <button onClick={handleLogout} className="mt-8 flex w-full items-center justify-center gap-2 rounded-xl border border-red-500/20 bg-red-500/10 px-3 py-2.5 text-sm font-medium text-red-200"><LogOut size={16} /> Logout</button>
      </aside>

      <main className="app-main ml-72 p-8">
        <header className="app-header mb-8 flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-sky-300">Campus portal</p>
            <h1 className="mt-1 text-3xl font-bold text-white">Welcome back, {user.name.split(' ')[0]}</h1>
          </div>
          <div className={`rounded-full border px-3 py-1.5 text-sm font-medium ${roleMeta[user.role].accent}`}>{roleMeta[user.role].label}</div>
        </header>

        {activeTab === 'Overview' ? (
          <>
            <OverviewCards dashboard={dashboard} user={user} />
            <div className="mt-8 grid gap-6 lg:grid-cols-[1.5fr_1fr]">
              <section className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-xl font-semibold text-white">{user.role === 'student' ? 'My timetable' : user.role === 'faculty' ? 'Faculty timetable' : 'Campus summary'}</h3>
                  <div className="flex items-center gap-2 rounded-full border border-slate-700 bg-slate-950/60 px-2 py-1 text-xs text-slate-300"><CalendarDays size={14} /> Updated</div>
                </div>
                <div className="space-y-3">
                  {(dashboard.timetable || dashboard.requests || []).slice(0, 5).map((item: any, index: number) => (
                    <div key={item.id || index} className="flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-950/60 p-3">
                      <div>
                        <div className="font-medium text-white">{item.title || item.purpose || item.subject || 'Academic update'}</div>
                        <div className="mt-1 text-sm text-slate-400">{item.day || item.room_code || item.faculty_name || item.message || 'Operational detail'}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-sky-300">{item.start_time || item.requested_date || item.created_at || 'N/A'}</div>
                        <div className={`mt-2 inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold ${statusTone(item.status || 'approved')}`}>{(item.status || 'approved').toUpperCase()}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
              <section className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5">
                <div className="mb-4 flex items-center justify-between"><h3 className="text-xl font-semibold text-white">Quick actions</h3><AlertCircle size={18} className="text-sky-300" /></div>
                <div className="space-y-3">
                  {user.role === 'student' && <><ActionCard title="View exam schedule" text="Check room, floor, and seat allocation." icon={BookOpen} /><ActionCard title="Library pass" text="Confirm your active campus pass." icon={KeyRound} /></>}
                  {user.role === 'faculty' && <><ActionCard title="Request vacant room" text="Submit extra class or practical booking." icon={Search} /><ActionCard title="Track requests" text="Monitor pending and approved room requests." icon={Clock3} /></>}
                  {user.role === 'admin' && <><ActionCard title="Approve requests" text="Review faculty booking submissions." icon={CheckCircle} /><ActionCard title="Manage campus" text="Allocate rooms, exams, and announcements." icon={ShieldCheck} /></>}
                </div>
              </section>
            </div>
            <div className="mt-8 grid gap-6 xl:grid-cols-3">
              <SummaryPanel title="Announcements" items={dashboard.announcements || []} />
              <SummaryPanel title="Rooms" items={(dashboard.rooms || []).slice(0, 4)} />
              <SummaryPanel title="Library / Passes" items={(dashboard.library_passes || []).slice(0, 4)} />
            </div>
          </>
        ) : (
          <RoleWorkspace
            tab={activeTab}
            user={user}
            dashboard={dashboard}
            onRefresh={refreshDashboard}
          />
        )}
      </main>
    </div>
  );
}

function RoleWorkspace({
  tab,
  user,
  dashboard,
  onRefresh,
}: {
  tab: WorkspaceTab;
  user: User;
  dashboard: DashboardData;
  onRefresh: () => void;
}) {
  const [records, setRecords] = useState<any[]>([]);
  const [rooms, setRooms] = useState<any[]>(dashboard.rooms || []);
  const [buildings, setBuildings] = useState<any[]>([]);
  const [students, setStudents] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [availableRooms, setAvailableRooms] = useState<any[] | null>(null);
  const [assistantResults, setAssistantResults] = useState<any[]>([]);
  const [allocationReport, setAllocationReport] = useState<any | null>(null);

  const headers = authHeaders();
  const loadWorkspace = async () => {
    setLoading(true);
    setError('');
    try {
      if (tab === 'Rooms' || tab === 'Exams') {
        const { data } = await API.get('/rooms', { headers });
        setRooms(data);
        if (tab === 'Rooms') {
          const { data: buildingData } = await API.get('/buildings', { headers });
          setBuildings(buildingData);
        }
      }
      if (tab === 'Timetable') {
        const { data } = await API.get('/timetable', { headers });
        setRecords(data);
        if (user.role === 'admin') {
          const [roomResponse, facultyResponse] = await Promise.all([
            API.get('/rooms', { headers }),
            API.get('/admin/users?role=faculty', { headers }),
          ]);
          setRooms(roomResponse.data);
          setStudents(facultyResponse.data);
        }
      } else if (tab === 'Requests') {
        const { data } = await API.get('/faculty-requests', { headers });
        setRecords(data);
      } else if (tab === 'Exams') {
        const { data } = await API.get('/exams', { headers });
        setRecords(data);
      } else if (tab === 'Announcements') {
        const { data } = await API.get('/announcements', { headers });
        setRecords(data);
      } else if (tab === 'Campus Explorer') {
        const { data } = await API.get('/buildings', { headers });
        setBuildings(data);
      } else if (tab === 'Library Passes') {
        const { data } = await API.get('/library-passes', { headers });
        setRecords(data);
        if (user.role === 'admin') {
          const users = await API.get('/admin/users?role=student', { headers });
          setStudents(users.data);
        }
      } else if (tab === 'Reports' && user.role === 'admin') {
        const { data } = await API.get('/admin/reports', { headers });
        setRecords(data);
      } else if (tab === 'Reports') {
        setRecords(dashboard.reports || []);
      } else if (tab === 'Rooms') {
        setRecords(rooms);
      } else if (tab === 'Users') {
        const { data } = await API.get('/admin/users', { headers });
        setRecords(data);
      } else if (tab === 'Audit history') {
        const { data } = await API.get('/admin/audit', { headers });
        setRecords(data);
      }
    } catch (requestError: any) {
      setError(requestError.response?.data?.detail || 'Could not load this section.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWorkspace();
    // Load once per section change; refreshes are explicitly triggered by workspace actions.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, user.role, dashboard]);

  const runAction = async (action: () => Promise<unknown>, successMessage: string) => {
    setError('');
    setMessage('');
    try {
      await action();
      setMessage(successMessage);
      await loadWorkspace();
      onRefresh();
    } catch (requestError: any) {
      setError(requestError.response?.data?.detail || 'The action could not be completed.');
    }
  };

  const fieldClass = 'w-full rounded-xl border border-slate-700 bg-slate-950/70 px-3 py-2.5 text-sm text-white outline-none';
  const submitClass = 'rounded-xl bg-sky-500 px-4 py-2.5 text-sm font-semibold text-slate-950 hover:bg-sky-400';
  const today = new Date().toLocaleDateString('en-CA');

  const searchAvailableRooms = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setMessage('');
    const form = new FormData(event.currentTarget);
    const params = new URLSearchParams({
      date: String(form.get('date')),
      start_time: String(form.get('start_time')),
      end_time: String(form.get('end_time')),
      min_capacity: String(form.get('min_capacity') || 1),
    });
    if (form.get('building_id')) params.set('building_id', String(form.get('building_id')));
    if (form.get('floor')) params.set('floor', String(form.get('floor')));
    if (form.get('facility')) params.set('facility', String(form.get('facility')));
    try {
      const { data } = await API.get(`/rooms?${params.toString()}`, { headers });
      setAvailableRooms(data);
      if (data.length === 0) setMessage('No rooms meet these availability criteria.');
    } catch (requestError: any) {
      setError(requestError.response?.data?.detail || 'Room availability search failed.');
    }
  };

  const askRoomAssistant = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setError('');
    setMessage('');
    try {
      const { data } = await API.post('/assistant/rooms', { query: form.get('query') }, { headers });
      setAssistantResults(data.recommendations);
      setMessage(data.message);
    } catch (requestError: any) {
      setError(requestError.response?.data?.detail || 'Room assistant could not process that request.');
      setAssistantResults([]);
    }
  };

  const createTimetableEntry = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    await runAction(
      () => API.post('/admin/timetable', {
        title: form.get('title'),
        subject: form.get('subject'),
        day: form.get('day'),
        start_time: form.get('start_time'),
        end_time: form.get('end_time'),
        room_id: Number(form.get('room_id')),
        instructor_id: Number(form.get('instructor_id')),
        branch: form.get('branch'),
        year: Number(form.get('year')),
        section: form.get('section'),
        batch: form.get('batch') || null,
      }, { headers }),
      'Official timetable entry created.',
    );
    formElement.reset();
  };

  const submitFacultyRequest = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    await runAction(
      () => API.post('/faculty-requests', {
        room_id: Number(form.get('room_id')),
        requested_date: form.get('date'),
        start_time: form.get('start_time'),
        end_time: form.get('end_time'),
        subject: form.get('subject'),
        purpose: form.get('purpose'),
        branch: form.get('branch'),
        year: Number(form.get('year')),
        section: form.get('section'),
        batch: form.get('batch') || null,
        expected_attendance: Number(form.get('expected_attendance')),
        required_facilities: form.get('required_facilities') || null,
        notes: form.get('notes'),
      }, { headers }),
      'Room request submitted for administrator review.',
    );
    formElement.reset();
  };

  const createAnnouncement = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    await runAction(
      () => API.post('/admin/announcements', {
        title: form.get('title'),
        message: form.get('message'),
        audience: form.get('audience'),
      }, { headers }),
      'Announcement published.',
    );
    formElement.reset();
  };

  const createReport = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    await runAction(
      () => API.post('/student/reports', {
        category: form.get('category'),
        details: form.get('details'),
      }, { headers }),
      'Your report has been sent to the campus administrator.',
    );
    formElement.reset();
  };

  const createExam = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    await runAction(
      () => API.post('/admin/exams', {
        title: form.get('title'),
        subject: form.get('subject'),
        exam_date: form.get('exam_date'),
        start_time: form.get('start_time'),
        end_time: form.get('end_time'),
        reporting_time: form.get('reporting_time') || null,
        room_ids: form.getAll('room_ids').map(Number),
        branch: form.get('branch'),
        year: Number(form.get('year')),
        section: form.get('section'),
        publish: form.get('publish') === 'on',
      }, { headers }),
      'Exam created and seats allocated.',
    );
    formElement.reset();
  };

  const createRoom = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    await runAction(
      () => API.post('/admin/rooms', {
        building_id: Number(form.get('building_id')),
        code: form.get('code'),
        room_type: form.get('room_type'),
        floor: form.get('floor'),
        capacity: Number(form.get('capacity')),
        facilities: form.get('facilities'),
        usage_permission: form.get('usage_permission'),
        examination_suitable: form.get('examination_suitable') === 'on',
      }, { headers }),
      'Room added to the campus directory.',
    );
    formElement.reset();
  };

  const issuePass = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    await runAction(
      () => API.post('/admin/library-passes', {
        student_id: Number(form.get('student_id')),
        expiry_date: form.get('expiry_date'),
      }, { headers }),
      'Library pass issued.',
    );
    formElement.reset();
  };

  const createUser = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const role = String(form.get('role'));
    await runAction(
      () => API.post('/admin/users', {
        name: form.get('name'),
        email: form.get('email'),
        password: form.get('password'),
        role,
        branch: form.get('branch') || null,
        year: form.get('year') ? Number(form.get('year')) : null,
        section: form.get('section') || null,
        roll_number: form.get('roll_number') || null,
        phone: form.get('phone') || null,
      }, { headers }),
      'User account created.',
    );
    formElement.reset();
  };

  const importStudents = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const file = form.get('file');
    if (!(file instanceof File) || file.size === 0) {
      setError('Choose a CSV or XLSX file first.');
      return;
    }
    await runAction(
      () => API.post('/admin/import-students', form, { headers }),
      'Student data imported successfully.',
    );
    formElement.reset();
  };

  const uploadBlueprint = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const buildingId = form.get('building_id');
    const file = form.get('file');
    if (!(file instanceof File) || file.size === 0) {
      setError('Choose a PDF, PNG, or JPEG blueprint.');
      return;
    }
    await runAction(
      () => API.post(`/admin/buildings/${buildingId}/blueprints`, form, { headers }),
      'Blueprint uploaded. The campus map remains a schematic until the university verifies it.',
    );
    formElement.reset();
  };

  const loadExamAllocations = async (examId: number) => {
    setError('');
    try {
      const { data } = await API.get(`/admin/exams/${examId}/allocations`, { headers });
      setAllocationReport(data);
    } catch (requestError: any) {
      setError(requestError.response?.data?.detail || 'Could not load seat allocations.');
    }
  };

  const exportExamAllocations = async (examId: number) => {
    setError('');
    try {
      const { data } = await API.get(`/admin/exams/${examId}/allocations.csv`, { headers, responseType: 'blob' });
      const url = URL.createObjectURL(data);
      const link = document.createElement('a');
      link.href = url;
      link.download = `exam-${examId}-allocations.csv`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (requestError: any) {
      setError(requestError.response?.data?.detail || 'Could not export seat allocations.');
    }
  };

  const validateLibraryPass = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setError('');
    setMessage('');
    try {
      const { data } = await API.post('/library-passes/verify', { pass_code: form.get('pass_code') }, { headers });
      setMessage(data.valid ? `Pass valid for ${data.student_name} through ${data.expiry_date}.` : `Pass is ${data.status}.`);
    } catch (requestError: any) {
      setError(requestError.response?.data?.detail || 'Could not validate this library pass.');
    }
  };

  const panel = (title: string, children: React.ReactNode, subtitle?: string) => (
    <section className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5">
      <div className="mb-5">
        <h2 className="text-xl font-semibold text-white">{title}</h2>
        {subtitle && <p className="mt-1 text-sm text-slate-400">{subtitle}</p>}
      </div>
      {children}
    </section>
  );

  const recordsList = (items: any[], emptyText: string, render: (item: any) => React.ReactNode) => (
    items.length === 0
      ? <div className="rounded-xl border border-dashed border-slate-700 p-4 text-sm text-slate-400">{emptyText}</div>
      : <div className="space-y-3">{items.map((item, index) => <div key={item.id ?? index} className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">{render(item)}</div>)}</div>
  );

  if (loading) return <div className="mt-8 rounded-3xl border border-slate-800 bg-slate-900/80 p-8 text-slate-300">Loading {tab.toLowerCase()}…</div>;

  return (
    <div className="mt-8 space-y-6">
      {error && <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-200">{error}</div>}
      {message && <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-200">{message}</div>}

      {tab === 'Timetable' && (
        <div className="space-y-6">
          {user.role === 'admin' && panel('Create official class', <form onSubmit={createTimetableEntry} className="grid gap-3 sm:grid-cols-2">
            <input name="title" placeholder="Class / subject name" required className={fieldClass} />
            <input name="subject" placeholder="Subject code" required className={fieldClass} />
            <select name="day" className={fieldClass}>{['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'].map((day) => <option key={day}>{day}</option>)}</select>
            <select name="room_id" required className={fieldClass}>{rooms.map((room) => <option key={room.id} value={room.id}>{room.code} · {room.building_name}</option>)}</select>
            <select name="instructor_id" required className={fieldClass}>{students.map((faculty) => <option key={faculty.id} value={faculty.id}>{faculty.name}</option>)}</select>
            <select name="branch" className={fieldClass}>{['CSE', 'AI ML', 'AI DS', 'ECE', 'ME', 'IT'].map((branch) => <option key={branch}>{branch}</option>)}</select>
            <select name="year" className={fieldClass}>{[1, 2, 3, 4].map((year) => <option key={year} value={year}>Year {year}</option>)}</select>
            <input name="section" placeholder="Section" defaultValue="A" required className={fieldClass} />
            <input name="batch" placeholder="Batch (optional)" className={fieldClass} />
            <input name="start_time" type="time" required className={fieldClass} />
            <input name="end_time" type="time" required className={fieldClass} />
            <button className={`${submitClass} sm:col-span-2`}>Add to official timetable</button>
          </form>, 'The server rejects room, instructor, and section time conflicts.')}
          {panel('Academic timetable', recordsList(records, 'No timetable entries found.', (item) => (
            <div className="flex flex-wrap justify-between gap-3">
              <div><div className="font-medium text-white">{item.title} <span className="text-slate-400">· {item.subject}</span></div><div className="mt-1 text-sm text-slate-400">{item.day}, {item.start_time}–{item.end_time} · {item.room_code} · {item.room_name}</div></div>
              <div className="text-sm text-sky-300">{item.instructor || `${item.branch} · Year ${item.year} · ${item.section}`}</div>
            </div>
          )))}
        </div>
      )}

      {tab === 'Room Assistant' && panel('Smart room assistant', <div className="space-y-4">
        <form onSubmit={askRoomAssistant} className="space-y-3">
          <textarea name="query" required minLength={5} rows={3} className={fieldClass} placeholder="Find a classroom for 70 CSE second-year students tomorrow between 11 AM and 1 PM" />
          <button className={submitClass}>Find suitable rooms</button>
        </form>
        {assistantResults.length > 0 && <div className="space-y-3">{assistantResults.map((item, index) => <div key={item.room} className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4"><div className="font-medium text-white">#{index + 1} {item.room} · {item.building}</div><div className="mt-1 text-sm text-slate-400">Floor {item.floor} · {item.capacity} seats · {item.facilities}</div><p className="mt-2 text-sm text-sky-200">{item.explanation}</p></div>)}</div>}
      </div>, 'A local, deterministic assistant parses date, time, capacity, branch/year, building, and facilities, then checks real schedule constraints. It does not book or approve rooms.')}

      {tab === 'Rooms' && (
        <div className="grid gap-6 xl:grid-cols-[1fr_1.2fr]">
          {user.role === 'faculty' && panel('Find a vacant room', <form onSubmit={searchAvailableRooms} className="grid gap-3 sm:grid-cols-2">
            <label className="text-xs text-slate-400">Date<input name="date" type="date" min={today} defaultValue={today} required className={`${fieldClass} mt-1`} /></label>
            <label className="text-xs text-slate-400">Minimum capacity<input name="min_capacity" type="number" min="1" defaultValue="1" className={`${fieldClass} mt-1`} /></label>
            <label className="text-xs text-slate-400">Start<input name="start_time" type="time" required className={`${fieldClass} mt-1`} /></label>
            <label className="text-xs text-slate-400">End<input name="end_time" type="time" required className={`${fieldClass} mt-1`} /></label>
            <label className="text-xs text-slate-400">Building<select name="building_id" className={`${fieldClass} mt-1`}><option value="">All buildings</option>{buildings.map((building) => <option key={building.id} value={building.id}>{building.name}</option>)}</select></label>
            <label className="text-xs text-slate-400">Floor<select name="floor" className={`${fieldClass} mt-1`}><option value="">Any floor</option>{['Ground', '1', '2'].map((floor) => <option key={floor}>{floor}</option>)}</select></label>
            <label className="text-xs text-slate-400 sm:col-span-2">Required facility<input name="facility" placeholder="e.g. Projector" className={`${fieldClass} mt-1`} /></label>
            <button className={`${submitClass} sm:col-span-2`}>Search availability</button>
          </form>, 'The search checks published classes, exams, and approved room requests.')}
          {user.role === 'faculty' && panel('Request a room', <form onSubmit={submitFacultyRequest} className="grid gap-3">
            <label className="text-xs text-slate-400">Available room<select name="room_id" required className={`${fieldClass} mt-1`}>
              {(availableRooms ?? rooms).map((room) => <option key={room.id} value={room.id}>{room.code} · {room.building_name} · capacity {room.capacity}</option>)}
            </select></label>
            <input name="subject" placeholder="Subject / class name" required className={fieldClass} />
            <label className="text-xs text-slate-400">Date<input name="date" type="date" min={today} defaultValue={today} required className={`${fieldClass} mt-1`} /></label>
            <div className="grid grid-cols-2 gap-3">
              <label className="text-xs text-slate-400">Start<input name="start_time" type="time" required className={`${fieldClass} mt-1`} /></label>
              <label className="text-xs text-slate-400">End<input name="end_time" type="time" required className={`${fieldClass} mt-1`} /></label>
            </div>
            <input name="purpose" placeholder="Purpose" required minLength={3} className={fieldClass} />
            <div className="grid grid-cols-2 gap-3">
              <select name="branch" className={fieldClass}>{['CSE', 'AI ML', 'AI DS', 'ECE', 'ME', 'IT'].map((branch) => <option key={branch}>{branch}</option>)}</select>
              <select name="year" className={fieldClass}>{[1, 2, 3, 4].map((year) => <option key={year} value={year}>Year {year}</option>)}</select>
              <input name="section" placeholder="Section" defaultValue="A" required className={fieldClass} />
              <input name="batch" placeholder="Batch (optional)" className={fieldClass} />
            </div>
            <input name="expected_attendance" type="number" min="1" defaultValue="30" required placeholder="Expected attendance" className={fieldClass} />
            <input name="required_facilities" placeholder="Required facilities (comma separated)" className={fieldClass} />
            <textarea name="notes" placeholder="Notes (optional)" className={fieldClass} rows={2} />
            <button className={submitClass}>Submit request</button>
          </form>, 'Requests require administrator approval.')}
          {user.role === 'admin' && panel('Add a room', <form onSubmit={createRoom} className="grid gap-3 sm:grid-cols-2">
            <select name="building_id" required className={fieldClass}>{buildings.length ? buildings.map((building) => <option key={building.id} value={building.id}>{building.name}</option>) : <option value="1">IET</option>}</select>
            <input name="code" placeholder="Room code" required className={fieldClass} />
            <input name="floor" placeholder="Floor" required className={fieldClass} />
            <input name="room_type" placeholder="Type" defaultValue="classroom" className={fieldClass} />
            <input name="capacity" type="number" min="1" placeholder="Capacity" required className={fieldClass} />
            <input name="facilities" placeholder="Facilities" className={fieldClass} />
            <input name="usage_permission" placeholder="Usage permission" defaultValue="all" className={fieldClass} />
            <label className="flex items-center gap-2 text-sm text-slate-300"><input name="examination_suitable" type="checkbox" /> Exam suitable</label>
            <button className={`${submitClass} sm:col-span-2`}>Add room</button>
          </form>, 'All room details here are configurable DEMO/TEST values.')}
          {panel('Room directory', recordsList(availableRooms ?? rooms, 'No rooms found.', (room) => (
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div><div className="font-medium text-white">{room.code} <span className="text-slate-400">· {room.room_type}</span></div><div className="mt-1 text-sm text-slate-400">{room.building_name} · Floor {room.floor} · {room.capacity} seats</div></div>
              <div className="text-right text-xs text-slate-400">{room.facilities}<div>{room.examination_suitable ? 'Exam suitable' : 'Not marked exam suitable'}</div></div>
            </div>
          )))}
        </div>
      )}

      {tab === 'Requests' && panel('Faculty room requests', recordsList(records, 'No requests to review.', (item) => (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div><div className="font-medium text-white">{item.purpose} · {item.room_code}</div><div className="mt-1 text-sm text-slate-400">{item.faculty_name} · {item.requested_date} · {item.start_time}–{item.end_time}</div></div>
          <div className="flex items-center gap-2"><span className={`rounded-full px-2.5 py-1 text-xs ${statusTone(item.status)}`}>{item.status}</span>{user.role === 'admin' && item.status === 'pending' && <>
            <button onClick={() => runAction(() => API.post(`/faculty-requests/${item.id}/decision?decision=approved`, {}, { headers }), 'Request approved.')} className="rounded-lg bg-emerald-500/15 px-3 py-2 text-xs text-emerald-200">Approve</button>
            <button onClick={() => runAction(() => API.post(`/faculty-requests/${item.id}/decision?decision=rejected`, {}, { headers }), 'Request rejected.')} className="rounded-lg bg-red-500/15 px-3 py-2 text-xs text-red-200">Reject</button>
          </>}</div>
        </div>
      )))}

      {tab === 'Exams' && (
        <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          {user.role === 'admin' && panel('Create examination', <form onSubmit={createExam} className="grid gap-3 sm:grid-cols-2">
            <input name="title" placeholder="Exam title" required className={fieldClass} />
            <input name="subject" placeholder="Subject" required className={fieldClass} />
            <input name="exam_date" type="date" min={today} required className={fieldClass} />
            <select name="room_ids" required multiple size={5} className={fieldClass}>{rooms.filter((room) => room.examination_suitable).map((room) => <option key={room.id} value={room.id}>{room.code} · {room.building_name} · {room.capacity} seats</option>)}</select>
            <input name="start_time" type="time" required className={fieldClass} />
            <input name="end_time" type="time" required className={fieldClass} />
            <input name="reporting_time" type="time" className={fieldClass} />
            <select name="branch" className={fieldClass}>{['CSE', 'AI ML', 'AI DS', 'ECE', 'ME', 'IT'].map((branch) => <option key={branch}>{branch}</option>)}</select>
            <div className="grid grid-cols-2 gap-3"><select name="year" className={fieldClass}>{[1, 2, 3, 4].map((year) => <option key={year} value={year}>Year {year}</option>)}</select><input name="section" placeholder="Section" defaultValue="A" required className={fieldClass} /></div>
            <label className="flex items-center gap-2 text-sm text-slate-300 sm:col-span-2"><input name="publish" type="checkbox" /> Publish exam and notify eligible students</label>
            <button className={`${submitClass} sm:col-span-2`}>Create and allocate seats</button>
          </form>, 'Choose multiple rooms with Ctrl/Command-click. The system checks total capacity and allocates students room-by-room.')}
          {panel('Exam schedule', recordsList(records, 'No examination details available.', (exam) => (
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="min-w-[220px]"><div className="font-medium text-white">{exam.title} · {exam.subject}</div><div className="mt-1 text-sm text-slate-400">{exam.exam_date} · {exam.start_time}–{exam.end_time}{exam.reporting_time ? ` · Report at ${exam.reporting_time}` : ''}</div>
                <div className="mt-1 text-sm text-sky-300">{exam.venue_released === false ? exam.building_name : `${exam.building_name}${exam.room_code ? ` · ${exam.room_code}${exam.room_floor ? ` · Floor ${exam.room_floor}` : ''}` : ''}${exam.seat_number ? ` · Seat ${exam.seat_number}` : ''}`}</div>
                {user.role === 'student' && exam.venue_released === false && <ExamReleaseTimer seconds={exam.seconds_until_release || 0} onRelease={onRefresh} />}
              </div>
              <div className="flex flex-wrap gap-2">
                {user.role === 'admin' && <>
                  <button onClick={() => loadExamAllocations(exam.id)} className="rounded-lg border border-slate-700 px-3 py-2 text-xs text-slate-200">Seats</button>
                  <button onClick={() => exportExamAllocations(exam.id)} className="rounded-lg border border-slate-700 px-3 py-2 text-xs text-slate-200">Export CSV</button>
                  <button onClick={() => runAction(() => API.patch(`/admin/exams/${exam.id}/publish?published=${!exam.published}`, {}, { headers }), exam.published ? 'Exam unpublished.' : 'Exam published.')} className="rounded-lg border border-slate-700 px-3 py-2 text-xs text-slate-200">{exam.published ? 'Unpublish' : 'Publish'}</button>
                </>}
              </div>
            </div>
          )))}
          {allocationReport && panel(`Seat allocations · ${allocationReport.title}`, <div className="space-y-4">{allocationReport.rooms.map((room: any) => <section key={room.room_id} className="rounded-xl border border-slate-800 p-3"><h3 className="font-medium text-white">{room.room} · {room.building} <span className="text-sm text-slate-400">{room.assigned}/{room.capacity} allocated</span></h3><div className="mt-2 grid gap-2 sm:grid-cols-2">{room.students.map((student: any) => <div key={`${room.room_id}-${student.seat_number}`} className="text-sm text-slate-300">{student.seat_number} · {student.name} · {student.roll_number}</div>)}</div></section>)}</div>)}
        </div>
      )}

      {tab === 'Announcements' && (
        <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          {user.role === 'admin' && panel('Publish announcement', <form onSubmit={createAnnouncement} className="grid gap-3">
            <input name="title" placeholder="Announcement title" required className={fieldClass} />
            <textarea name="message" placeholder="Message" required rows={4} className={fieldClass} />
            <select name="audience" className={fieldClass}><option value="all">All campus</option>{['CSE', 'AI ML', 'AI DS', 'ECE', 'ME', 'IT'].map((branch) => <option key={branch} value={branch}>{branch}</option>)}</select>
            <button className={submitClass}>Publish</button>
          </form>)}
          {panel('Campus announcements', recordsList(records, 'No announcements found.', (item) => <><div className="font-medium text-white">{item.title}</div><p className="mt-2 whitespace-pre-wrap text-sm text-slate-300">{item.message}</p><div className="mt-2 text-xs text-slate-500">{item.audience} · {item.created_at}</div></>))}
        </div>
      )}

      {tab === 'Campus Explorer' && (
        <div className="space-y-6">
          {user.role === 'admin' && panel('Import a building blueprint', <form onSubmit={uploadBlueprint} className="grid gap-3 sm:grid-cols-[1fr_1fr_auto]">
            <select name="building_id" required className={fieldClass}>{buildings.map((building) => <option key={building.id} value={building.id}>{building.name}</option>)}</select>
            <input name="file" type="file" accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg" required className={fieldClass} />
            <button className={submitClass}>Upload blueprint</button>
          </form>, 'PDF, PNG, and JPEG; maximum 10 MB. Files are stored privately and require sign-in to view.')}
          {panel('Campus Explorer', buildings.length === 0 ? <p className="text-sm text-slate-400">No buildings configured.</p> : (
            <div className="grid gap-5 lg:grid-cols-2">{buildings.map((building) => (
          <div key={building.id} className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
            <h3 className="font-semibold text-white">{building.name}</h3><p className="mt-1 text-sm text-slate-400">{building.location} · schematic demo listing</p>
            <div className="mt-4 grid gap-2 sm:grid-cols-2">{building.rooms.map((room: any) => <div key={room.id} className="rounded-xl border border-slate-800 p-3"><div className="text-sm font-medium text-slate-200">{room.code}</div><div className="text-xs text-slate-400">Floor {room.floor} · {room.room_type}</div></div>)}</div>
            {(building.blueprints || []).length > 0 && <div className="mt-4 space-y-2"><h4 className="text-sm font-medium text-slate-300">Imported blueprints</h4>{building.blueprints.map((blueprint: any) => <button key={blueprint.id} onClick={async () => {
              try {
                const { data } = await API.get(`/buildings/${building.id}/blueprints/${blueprint.id}`, { headers, responseType: 'blob' });
                window.open(URL.createObjectURL(data), '_blank', 'noopener,noreferrer');
              } catch {
                setError('Could not open this blueprint.');
              }
            }} className="block text-left text-sm text-sky-300 underline">{blueprint.filename}</button>)}</div>}
          </div>
            ))}</div>
          ), 'Room positions and capacities are not verified; import official blueprints when available.')}
        </div>
      )}

      {tab === 'Library Passes' && (
        <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          {user.role === 'admin' && <div className="space-y-6">
            {panel('Issue a library pass', <form onSubmit={issuePass} className="grid gap-3">
              <select name="student_id" required className={fieldClass}>{students.map((student) => <option key={student.id} value={student.id}>{student.name} · {student.email}</option>)}</select>
              <input name="expiry_date" type="date" min={today} required className={fieldClass} />
              <button className={submitClass}>Issue pass</button>
            </form>)}
            {panel('Verify a scanned pass', <form onSubmit={validateLibraryPass} className="flex flex-wrap gap-3">
              <input name="pass_code" required placeholder="Scanned QR pass code" className={`${fieldClass} min-w-[220px] flex-1`} />
              <button className={submitClass}>Verify validity</button>
            </form>, 'A QR code is only an identifier; the server checks revocation and expiry before confirming entry.')}
          </div>}
          {panel('Library passes', recordsList(records, 'No library passes found.', (pass) => <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-4"><div><div className="font-medium text-white">{pass.pass_code}</div><div className="mt-1 text-sm text-slate-400">{pass.student_name || 'My pass'} · expires {pass.expiry_date}</div></div>{user.role === 'student' && pass.status === 'active' && <QRCodeSVG value={pass.pass_code} size={88} bgColor="#ffffff" fgColor="#020817" aria-label="Library pass verification code" />}</div>
            <div className="flex items-center gap-2"><span className={`rounded-full px-2.5 py-1 text-xs ${statusTone(pass.status === 'active' ? 'approved' : 'rejected')}`}>{pass.status}</span>{user.role === 'admin' && pass.status === 'active' && <button onClick={() => runAction(() => API.patch(`/admin/library-passes/${pass.id}/revoke`, {}, { headers }), 'Library pass revoked.')} className="rounded-lg bg-red-500/10 px-3 py-2 text-xs text-red-200">Revoke</button>}</div>
          </div>))}
        </div>
      )}

      {tab === 'Reports' && (
        <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          {user.role === 'student' && panel('Report incorrect information', <form onSubmit={createReport} className="grid gap-3">
            <select name="category" className={fieldClass}><option>Timetable</option><option>Examination</option><option>Faculty</option><option>Room information</option><option>Other</option></select>
            <textarea name="details" required minLength={5} rows={4} placeholder="Describe the information that needs review" className={fieldClass} />
            <button className={submitClass}>Send report</button>
          </form>)}
          {panel(user.role === 'admin' ? 'Student reports' : 'My reports', recordsList(records, 'No reports have been filed.', (report) => <div className="flex flex-wrap items-center justify-between gap-3"><div><div className="font-medium text-white">{report.category} · {report.student || 'You'}</div><p className="mt-1 text-sm text-slate-400">{report.details}</p><span className={`mt-2 inline-flex rounded-full px-2 py-1 text-xs ${statusTone(report.status === 'resolved' ? 'approved' : 'pending')}`}>{report.status}</span></div>{user.role === 'admin' && report.status !== 'resolved' && <button onClick={() => runAction(() => API.patch(`/admin/reports/${report.id}/resolve`, {}, { headers }), 'Report marked as resolved.')} className="rounded-lg bg-emerald-500/15 px-3 py-2 text-xs text-emerald-200">Resolve</button>}</div>))}
        </div>
      )}

      {tab === 'Users' && (
        <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          {panel('Create a user account', <form onSubmit={createUser} className="grid gap-3 sm:grid-cols-2">
            <input name="name" placeholder="Full name" required minLength={2} className={fieldClass} />
            <input name="email" type="email" placeholder="Email" required className={fieldClass} />
            <input name="password" type="password" placeholder="Initial password (8+ characters)" required minLength={8} maxLength={72} className={fieldClass} />
            <select name="role" className={fieldClass}><option value="student">Student</option><option value="faculty">Faculty</option></select>
            <input name="branch" placeholder="Branch" className={fieldClass} />
            <select name="year" className={fieldClass}><option value="">Year (faculty can leave blank)</option>{[1, 2, 3, 4].map((year) => <option key={year} value={year}>Year {year}</option>)}</select>
            <input name="section" placeholder="Section" className={fieldClass} />
            <input name="roll_number" placeholder="Roll number (students)" className={fieldClass} />
            <input name="phone" placeholder="Phone (optional)" className={fieldClass} />
            <button className={`${submitClass} sm:col-span-2`}>Create account</button>
          </form>, 'Student accounts require branch, year, section, and roll number.')}
          {panel('Import student roster', <form onSubmit={importStudents} className="space-y-3">
            <p className="text-sm text-slate-400">CSV/XLSX columns: name, email, password, branch, year, section, roll_number. Passwords must be at least 8 characters.</p>
            <input name="file" type="file" accept=".csv,.xlsx" required className={fieldClass} />
            <button className={submitClass}>Import roster</button>
          </form>, 'Imports are transactional: invalid or duplicate rows reject the entire upload.')}
          {panel('Accounts', recordsList(records, 'No user accounts found.', (account) => <div className="flex flex-wrap justify-between gap-2"><div><div className="font-medium text-white">{account.name}</div><div className="text-sm text-slate-400">{account.email}</div></div><div className="text-right text-sm text-sky-300">{account.role}{account.branch ? ` · ${account.branch}` : ''}{account.year ? ` · Year ${account.year}` : ''}</div></div>))}
        </div>
      )}

      {tab === 'Audit history' && panel('Administrator activity', recordsList(records, 'No administrative actions recorded.', (item) => <div className="flex flex-wrap justify-between gap-2"><div><div className="font-medium text-white">{item.action} · {item.entity_type} #{item.entity_id}</div><div className="mt-1 text-sm text-slate-400">{item.details || 'No details'} · by {item.actor}</div></div><div className="text-xs text-slate-500">{item.created_at}</div></div>))}
    </div>
  );
}

function ExamReleaseTimer({ seconds, onRelease }: { seconds: number; onRelease: () => void }) {
  const [remaining, setRemaining] = useState(seconds);

  useEffect(() => {
    let countdown = Math.max(0, seconds);
    setRemaining(countdown);
    if (countdown === 0) {
      onRelease();
      return;
    }

    const timer = window.setInterval(() => {
      countdown -= 1;
      setRemaining(countdown);
      if (countdown <= 0) {
        window.clearInterval(timer);
        onRelease();
      }
    }, 1000);
    return () => window.clearInterval(timer);
  }, [seconds, onRelease]);

  const hours = Math.floor(remaining / 3600);
  const minutes = Math.floor((remaining % 3600) / 60);
  const secondsLeft = remaining % 60;
  return <div className="mt-2 text-sm text-amber-300">Venue and seat release in {hours}h {minutes}m {secondsLeft}s</div>;
}

function OverviewCards({ dashboard, user }: { dashboard: DashboardData; user: User }) {
  const metrics = useMemo(() => {
    if (user.role === 'student') {
      return [
        { label: 'Timetable', value: dashboard.summary?.timetable_count ?? 0, icon: CalendarDays },
        { label: 'Exams', value: dashboard.summary?.exam_count ?? 0, icon: BookOpen },
        { label: 'Active Passes', value: dashboard.summary?.active_passes ?? 0, icon: KeyRound },
      ];
    }
    if (user.role === 'faculty') {
      return [
        { label: 'My requests', value: dashboard.summary?.my_requests ?? 0, icon: Clock3 },
        { label: 'Available rooms', value: dashboard.summary?.available_rooms ?? 0, icon: DoorOpen },
      ];
    }
    return [
      { label: 'Total rooms', value: dashboard.summary?.total_rooms ?? 0, icon: DoorOpen },
      { label: 'Pending', value: dashboard.summary?.pending_requests ?? 0, icon: Clock3 },
      { label: 'Students', value: dashboard.summary?.students ?? 0, icon: Users },
      { label: 'Faculty', value: dashboard.summary?.faculty ?? 0, icon: Users },
    ];
  }, [dashboard, user.role]);

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {metrics.map(({ label, value, icon: Icon }) => (
        <div key={label} className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-slate-400">{label}</div>
              <div className="mt-2 text-3xl font-bold text-white">{value}</div>
            </div>
            <div className="rounded-xl bg-sky-500/10 p-3 text-sky-300"><Icon size={20} /></div>
          </div>
        </div>
      ))}
    </div>
  );
}

function ActionCard({ title, text, icon: Icon }: { title: string; text: string; icon: any }) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-slate-800 bg-slate-950/60 p-3">
      <div className="rounded-xl bg-sky-500/10 p-2 text-sky-300"><Icon size={18} /></div>
      <div>
        <div className="font-medium text-white">{title}</div>
        <div className="text-sm text-slate-400">{text}</div>
      </div>
    </div>
  );
}

function SummaryPanel({ title, items }: { title: string; items: any[] }) {
  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5">
      <h3 className="mb-4 text-lg font-semibold text-white">{title}</h3>
      <div className="space-y-3">
        {items.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-700 p-4 text-sm text-slate-400">No information available.</div>
        ) : (
          items.map((item: any, idx) => (
            <div key={idx} className="rounded-2xl border border-slate-800 bg-slate-950/60 p-3">
              <div className="font-medium text-white">{item.title || item.code || item.pass_code || item.room_code || item.name || 'Entry'}</div>
              <div className="mt-1 text-sm text-slate-400">{item.message || item.facilities || item.status || item.audience || item.floor || item.building_name || 'Campus detail'}</div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

export default App;
