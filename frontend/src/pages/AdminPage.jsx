import { useEffect, useState } from "react";
import { ArrowLeft, FileText, LockKeyhole, LogOut, Plus, ShieldCheck } from "lucide-react";
import { createRule, listRules } from "../services/api";
import { login, logout } from "../services/auth";

const initialForm = {
  rule_code: "",
  category: "food",
  field_name: "",
  requirement_description: "",
  validation_type: "presence",
  validation_expression: "",
  severity: "standard",
  mandatory: true,
  source_reference: "",
  rule_version: "2011-preliminary",
  active: true,
  reason: "",
};

export default function AdminPage({ onBack }) {
  const [user, setUser] = useState(null);
  const [credentials, setCredentials] = useState({ email: "", password: "" });
  const [form, setForm] = useState(initialForm);
  const [rules, setRules] = useState([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    listRules().then((result) => setRules(result.items)).catch((error) => setMessage(error.message));
  }, []);

  async function handleLogin(event) {
    event.preventDefault();
    try {
      const result = await login(credentials.email, credentials.password);
      setUser(result.user);
      setMessage("Authenticated administrator session started.");
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function handleCreate(event) {
    event.preventDefault();
    try {
      const created = await createRule(form);
      setRules((current) => [...current, created]);
      setForm(initialForm);
      setMessage("Rule created and audit logged.");
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function handleLogout() {
    await logout();
    setUser(null);
    setMessage("Session ended.");
  }

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  return (
    <div className="admin-page">
      <button className="back-button" onClick={onBack}>
        <ArrowLeft size={16} /> Overview
      </button>
      <div className="admin-heading">
        <div>
          <p className="eyebrow">Administration</p>
          <h1>Rules control.</h1>
          <p className="intro-copy">Manage verified rule records. Every mutation is recorded in the audit log.</p>
        </div>
        <div className="admin-lock">
          <LockKeyhole size={16} /> Protected
        </div>
      </div>
      {message && <div className="admin-message">{message}</div>}
      {!user ? (
        <form className="panel admin-login" onSubmit={handleLogin}>
          <div className="admin-login-icon">
            <ShieldCheck size={21} />
          </div>
          <h2>Administrator sign in</h2>
          <p>Use the admin credentials configured in the backend environment.</p>
          <input
            type="email"
            placeholder="Admin email"
            value={credentials.email}
            onChange={(event) => update("email", event.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={credentials.password}
            onChange={(event) => update("password", event.target.value)}
            required
          />
          <button className="primary-button" type="submit">
            <LockKeyhole size={16} /> Sign in
          </button>
        </form>
      ) : (
        <div className="admin-layout">
          <section className="panel rule-form-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">New rule</p>
                <h2>Add verified requirement</h2>
              </div>
              <Plus size={18} />
            </div>
            <form onSubmit={handleCreate}>
              <input
                placeholder="Rule code"
                value={form.rule_code}
                onChange={(event) => update("rule_code", event.target.value)}
                required
              />
              <select value={form.category} onChange={(event) => update("category", event.target.value)}>
                <option value="food">Food</option>
                <option value="cosmetics">Cosmetics</option>
                <option value="household_products">Household products</option>
                <option value="personal_care">Personal care</option>
                <option value="electronics">Electronics</option>
                <option value="clothing">Clothing</option>
                <option value="other_packaged_commodities">Other packaged commodities</option>
              </select>
              <input
                placeholder="Field name, e.g. mrp"
                value={form.field_name}
                onChange={(event) => update("field_name", event.target.value)}
                required
              />
              <textarea
                placeholder="Requirement description"
                value={form.requirement_description}
                onChange={(event) => update("requirement_description", event.target.value)}
                required
              />
              <select value={form.validation_type} onChange={(event) => update("validation_type", event.target.value)}>
                <option value="presence">Presence</option>
                <option value="regex">Regex</option>
              </select>
              <input
                placeholder="Validation expression (regex)"
                value={form.validation_expression}
                onChange={(event) => update("validation_expression", event.target.value)}
              />
              <select value={form.severity} onChange={(event) => update("severity", event.target.value)}>
                <option value="standard">Standard</option>
                <option value="critical">Critical</option>
              </select>
              <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, color: "#40584b", marginTop: 9 }}>
                <input
                  type="checkbox"
                  checked={form.mandatory}
                  onChange={(event) => update("mandatory", event.target.checked)}
                />
                Mandatory declaration
              </label>
              <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, color: "#40584b", marginTop: 9 }}>
                <input
                  type="checkbox"
                  checked={form.active}
                  onChange={(event) => update("active", event.target.checked)}
                />
                Active rule
              </label>
              <input
                placeholder="Official source reference"
                value={form.source_reference}
                onChange={(event) => update("source_reference", event.target.value)}
                required
              />
              <input
                placeholder="Rule version"
                value={form.rule_version}
                onChange={(event) => update("rule_version", event.target.value)}
                required
              />
              <input
                placeholder="Change reason"
                value={form.reason}
                onChange={(event) => update("reason", event.target.value)}
              />
              <button className="primary-button" type="submit">
                <Plus size={16} /> Create rule
              </button>
            </form>
            <button className="text-button logout-button" onClick={handleLogout}>
              <LogOut size={15} /> Sign out
            </button>
          </section>
          <section className="panel rule-list-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Versioned catalog</p>
                <h2>{rules.length} rule records</h2>
              </div>
              <FileText size={18} />
            </div>
            {rules.length ? (
              rules.map((rule) => (
                <div className="admin-rule" key={rule.id}>
                  <strong>{rule.rule_code}</strong>
                  <span>
                    {rule.category} · {rule.field_name} · v{rule.rule_version}
                  </span>
                  <small>{rule.source_reference}</small>
                </div>
              ))
            ) : (
              <div className="history-empty">
                <FileText size={21} />
                <p>No rule records yet.</p>
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
