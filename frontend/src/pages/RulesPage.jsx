import { useEffect, useState } from "react";
import { ArrowLeft, BookOpen, CheckCircle2, FileText, Filter, LoaderCircle, ShieldAlert } from "lucide-react";
import { listRules } from "../services/api";

const categories = [["", "All categories"], ["food", "Food"], ["cosmetics", "Cosmetics"], ["household_products", "Household products"], ["personal_care", "Personal care"], ["electronics", "Electronics"], ["clothing", "Clothing"], ["other_packaged_commodities", "Other packaged commodities"]];

export default function RulesPage({ onBack }) {
  const [rules, setRules] = useState([]);
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  useEffect(() => { setLoading(true); listRules().then((result) => setRules(result.items)).catch((error) => setMessage(error.message)).finally(() => setLoading(false)); }, []);
  const visibleRules = category ? rules.filter((rule) => rule.category === category) : rules;
  return <div className="rules-page"><button className="back-button" onClick={onBack}><ArrowLeft size={16} /> Overview</button><div className="rules-heading"><div><p className="eyebrow">Reference library</p><h1>Rules library.</h1><p className="intro-copy">Preliminary mappings from the provided Legal Metrology (Packaged Commodities) Rules, 2011 PDF.</p></div><div className="rules-source"><BookOpen size={16} /><span><strong>Rules 2011.pdf</strong><small>2011-preliminary</small></span></div></div><div className="rules-notice"><ShieldAlert size={17} /><span>These mappings are a screening aid. Verify current amendments and category-specific laws before production use.</span></div><div className="rules-toolbar panel"><Filter size={15} /><select aria-label="Filter rules by category" value={category} onChange={(event) => setCategory(event.target.value)}>{categories.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select><span>{visibleRules.length} rule records</span></div>{message && <div className="history-message">{message}</div>}{loading ? <div className="rules-loading"><LoaderCircle className="spin" size={18} /> Loading rule catalog...</div> : <div className="rules-grid">{visibleRules.map((rule) => <RuleCard rule={rule} key={rule.id} />)}</div>}</div>;
}

function RuleCard({ rule }) { return <article className={`rule-card panel ${rule.active ? "" : "rule-card--inactive"}`}><div className="rule-card-top"><div className="rule-icon">{rule.active ? <CheckCircle2 size={16} /> : <ShieldAlert size={16} />}</div><span className={`rule-state ${rule.active ? "rule-state--active" : "rule-state--inactive"}`}>{rule.active ? "Active mapping" : "Verify separately"}</span></div><p className="rule-code">{rule.rule_code}</p><h2>{rule.field_name.replaceAll("_", " ")}</h2><p className="rule-description">{rule.requirement_description}</p><div className="rule-meta"><span>{rule.category.replaceAll("_", " ")}</span><span>{rule.source_reference}</span><span>v{rule.rule_version}</span></div></article>; }
