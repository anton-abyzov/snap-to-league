// Same rules as app/standings.py: group stage only, 3 for a win, 1 for a draw,
// sorted by points, goal difference, goals for, then name.
const POINTS = { basketball: [2, 0, 1], nba2k: [2, 0, 1] }; // win, draw, loss; others 3-1-0

export function computeStandings(matches, teams = [], sport = "") {
  const [WIN, DRAW, LOSS] = POINTS[(sport || "").toLowerCase()] || [3, 1, 0];
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
      if (gf > ga) { r.W++; r.Pts += WIN; } else if (gf === ga) { r.D++; r.Pts += DRAW; } else { r.L++; r.Pts += LOSS; }
    }
  }
  const out = [...rows.values()];
  out.forEach((r) => { r.GD = r.GF - r.GA; });
  return out.sort((x, y) => y.Pts - x.Pts || y.GD - x.GD || y.GF - x.GF || x.team.localeCompare(y.team));
}

// One table per group when the board has groups ("Group A", "Group B"); otherwise one table.
export function groupTables(matches, teams = [], sport = "") {
  const labels = [...new Set(matches.filter((m) => m.stage === "group").map((m) => m.group || ""))];
  if (labels.length <= 1) {
    const rows = computeStandings(matches, teams, sport);
    return rows.length ? [{ label: labels[0] ? `Group ${labels[0]}` : "", rows }] : [];
  }
  return labels.sort().map((g) => ({ label: g ? `Group ${g}` : "Other games", rows: computeStandings(matches.filter((m) => m.stage !== "group" || (m.group || "") === g), [], sport) }));
}

export function groupTablesHtml(tables) {
  return tables.map((t) => `${t.label ? `<div class="stagehead">${esc(t.label)}</div>` : ""}${standingsTable(t.rows)}`).join("");
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
    const named = { quarterfinal: "Quarterfinals", semifinal: "Semifinals", final: "Final" };
    const third = /3rd|third/i.test(`${m.round || ""}`);
    const label = third ? "3rd place" : named[m.stage] || m.round || "Knockout";
    if (!rounds.has(label)) rounds.set(label, { label, rank: third ? 4 : STAGE_RANK[m.stage] ?? 0, first: i, matches: [] });
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

// ---------- leaderboards (races, heats, quizzes, cup stacking) ----------
export function toNumber(v) {
  if (v === null || v === undefined || v === "") return null;
  const s = String(v).trim().toLowerCase().replace(",", ".");
  const t = s.match(/^(?:(\d+):)?(\d+):(\d+(?:\.\d+)?)$/);
  if (t) return (+(t[1] || 0)) * 3600 + (+t[2]) * 60 + parseFloat(t[3]);
  const n = s.match(/-?\d+(?:\.\d+)?/);
  return n ? parseFloat(n[0]) : null;
}

export function rankLeaderboard(lb) {
  const rows = (lb.entries || []).map((e) => {
    let score = toNumber(e.total);
    const vals = (e.values || []).map(toNumber);
    if (score === null && vals.some((v) => v !== null)) {
      score = vals.reduce((a, v) => a + (v || 0), 0);
      if (lb.lower_is_better && vals.some((v) => v === null)) score = null;
    }
    const out = /dnf|dns|dq|dsq|out/i.test(e.note || "");
    return { ...e, score: out ? null : score };
  });
  rows.sort((a, b) => (a.score === null) - (b.score === null) || (a.score === null ? 0 : lb.lower_is_better ? a.score - b.score : b.score - a.score) || a.name.localeCompare(b.name));
  let place = 0, prev;
  rows.forEach((r, i) => { if (r.score === null) { r.place = null; return; } if (r.score !== prev) { place = i + 1; prev = r.score; } r.place = place; });
  return rows;
}

function fmt(n, lb) {
  if (n === null || n === undefined) return "–";
  if (lb.metric === "time" && n >= 60) { const m = Math.floor(n / 60), s = (n - m * 60).toFixed(2).padStart(5, "0"); return `${m}:${s}`; }
  return Number.isInteger(n) ? String(n) : n.toFixed(2);
}

export function leaderboardHtml(lb) {
  if (!lb || !(lb.entries || []).length) return "";
  const rows = rankLeaderboard(lb);
  const podium = rows.filter((r) => r.place && r.place <= 3).slice(0, 3);
  const order = [1, 0, 2].map((i) => podium[i]).filter(Boolean);
  const pod = `<div class="podium">${order.map((r) => `<div class="step p${r.place}" style="--i:${r.place}"><span class="medal">${r.place}</span><b>${esc(r.name)}</b><em>${fmt(r.score, lb)} ${esc(lb.metric || "")}</em><i></i></div>`).join("")}</div>`;
  const rounds = lb.rounds || [];
  const head = `<thead><tr><th class="pos">#</th><th class="team">Name</th>${rounds.map((r) => `<th>${esc(r)}</th>`).join("")}<th>${esc(lb.lower_is_better ? "Best" : "Total")}</th></tr></thead>`;
  const body = rows.map((r, i) => `<tr style="--i:${i}" class="${r.place && r.place <= 3 ? "through" : ""}"><td class="pos">${r.place ?? "–"}</td><td class="team">${esc(r.name)}${r.note ? ` <span class="muted-cell">${esc(r.note)}</span>` : ""}</td>${rounds.map((_, j) => `<td>${esc((r.values || [])[j] ?? "–")}</td>`).join("")}<td class="pts">${fmt(r.score, lb)}</td></tr>`).join("");
  return pod + `<table class="st">${head}<tbody>${body}</tbody></table>`;
}
