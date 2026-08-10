// In local dev, Vite's server.proxy forwards "/api" to the Flask backend
// (see vite.config.js) so a relative path works. That proxy does not exist
// in a static Vercel deployment, so production needs an absolute URL to a
// separately-hosted backend, supplied via VITE_API_BASE_URL.
const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || `Request failed (${res.status})`);
  }
  return data;
}

export const api = {
  me: () => request("/auth/me"),
  login: (username, password) =>
    request("/auth/login", { method: "POST", body: JSON.stringify({ username, password }) }),
  register: (username, password) =>
    request("/auth/register", { method: "POST", body: JSON.stringify({ username, password }) }),
  logout: () => request("/auth/logout", { method: "POST" }),
  processVideo: (url, method, percentage) =>
    request("/process", { method: "POST", body: JSON.stringify({ url, method, percentage }) }),
};
