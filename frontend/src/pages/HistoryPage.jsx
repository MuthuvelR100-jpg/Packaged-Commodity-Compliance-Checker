import { useEffect, useState } from "react";
import { ArrowLeft, ArrowUpRight, ClipboardList, Download, LoaderCircle, Search, Trash2 } from "lucide-react";
import { deleteInspection, downloadInspectionReport, getInspection, listInspections } from "../services/api";

export default function HistoryPage({ onBack }) {
  const [filters, setFilters] = useState({ q: "", status: "", category: "" });
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listInspections(filters).then((result) => {
      if (!cancelled) setItems(result.items);
    }).catch((error) => {
      if (!cancelled) setMessage(error.message);
    }).finally(() => {
      if (!cancelled) setLoading(false);
    });
    return () => { cancelled = true; };
  }, [filters]);

  async function openInspection(id) {
    try {
      setSelected(await getInspection(id));
      setMessage("");
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function removeInspection(id) {
    if (!window.confirm("Delete this inspection record?")) return;
    try {
      await deleteInspection(id);
      setItems((current) => current.filter((item) => item.id !== id));
      if (selected?.id === id) setSelected(null);
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function downloadReport(id) {
    try {
      const blob = await downloadInspectionReport(id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `inspection-${id}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      setMessage(error.message);
    }
  }

  return <div className="history-page"><div className="history-heading"><div><button className="back-button" onClick={onBack}><ArrowLeft size={16} /> Overview</button><p className="eyebrow">Records</p><h1>Inspection history.</h1><p className="intro-copy">Review saved screening records and their extracted declarations.</p></div></div><div className="history-toolbar panel"><div className="search-control"><Search size={16} /><input aria-label="Search inspections" placeholder="Search product name" value={filters.q} onChange={(event) => setFilters({ ...filters, q: event.target.value })} /></div><select aria-label="Filter by status" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}><option value="">All statuses</option><option value="COMPLIANT">Compliant</option><option value="NEEDS_REVIEW">Needs review</option><option value="NON_COMPLIANT">Non-compliant</option></select><select aria-label="Filter by category" value={filters.category} onChange={(event) => setFilters({ ...filters, category: event.target.value })}><option value="">All categories</option><option value="food">Food</option><option value="cosmetics">Cosmetics</option><option value="household_products">Household products</option><option value="personal_care">Personal care</option></select></div>{message && <div className="history-message">{message}</div>}<div className="history-layout"><section className="panel history-list-panel"><div className="panel-heading"><div><p className="eyebrow">Saved records</p><h2>{items.length} inspections</h2></div>{loading && <LoaderCircle className="spin" size={17} />}</div>{!loading && items.length === 0 ? <div className="history-empty"><ClipboardList size={21} /><p>No inspections match these filters.</p></div> : <div className="history-list">{items.map((item) => <HistoryRow key={item.id} item={item} active={selected?.id === item.id} onOpen={() => openInspection(item.id)} onDelete={() => removeInspection(item.id)} />)}</div>}</section><section className="panel history-detail-panel">{selected ? <Detail inspection={selected} onDownload={downloadReport} /> : <div className="history-empty"><ClipboardList size={21} /><p>Select a record to view its details.</p></div>}</section></div></div>;
}

function HistoryRow({ item, active, onOpen, onDelete }) { const statusClass = (item.status || "review").toLowerCase().replace("_", "-"); return <div className={`history-row ${active ? "history-row--active" : ""}`}><button className="history-open" onClick={onOpen}><div className="history-row-icon"><ClipboardList size={16} /></div><div className="history-row-copy"><strong>{item.product_name || "Unnamed package"}</strong><span>{item.id.slice(0, 8)} · {item.category || "Uncategorized"}</span></div><span className={`status-badge status-badge--${statusClass}`}>{(item.status || "REVIEW").replace("_", " ")}</span></button><button className="icon-button history-delete" onClick={onDelete} aria-label={`Delete ${item.id}`}><Trash2 size={15} /></button></div>; }
function Detail({ inspection, onDownload }) { return <div className="detail-content"><div className="panel-heading"><div><p className="eyebrow">Inspection detail</p><h2>{inspection.product_name || "Unnamed package"}</h2></div><button className="text-button" onClick={() => onDownload(inspection.id)}><Download size={15} /> PDF report</button></div><div className="detail-grid"><DetailItem label="Inspection ID" value={inspection.id} /><DetailItem label="Category" value={inspection.category || "Not selected"} /><DetailItem label="Score" value={inspection.score === null ? "Not calculated" : `${inspection.score}%`} /><DetailItem label="Rule version" value={inspection.rule_version || "Not available"} /></div><h3>Declarations</h3>{inspection.declarations?.length ? <div className="detail-declarations">{inspection.declarations.map((declaration) => <div className="detail-declaration" key={declaration.id}><strong>{declaration.field_name.replaceAll("_", " ")}</strong><span>{declaration.extracted_value || "No value recorded"}</span><small>{declaration.status}</small></div>)}</div> : <p className="detail-muted">No declarations were saved for this record.</p>}</div>; }
function DetailItem({ label, value }) { return <div><span>{label}</span><strong>{value}</strong></div>; }
