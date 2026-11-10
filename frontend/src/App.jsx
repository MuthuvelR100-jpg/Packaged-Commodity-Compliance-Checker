import { useEffect, useState } from "react";
import {
  Activity,
  ArrowUpRight,
  BarChart3,
  Camera,
  CheckCircle2,
  ClipboardCheck,
  Clock3,
  FileText,
  HelpCircle,
  LayoutDashboard,
  Menu,
  PackageSearch,
  PanelLeftClose,
  Settings2,
  ShieldCheck,
  Upload,
  X,
} from "lucide-react";
import InspectionPage from "./pages/InspectionPage";
import HistoryPage from "./pages/HistoryPage";
import AdminPage from "./pages/AdminPage";
import RulesPage from "./pages/RulesPage";

const navigation = [
  { label: "Overview", icon: LayoutDashboard },
  { label: "New inspection", icon: ClipboardCheck },
  { label: "Inspection history", icon: Clock3 },
  { label: "Rules library", icon: FileText },
];

const inspections = [
  { id: "INS-2048", product: "Sunrise Detergent", category: "Household", date: "02 Sep 2026", score: "92%", status: "Needs review" },
  { id: "INS-2047", product: "Nourish Oats", category: "Food", date: "01 Sep 2026", score: "100%", status: "Compliant" },
  { id: "INS-2046", product: "Glow Care Lotion", category: "Personal care", date: "31 Aug 2026", score: "68%", status: "Non-compliant" },
];

function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [apiStatus, setApiStatus] = useState("checking");
  const [currentView, setCurrentView] = useState("overview");
  const viewTitle = currentView === "inspection" ? "Inspection" : currentView === "history" ? "History" : currentView === "admin" ? "Administration" : currentView === "rules" ? "Rules" : "Overview";

  useEffect(() => {
    fetch("/api/health")
      .then((response) => {
        if (!response.ok) throw new Error("API unavailable");
        return response.json();
      })
      .then(() => setApiStatus("online"))
      .catch(() => setApiStatus("offline"));
  }, []);

  return (
    <div className="app-shell">
      <aside className={`sidebar ${isSidebarOpen ? "sidebar--open" : ""}`}>
        <div className="brand-lockup">
          <div className="brand-mark"><ShieldCheck size={20} strokeWidth={2.4} /></div>
          <div><strong>Civic Lens</strong><span>Commodity compliance</span></div>
          <button className="icon-button sidebar-close" onClick={() => setIsSidebarOpen(false)} aria-label="Close navigation"><X size={18} /></button>
        </div>

        <div className="workspace-switcher"><span className="workspace-dot" /> SIH 2026 workspace <span className="chevron">⌄</span></div>
        <nav className="main-nav" aria-label="Primary navigation">
          <p className="nav-label">Workspace</p>
          {navigation.map(({ label, icon: Icon }) => {
            const targetView = label === "New inspection" ? "inspection" : label === "Inspection history" ? "history" : label === "Rules library" ? "rules" : "overview";
            const isActive = currentView === targetView;
            return (
              <button className={`nav-item ${isActive ? "nav-item--active" : ""}`} key={label} onClick={() => setCurrentView(targetView)}>
                <Icon size={18} /> <span>{label}</span>
                {label === "Inspection history" && <small>24</small>}
              </button>
            );
          })}
          <p className="nav-label nav-label--spaced">Administration</p>
          <button className={`nav-item ${currentView === "admin" ? "nav-item--active" : ""}`} onClick={() => setCurrentView("admin")}><Settings2 size={18} /><span>Admin controls</span></button>
          <button className="nav-item"><HelpCircle size={18} /><span>About Civic Lens</span></button>
        </nav>
        <div className="sidebar-footer"><div className="avatar">AS</div><div><strong>Authority staff</strong><span>Screening officer</span></div><button className="icon-button" aria-label="Account settings"><Settings2 size={16} /></button></div>
      </aside>

      {isSidebarOpen && <button className="sidebar-overlay" onClick={() => setIsSidebarOpen(false)} aria-label="Close navigation overlay" />}
      <main className="main-content">
        <header className="topbar">
          <button className="icon-button menu-trigger" onClick={() => setIsSidebarOpen(true)} aria-label="Open navigation"><Menu size={21} /></button>
          <div className="breadcrumb"><span>Workspace</span><span>/</span><strong>{viewTitle}</strong></div>
          <div className="topbar-actions"><div className={`api-pill api-pill--${apiStatus}`}><Activity size={14} /> API {apiStatus === "checking" ? "checking" : apiStatus}</div><button className="help-button"><HelpCircle size={16} /> Help centre</button></div>
        </header>

        {currentView === "inspection" ? <InspectionPage onBack={() => setCurrentView("overview")} /> : currentView === "history" ? <HistoryPage onBack={() => setCurrentView("overview")} /> : currentView === "admin" ? <AdminPage onBack={() => setCurrentView("overview")} /> : currentView === "rules" ? <RulesPage onBack={() => setCurrentView("overview")} /> : <div className="content-wrap">
          <section className="page-intro"><div><p className="eyebrow">Wednesday, 02 September 2026</p><h1>Good morning, <em>officer.</em></h1><p className="intro-copy">A clear view of your packaged commodity screening activity.</p></div><button className="primary-button" onClick={() => setCurrentView("inspection")}><ClipboardCheck size={18} /> Start inspection <ArrowUpRight size={17} /></button></section>

          <section className="signal-strip"><div className="signal-icon"><PackageSearch size={21} /></div><div><strong>Screening engine ready</strong><span>OCR and rule-based validation are available for a new inspection.</span></div><button className="text-button">View system status <ArrowUpRight size={15} /></button></section>

          <section className="metric-grid" aria-label="Inspection summary">
            <Metric icon={ClipboardCheck} label="Total inspections" value="248" trend="+18.4%" detail="vs. last month" accent="green" />
            <Metric icon={CheckCircle2} label="Compliant" value="156" trend="62.9%" detail="of all inspections" accent="teal" />
            <Metric icon={Clock3} label="Needs review" value="54" trend="21.8%" detail="awaiting verification" accent="amber" />
            <Metric icon={BarChart3} label="Avg. score" value="86.7%" trend="+4.2%" detail="vs. last month" accent="blue" />
          </section>

          <section className="dashboard-grid">
            <div className="panel inspections-panel"><div className="panel-heading"><div><p className="eyebrow">Latest activity</p><h2>Recent inspections</h2></div><button className="text-button">View all <ArrowUpRight size={15} /></button></div><div className="inspection-list">{inspections.map((inspection) => <InspectionRow inspection={inspection} key={inspection.id} />)}</div></div>
            <div className="panel distribution-panel"><div className="panel-heading"><div><p className="eyebrow">Across 248 checks</p><h2>Screening outcome</h2></div><button className="icon-button" aria-label="More chart options"><PanelLeftClose size={17} /></button></div><div className="donut-wrap"><div className="donut"><div><strong>62.9%</strong><span>compliant</span></div></div><div className="legend"><Legend color="green" label="Compliant" value="156" /><Legend color="amber" label="Needs review" value="54" /><Legend color="red" label="Non-compliant" value="38" /></div></div><div className="chart-note"><span className="note-bar" /> Most screenings are passing, but review items remain worth a second look.</div></div>
          </section>

          <footer className="page-footer"><span><ShieldCheck size={15} /> Automated screening assistance, not a legally binding determination.</span><span>Rule set: General PCM · v0.1 draft</span></footer>
        </div>}
      </main>
    </div>
  );
}

function Metric({ icon: Icon, label, value, trend, detail, accent }) { return <article className="metric-card"><div className={`metric-icon metric-icon--${accent}`}><Icon size={19} /></div><p>{label}</p><div className="metric-value">{value}</div><div className="metric-foot"><span className={`trend trend--${accent}`}>{trend}</span><span>{detail}</span></div></article>; }
function InspectionRow({ inspection }) { const statusClass = inspection.status.toLowerCase().replace(" ", "-"); return <div className="inspection-row"><div className="inspection-thumb"><PackageSearch size={17} /></div><div className="inspection-info"><strong>{inspection.product}</strong><span>{inspection.id} · {inspection.category}</span></div><span className={`status-badge status-badge--${statusClass}`}>{inspection.status}</span><div className="inspection-score"><strong>{inspection.score}</strong><span>{inspection.date}</span></div><button className="icon-button row-arrow" aria-label={`Open ${inspection.id}`}><ArrowUpRight size={16} /></button></div>; }
function Legend({ color, label, value }) { return <div className="legend-row"><span className={`legend-dot legend-dot--${color}`} /><span>{label}</span><strong>{value}</strong></div>; }

export default App;
