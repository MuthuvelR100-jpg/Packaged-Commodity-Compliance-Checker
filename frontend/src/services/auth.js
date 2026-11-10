import { API_BASE_URL } from "./api";

async function authRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Authentication request failed.");
  return payload;
}

export function login(email, password) {
  return authRequest("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
}

export function logout() {
  return authRequest("/auth/logout", { method: "POST" });
}

export function getCurrentUser() {
  return authRequest("/auth/me");
}
