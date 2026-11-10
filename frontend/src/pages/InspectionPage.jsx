import { useState } from "react";
import { AlertTriangle, ArrowLeft, Camera, CheckCircle2, FileSearch, LoaderCircle, ScanLine, Upload, XCircle } from "lucide-react";
import { createInspection, extractDeclarations, preprocessPackageImage, runOCR, scoreValidation, uploadPackageImage, validateDeclarations } from "../services/api";

const categories = [
  ["food", "Food"],
  ["cosmetics", "Cosmetics"],
  ["household_products", "Household products"],
  ["personal_care", "Personal care"],
  ["electronics", "Electronics"],
  ["clothing", "Clothing"],
  ["other_packaged_commodities", "Other packaged commodities"],
];

const stages = ["Upload", "Preprocess", "Read package", "Extract fields", "Validate"];

export default function InspectionPage({ onBack }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [category, setCategory] = useState("other_packaged_commodities");
  const [stage, setStage] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [ocr, setOcr] = useState(null);
  const [extraction, setExtraction] = useState(null);
  const [score, setScore] = useState(null);
  const [savedId, setSavedId] = useState(null);

  function chooseFile(event) {
    const selected = event.target.files?.[0];
    if (!selected) return;
    setFile(selected);
    setPreview(URL.createObjectURL(selected));
    setError("");
    setOcr(null);
    setExtraction(null);
    setScore(null);
    setSavedId(null);
    setStage(0);
  }

  async function startInspection() {
    if (!file) return;
    setBusy(true);
    setError("");
    setSavedId(null);
    try {
      setStage(1);
      const uploaded = await uploadPackageImage(file);
      const processed = await preprocessPackageImage(uploaded.image.filename);
      if (processed.quality === "poor") {
        setError(processed.quality_message);
        setStage(1);
        return;
      }
      setStage(2);
      const ocrResult = await runOCR(processed.processed_filename);
      setOcr(ocrResult);
      setStage(3);
      const extracted = await extractDeclarations(ocrResult.text, ocrResult.detections);
      setExtraction(extracted);
      setStage(4);
      const validation = await validateDeclarations(category, extracted.fields);
      const scoreResult = await scoreValidation(validation);
      setScore(scoreResult);

      const declarations = Object.values(extracted.fields).map((field) => ({
        field_name: field.field_name,
        extracted_value: field.value,
        status: field.status,
        ocr_confidence: field.confidence,
        explanation: field.message,
      }));

      const saved = await createInspection({
        product_name: extracted.fields.product_name?.value || file.name,
        category,
        status: scoreResult.status,
        score: scoreResult.score,
        image_path: uploaded.image.filename,
        processed_image_path: processed.processed_filename,
        ocr_detections: ocrResult.detections,
        rule_version: scoreResult.rule_versions?.[0],
        declarations,
      });
      setSavedId(saved.id);
    } catch (caughtError) {
      setError(caughtError.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="inspection-page">
      <div className="inspection-heading"><div><button className="back-button" onClick={onBack}><ArrowLeft size={16} /> Overview</button><p className="eyebrow">New screening</p><h1>Inspect a package.</h1><p className="intro-copy">Read the label first. The rule engine will show what needs a closer look.</p></div><div className="inspection-disclaimer"><ScanLine size={17} /> Screening assistance only</div></div>
      <div className="inspection-layout">
        <section className="panel intake-panel">
          <div className="panel-heading"><div><p className="eyebrow">Step 01</p><h2>Package image</h2></div><span className="step-count">{file ? "Ready" : "Required"}</span></div>
          {!preview ? <label className="drop-zone"><Upload size={23} /><strong>Choose a package image</strong><span>JPG, PNG, or WEBP · max 10 MB</span><input type="file" accept="image/jpeg,image/png,image/webp" onChange={chooseFile} /></label> : <div className="image-preview"><img src={preview} alt="Selected package" /><label className="replace-image"><Upload size={14} /> Replace<input type="file" accept="image/jpeg,image/png,image/webp" onChange={chooseFile} /></label><button className="remove-image" onClick={() => { setFile(null); setPreview(""); }} aria-label="Remove image"><XCircle size={19} /></button></div>}
          <div className="category-control"><label htmlFor="category">Product category</label><select id="category" value={category} onChange={(event) => setCategory(event.target.value)}>{categories.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select><span>Choose manually when automatic classification is uncertain.</span></div>
          <button className="primary-button inspect-button" disabled={!file || busy} onClick={startInspection}>{busy ? <LoaderCircle className="spin" size={17} /> : <FileSearch size={17} />}{busy ? "Processing package..." : "Run inspection"}</button>
          {error && <div className="inspection-error"><AlertTriangle size={17} /><span>{error}</span></div>}
        </section>
        <section className="inspection-main">
          <div className="progress-panel panel"><div className="panel-heading"><div><p className="eyebrow">Live pipeline</p><h2>Inspection progress</h2></div><span className="progress-label">{stage + 1} / {stages.length}</span></div><div className="stage-list">{stages.map((label, index) => <div className={`stage-item ${index < stage ? "stage-item--done" : ""} ${index === stage ? "stage-item--current" : ""}`} key={label}><span className="stage-number">{index < stage ? <CheckCircle2 size={15} /> : index + 1}</span><span>{label}</span>{index === stage && busy && <LoaderCircle className="spin stage-loader" size={14} />}</div>)}</div></div>
          {score ? <ResultSummary score={score} extraction={extraction} ocr={ocr} /> : <div className="empty-result panel"><div className="empty-result-icon"><Camera size={21} /></div><h2>Your result will appear here</h2><p>Upload a clear package image to see detected declarations, confidence, and rule-based screening results.</p></div>}
        </section>
      </div>
    </div>
  );
}

function ResultSummary({ score, extraction, ocr }) {
  const statusClass = score.status.toLowerCase().replace("_", "-");
  const fields = Object.values(extraction.fields);
  return <div className="result-stack"><section className="result-hero panel"><div><p className="eyebrow">Inspection result</p><h2>{score.status.replaceAll("_", " ")}</h2><p>{score.message}</p></div><div className={`result-score result-score--${statusClass}`}><strong>{score.score === null ? "—" : `${score.score}%`}</strong><span>screening score</span></div></section><section className="panel declaration-panel"><div className="panel-heading"><div><p className="eyebrow">Extracted declarations</p><h2>Field review</h2></div><span className="result-meta">OCR avg. {ocr?.average_confidence ? `${Math.round(ocr.average_confidence * 100)}%` : "n/a"}</span></div><div className="declaration-list">{fields.map((field) => <div className="declaration-row" key={field.field_name}><div className={`declaration-icon declaration-icon--${field.status}`} >{field.status === "detected" ? <CheckCircle2 size={15} /> : <AlertTriangle size={15} />}</div><div className="declaration-copy"><strong>{field.field_name.replaceAll("_", " ")}</strong><span>{field.value || field.message}</span></div><span className={`field-status field-status--${field.status}`}>{field.status}</span></div>)}</div></section></div>;
}
