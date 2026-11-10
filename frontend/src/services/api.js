const API_BASE_URL = "/api";

export async function uploadPackageImage(file) {
  const formData = new FormData();
  formData.append("image", file);

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  });

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Image upload failed.");
  }
  return payload;
}

export async function preprocessPackageImage(filename) {
  const response = await fetch(`${API_BASE_URL}/preprocess`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename }),
  });

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Image preprocessing failed.");
  }
  return payload.processing;
}

export async function runOCR(filename) {
  const response = await fetch(`${API_BASE_URL}/ocr`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename }),
  });

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "OCR failed.");
  }
  return payload.ocr;
}

export async function extractDeclarations(text, detections = []) {
  const response = await fetch(`${API_BASE_URL}/extract`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, detections }),
  });

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Declaration extraction failed.");
  }
  return payload.extraction;
}

export async function validateDeclarations(category, fields) {
  const response = await fetch(`${API_BASE_URL}/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ category, fields }),
  });

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Declaration validation failed.");
  }
  return payload.validation;
}

export async function scoreValidation(validation) {
  const response = await fetch(`${API_BASE_URL}/score`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ validation }),
  });

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Compliance score calculation failed.");
  }
  return payload.score;
}

export async function listInspections(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  const response = await fetch(`${API_BASE_URL}/inspections?${params}`);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Could not load inspection history.");
  return payload;
}

export async function getInspection(id) {
  const response = await fetch(`${API_BASE_URL}/inspection/${id}`);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Could not load inspection.");
  return payload;
}

export async function deleteInspection(id) {
  const response = await fetch(`${API_BASE_URL}/inspection/${id}`, { method: "DELETE", credentials: "include" });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Could not delete inspection.");
  return payload;
}

export async function downloadInspectionReport(id) {
  const response = await fetch(`${API_BASE_URL}/report/${id}`);
  if (!response.ok) {
    const payload = await response.json();
    throw new Error(payload.error || "Could not generate report.");
  }
  return response.blob();
}

export async function listRules() {
  const response = await fetch(`${API_BASE_URL}/rules`);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Could not load rules.");
  return payload;
}

export async function createRule(rule) {
  const response = await fetch(`${API_BASE_URL}/rules`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify(rule) });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Could not create rule.");
  return payload;
}

export async function createInspection(data) {
  const response = await fetch(`${API_BASE_URL}/inspection`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Could not save inspection.");
  return payload;
}

export { API_BASE_URL };
