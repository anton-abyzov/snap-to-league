// Same rules as app/standings.py: group stage only, 3 for a win, 1 for a draw,
// sorted by points, goal difference, goals for, then name.
export function computeStandings(matches, teams = []) {
  const rows = new Map();
  const row = (t) => {
    if (!rows.has(t)) rows.set(t, { team: t, P: 0, W: 0, D: 0, L: 0, GF: 0, GA: 0, GD: 0, Pts: 0 });
    return rows.get(t);
  };
  teams.forEach(row);
  for (const m of matches) {
    if (m.stage !== "group" || !m.home || !m.away) continue;
    const h = row(m.home), a = row(m.away);
    const hs = num(m.homeScore), as = num(m.awayScore);
    if (m.status !== "played" || hs === null || as === null) continue;
    for (const [r, gf, ga] of [[h, hs, as], [a, as, hs]]) {
      r.P++; r.GF += gf; r.GA += ga;
      if (gf > ga) { r.W++; r.Pts += 3; } else if (gf === ga) { r.D++; r.Pts += 1; } else { r.L++; }
    }
  }
  const out = [...rows.values()];
  out.forEach((r) => { r.GD = r.GF - r.GA; });
  return out.sort((x, y) => y.Pts - x.Pts || y.GD - x.GD || y.GF - x.GF || x.team.localeCompare(y.team));
}

export function num(v) {
  if (v === null || v === undefined || v === "") return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

export function standingsTable(rows, through = 2) {
  const head = `<thead><tr><th class="pos">#</th><th class="team">Team</th><th>P</th><th>W</th><th>D</th><th>L</th><th>GF</th><th>GA</th><th>GD</th><th>Pts</th></tr></thead>`;
  const body = rows.map((r, i) => `<tr class="${i < through ? "through" : ""}"><td class="pos">${i + 1}</td><td class="team">${esc(r.team)}</td><td>${r.P}</td><td>${r.W}</td><td>${r.D}</td><td>${r.L}</td><td>${r.GF}</td><td>${r.GA}</td><td>${r.GD > 0 ? "+" : ""}${r.GD}</td><td class="pts">${r.Pts}</td></tr>`).join("");
  return `<table class="st">${head}<tbody>${body}</tbody></table>`;
}

export function readOut(name, rows, matches) {
  const lines = [`${name}. Standings after ${rows.reduce((s, r) => s + r.P, 0) / 2} games.`];
  rows.forEach((r, i) => lines.push(`${ordinal(i + 1)}, ${r.team}, ${r.Pts} point${r.Pts === 1 ? "" : "s"}.`));
  const next = matches.find((m) => m.status === "scheduled");
  if (next) lines.push(`Next up${next.stage !== "group" ? `, the ${next.stage}` : ""}: ${next.home} against ${next.away}${next.when ? `, ${next.when}` : ""}${next.venue ? ` on ${next.venue}` : ""}.`);
  return lines.join(" ");
}

function ordinal(n) { return ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth"][n - 1] || `Number ${n}`; }

export function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

export async function speak(text) {
  try {
    const r = await fetch("/api/speak", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ text }) });
    if (r.status === 200) { const a = new Audio(URL.createObjectURL(await r.blob())); await a.play(); return "elevenlabs"; }
  } catch (e) { console.warn("voice service failed, using the browser voice", e); }
  if ("speechSynthesis" in window) { speechSynthesis.cancel(); speechSynthesis.speak(new SpeechSynthesisUtterance(text)); return "browser"; }
  return "none";
}
