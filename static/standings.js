// Same rules as app/standings.py: group stage only, 3 for a win, 1 for a draw,
// sorted by points, goal difference, goals for, then name.
export function computeStandings(matches, teams = []) {
  if (!matches.some((m) => m.stage === "group")) return [];
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
  const body = rows.map((r, i) => `<tr class="${i < through ? "through" : ""}" style="--i:${i}"><td class="pos">${i + 1}</td><td class="team">${esc(r.team)}</td><td>${r.P}</td><td>${r.W}</td><td>${r.D}</td><td>${r.L}</td><td>${r.GF}</td><td>${r.GA}</td><td>${r.GD > 0 ? "+" : ""}${r.GD}</td><td class="pts">${r.Pts}</td></tr>`).join("");
  return `<table class="st">${head}<tbody>${body}</tbody></table>`;
}

const STAGE_RANK = { knockout: 0, quarterfinal: 1, semifinal: 2, final: 3 };

export function bracketRounds(matches) {
  const ko = matches.filter((m) => m.stage && m.stage !== "group");
  const rounds = new Map();
  ko.forEach((m, i) => {
    const label = m.round || (m.stage === "knockout" ? "Knockout" : m.stage[0].toUpperCase() + m.stage.slice(1));
    if (!rounds.has(label)) rounds.set(label, { label, rank: STAGE_RANK[m.stage] ?? 0, first: i, matches: [] });
    rounds.get(label).matches.push(m);
  });
  return [...rounds.values()].sort((a, b) => a.rank - b.rank || a.first - b.first);
}

export function bracketHtml(matches) {
  const rounds = bracketRounds(matches);
  if (!rounds.length) return "";
  const side = (m, who) => {
    const name = who === "h" ? m.home : m.away;
    const score = who === "h" ? m.homeScore : m.awayScore;
    const win = m.winner && m.winner === name;
    return `<div class="p ${win ? "win" : ""}"><span>${esc(name)}</span><span class="sc">${score ?? (win ? "W" : "")}</span></div>`;
  };
  return `<div class="bracket">${rounds.map((r) => `<div class="round"><div class="stagehead">${esc(r.label)}</div>${r.matches.map((m) => `<div class="bm">${side(m, "h")}${side(m, "a")}${m.status !== "played" && (m.when || m.venue) ? `<div class="when">${esc([m.when, m.venue].filter(Boolean).join(" · "))}</div>` : ""}</div>`).join("")}</div>`).join("")}</div>`;
}

export function readOut(name, rows, matches) {
  const lines = [`${name}.`];
  if (rows.length) lines.push(`Standings after ${rows.reduce((s, r) => s + r.P, 0) / 2} games.`);
  rows.forEach((r, i) => lines.push(`${ordinal(i + 1)}, ${r.team}, ${r.Pts} point${r.Pts === 1 ? "" : "s"}.`));
  const rounds = bracketRounds(matches);
  const lastPlayed = [...rounds].reverse().find((r) => r.matches.some((m) => m.winner));
  if (lastPlayed) {
    lines.push(`${lastPlayed.label} results.`);
    lastPlayed.matches.filter((m) => m.winner).forEach((m) => {
      const loser = m.winner === m.home ? m.away : m.home;
      const sc = m.homeScore !== null && m.homeScore !== undefined && m.awayScore !== null && m.awayScore !== undefined ? ` ${Math.max(m.homeScore, m.awayScore)} to ${Math.min(m.homeScore, m.awayScore)}` : "";
      lines.push(`${m.winner} beat ${loser}${sc}.`);
    });
  }
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

export function goalsText(m) {
  if (!m.goals || !m.goals.length) return "";
  const side = (s) => m.goals.filter((g) => g.side === s).map((g) => `${g.player}${g.count > 1 ? ` ${g.count}` : ""}${g.minute ? ` ${g.minute}${g.minute.includes("'") ? "" : "'"}` : ""}`).join(", ");
  const h = side("home"), a = side("away");
  return `Goals: ${h || "none"}${a ? ` / ${a}` : ""}`;
}

// Scorers across every game: goals, games scored in, and the minutes when written.
export function topScorers(matches) {
  const rows = new Map();
  for (const m of matches) {
    for (const g of m.goals || []) {
      const team = g.side === "home" ? m.home : m.away;
      const key = `${g.player.toLowerCase()}|${team.toLowerCase()}`;
      if (!rows.has(key)) rows.set(key, { player: g.player, team, number: g.number || "", goals: 0, games: new Set(), minutes: [] });
      const r = rows.get(key);
      r.goals += g.count || 1; r.games.add(`${m.home}|${m.away}`);
      if (g.minute) r.minutes.push(`${g.minute}${g.minute.includes("'") ? "" : "'"} v ${g.side === "home" ? m.away : m.home}`);
    }
  }
  return [...rows.values()].sort((a, b) => b.goals - a.goals || a.player.localeCompare(b.player));
}

export function scorersTable(rows) {
  if (!rows.length) return "";
  return `<table class="st scorers"><thead><tr><th class="pos">#</th><th class="team">Player</th><th class="team">Team</th><th>G</th><th class="team">When</th></tr></thead><tbody>${rows.map((r, i) =>
    `<tr style="--i:${i}"><td class="pos">${i + 1}</td><td class="team">${r.number ? `<span class="shirt">${esc(r.number)}</span>` : ""}${esc(r.player)}</td><td class="team muted-cell">${esc(r.team)}</td><td class="pts">${r.goals}</td><td class="team muted-cell">${esc(r.minutes.join(", "))}</td></tr>`).join("")}</tbody></table>`;
}
