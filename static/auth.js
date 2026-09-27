// EasyChamp sign-in (Keycloak, authorization code + PKCE). No library: the browser does the hashing.
// Tokens stay in this browser; the publish call sends the access token and the server checks it with
// Keycloak before using it, so the league is created in the organizer's own EasyChamp account.
const KEY = "snap-auth";
const FLOW = "snap-auth-flow";
let cfg = null;

export function configure(c) { cfg = c; }

function read() { try { return JSON.parse(localStorage.getItem(KEY) || "null"); } catch (e) { return null; } }
function write(v) { try { v ? localStorage.setItem(KEY, JSON.stringify(v)) : localStorage.removeItem(KEY); } catch (e) { /* private mode */ } }
function b64url(bytes) { return btoa(String.fromCharCode(...new Uint8Array(bytes))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, ""); }
function random(n = 32) { return b64url(crypto.getRandomValues(new Uint8Array(n))); }
function claims(jwt) {
  try { return JSON.parse(decodeURIComponent(escape(atob(jwt.split(".")[1].replace(/-/g, "+").replace(/_/g, "/"))))); } catch (e) { return {}; }
}
const redirectUri = () => `${location.origin}/callback`;

export function user() {
  const s = read();
  if (!s) return null;
  if (s.refreshExp && s.refreshExp < Date.now()) { write(null); return null; }
  return { name: s.name, email: s.email };
}

async function ready() {
  if (cfg && cfg.issuer && cfg.clientId) return cfg;
  const h = await (await fetch("/api/health", { cache: "no-store" })).json();  // the page loaded without it
  if (!h.auth) throw new Error("EasyChamp sign-in is not available right now. Reload the page and try again.");
  return (cfg = h.auth);
}

export async function signIn() {
  await ready();
  const verifier = random(48), state = random(16);
  const challenge = b64url(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier)));
  sessionStorage.setItem(FLOW, JSON.stringify({ verifier, state }));
  const q = new URLSearchParams({ client_id: cfg.clientId, redirect_uri: redirectUri(), response_type: "code",
    scope: "openid profile email", state, code_challenge: challenge, code_challenge_method: "S256" });
  location.assign(`${cfg.issuer}/protocol/openid-connect/auth?${q}`);
}

function keep(tok) {
  const c = claims(tok.access_token);
  write({ access: tok.access_token, refresh: tok.refresh_token, exp: Date.now() + (tok.expires_in || 300) * 1000,
    refreshExp: tok.refresh_expires_in ? Date.now() + tok.refresh_expires_in * 1000 : null,
    name: c.name || c.given_name || c.preferred_username || c.email || "Organizer", email: c.email || null });
}

async function tokenCall(body) {
  await ready();
  const r = await fetch(`${cfg.issuer}/protocol/openid-connect/token`, { method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" }, body: new URLSearchParams({ client_id: cfg.clientId, ...body }) });
  if (!r.ok) throw new Error(`sign-in failed (${r.status})`);
  return r.json();
}

// On /callback: swap the code for tokens, then return to the page. Returns true when a sign-in finished.
export async function finishSignIn() {
  if (location.pathname !== "/callback") return false;
  const q = new URLSearchParams(location.search);
  let flow = null;
  try { flow = JSON.parse(sessionStorage.getItem(FLOW) || "null"); } catch (e) { /* none */ }
  sessionStorage.removeItem(FLOW);
  if (q.get("code") && flow && q.get("state") === flow.state) {
    keep(await tokenCall({ grant_type: "authorization_code", code: q.get("code"), redirect_uri: redirectUri(), code_verifier: flow.verifier }));
  }
  history.replaceState(null, "", "/");
  return !!q.get("code");
}

// A fresh access token, refreshing it when it is about to expire; null when the organizer must sign in again.
export async function accessToken() {
  const s = read();
  if (!s) return null;
  if (s.exp - 30000 > Date.now()) return s.access;
  if (!s.refresh) { write(null); return null; }
  try { keep(await tokenCall({ grant_type: "refresh_token", refresh_token: s.refresh })); return read().access; }
  catch (e) { write(null); return null; }
}

export function signOut() { write(null); }
