const $ = (s, r = document) => r.querySelector(s);
const esc = v => String(v ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

function toast(msg, ok = true) {
  const t = $("#toast");
  t.textContent = msg; t.className = "show " + (ok ? "ok" : "err");
  clearTimeout(toast.id); toast.id = setTimeout(() => t.className = "", 3500);
}

async function api(path, method = "GET", data) {
  const res = await fetch(path, {
    method, headers: { "Content-Type": "application/json" },
    body: data ? JSON.stringify(data) : undefined
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(json.error || "Request failed");
  return json;
}

function table(el, cols, rows) {
  el.innerHTML = "<thead><tr>" + cols.map(c => `<th>${c[0]}</th>`).join("") + "</tr></thead><tbody>" +
    (rows.length ? rows.map(r => "<tr>" + cols.map(c => `<td>${c[2] ? c[2](r) : esc(r[c[1]])}</td>`).join("") + "</tr>").join("")
                 : `<tr><td colspan="${cols.length}">No data yet</td></tr>`) + "</tbody>";
}

const loaders = {
  async standings() {
    const rows = await api("/api/standings");
    table($("#t-standings"), [["#", "", r => rows.indexOf(r) + 1], ["Team", "team_name"], ["Played", "played"],
      ["Won", "won"], ["Lost", "lost"], ["Points", "points", r => `<b>${r.points}</b>`]], rows);
  },
  async report() {
    table($("#t-report"), [["Player", "player_name"], ["Team", "team_name"], ["Total points", "total_points"],
      ["Avg efficiency", "avg_efficiency"], ["Grade", "grade", r => `<span class="badge ${esc(r.grade)}">${esc(r.grade)}</span>`]],
      await api("/api/player-report"));
  },
  async scorers() {
    const rows = await api("/api/top-scorers?n=" + ($("#n").value || 3));
    const keys = rows.length ? Object.keys(rows[0]) : [];
    table($("#t-scorers"), [["Rank", "", r => rows.indexOf(r) + 1], ...keys.map(k => [k.replace(/_/g, " "), k])], rows);
  },
  async matches() {
    table($("#t-matches"), [["ID", "match_id"], ["Date", "match_date"], ["Team 1", "team1"], ["Team 2", "team2"],
      ["Score", "", r => `${r.score1} – ${r.score2}`], ["Winner", "winner"]], await api("/api/matches"));
  },
  async manage() {
    const [teams, matches, players] = await Promise.all([api("/api/teams"), api("/api/matches"), api("/api/players")]);
    const opts = (rows, v, l) => rows.map(r => `<option value="${esc(r[v])}">${esc(l(r))}</option>`).join("");
    document.querySelectorAll("select.teams").forEach(s => s.innerHTML = opts(teams, "team_id", r => r.team_name));
    $("#sel-match").innerHTML = opts(matches, "match_id", r => `#${r.match_id} ${r.team1} vs ${r.team2}`);
    $("#sel-player").innerHTML = opts(players, "player_id", r => `${r.player_name} (${r.team_name})`);
  }
};

function show(name) {
  document.querySelectorAll(".tab").forEach(s => s.classList.toggle("hidden", s.id !== name));
  document.querySelectorAll("#tabs button").forEach(b => b.classList.toggle("active", b.dataset.tab === name));
  loaders[name]().catch(e => toast(e.message, false));
}
$("#tabs").addEventListener("click", e => e.target.dataset.tab && show(e.target.dataset.tab));
$("#go-scorers").addEventListener("click", () => show("scorers"));

function wire(id, path, after) {
  $(id).addEventListener("submit", async e => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.target));
    try {
      const r = await api(path, "POST", data);
      toast(r.message || "Saved"); e.target.reset(); after && after();
    } catch (err) { toast(err.message, false); }   // shows trigger / SIGNAL messages
  });
}
const refresh = () => loaders.manage().catch(() => {});
wire("#f-match", "/api/matches", refresh);
wire("#f-player", "/api/players", refresh);
wire("#f-stats", "/api/player-stats");
wire("#f-team", "/api/teams", refresh);

show("standings");
