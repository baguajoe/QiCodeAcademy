// Thin fetch wrapper for the Flask API (see API.md). Same-origin: /api/...
export class ApiError extends Error {
  constructor(status, body) {
    super((body && body.message) || (status === 0 ? "network" : `HTTP ${status}`));
    this.status = status;
    this.code = body && body.error;
    this.errors = (body && body.errors) || {};
    this.body = body;
  }
}

let authToken = null;
let unauthorizedHandler = null;

export function setAuthToken(token) {
  authToken = token || null;
}
export function onUnauthorized(fn) {
  unauthorizedHandler = fn;
}

function buildUrl(path, params) {
  const url = new URL(`/api${path}`, window.location.origin);
  Object.entries(params || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
  });
  return url.toString();
}

async function request(method, path, { params, body, auth = false, raw = false, signal } = {}) {
  const headers = { Accept: "application/json" };
  let payload;
  if (body instanceof FormData) payload = body;
  else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  if (auth && authToken) headers.Authorization = `Bearer ${authToken}`;

  let res;
  try {
    res = await fetch(buildUrl(path, params), { method, headers, body: payload, signal });
  } catch (err) {
    if (err.name === "AbortError") throw err;
    throw new ApiError(0, null);
  }
  if (res.status === 401 && auth && unauthorizedHandler) unauthorizedHandler();
  if (raw) {
    if (!res.ok) throw new ApiError(res.status, await res.json().catch(() => null));
    return res;
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, data);
  return data;
}

export const api = {
  get: (path, opts) => request("GET", path, opts),
  post: (path, body, opts) => request("POST", path, { ...opts, body }),
  put: (path, body, opts) => request("PUT", path, { ...opts, body }),
  patch: (path, body, opts) => request("PATCH", path, { ...opts, body }),
  del: (path, opts) => request("DELETE", path, opts),
};

// Admin helpers (JWT)
export const adminApi = {
  get: (path, opts) => request("GET", path, { ...opts, auth: true }),
  post: (path, body, opts) => request("POST", path, { ...opts, body, auth: true }),
  patch: (path, body, opts) => request("PATCH", path, { ...opts, body, auth: true }),
  del: (path, opts) => request("DELETE", path, { ...opts, auth: true }),
  download: async (path, filename, params) => {
    const res = await request("GET", path, { params, auth: true, raw: true });
    const url = URL.createObjectURL(await res.blob());
    const a = Object.assign(document.createElement("a"), { href: url, download: filename });
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  },
};
