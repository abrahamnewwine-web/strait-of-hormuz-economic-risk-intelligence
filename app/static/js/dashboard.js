/* Strait of Hormuz Economic Risk Intelligence frontend controller */
Chart.defaults.animation = false;
Chart.defaults.color = "#93a4c3";
Chart.defaults.borderColor = "#233354";

const state = {
  scenario: "Normal",
  year: "",
  month: "",
  industry: "All",
  charts: {},
};

function fmtNum(val, unit) {
  if (unit && unit.startsWith("$")) return `$${Number(val).toFixed(2)}`;
  return Number(val).toFixed(1);
}

function bandClass(band) {
  if (band.includes("CRITICAL")) return "band-crit";
  if (band.includes("HIGH")) return "band-high";
  if (band.includes("ELEVATED")) return "band-elev";
  if (band.includes("MODERATE")) return "band-mod";
  return "band-low";
}

function bandColor(band) {
  if (band.includes("CRITICAL")) return "#ef4444";
  if (band.includes("HIGH")) return "#f97316";
  if (band.includes("ELEVATED")) return "#f59e0b";
  if (band.includes("MODERATE")) return "#38bdf8";
  return "#10b981";
}

async function init() {
  const res = await fetch("/api/filters");
  const opts = await res.json();

  const btnBox = document.getElementById("scenarioButtons");
  btnBox.innerHTML = opts.scenarios
    .map((s) => {
      const sev = s.risk_index >= 90 ? "sev-critical" : s.risk_index >= 75 ? "sev-high" : "";
      const active = s.scenario_name === state.scenario ? "active" : "";
      return `<button type="button" class="scen-btn ${sev} ${active}" data-scen="${s.scenario_name}">${s.scenario_name}</button>`;
    })
    .join("");

  btnBox.querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.scenario = btn.dataset.scen;
      btnBox.querySelectorAll("button").forEach((b) => b.classList.toggle("active", b === btn));
      loadDashboard();
    });
  });

  const ySel = document.getElementById("yearFilter");
  opts.years.forEach((y) => ySel.insertAdjacentHTML("beforeend", `<option value="${y}">${y}</option>`));

  const mSel = document.getElementById("monthFilter");
  opts.months.forEach((m) => mSel.insertAdjacentHTML("beforeend", `<option value="${m.month_num}">${m.month_name}</option>`));

  const iSel = document.getElementById("industryFilter");
  opts.industries.forEach((ind) => iSel.insertAdjacentHTML("beforeend", `<option value="${ind}">${ind}</option>`));

  ySel.addEventListener("change", () => { state.year = ySel.value; loadDashboard(); });
  mSel.addEventListener("change", () => { state.month = mSel.value; loadDashboard(); });
  iSel.addEventListener("change", () => { state.industry = iSel.value; loadDashboard(); });

  document.getElementById("resetBtn").addEventListener("click", () => {
    state.scenario = "Normal";
    state.year = "";
    state.month = "";
    state.industry = "All";
    ySel.value = "";
    mSel.value = "";
    iSel.value = "All";
    btnBox.querySelectorAll("button").forEach((b) => b.classList.toggle("active", b.dataset.scen === "Normal"));
    loadDashboard();
  });

  await loadDashboard();
}

async function loadDashboard() {
  const qs = new URLSearchParams({ scenario: state.scenario });
  if (state.year) qs.set("year", state.year);
  if (state.month) qs.set("month", state.month);
  if (state.industry && state.industry !== "All") qs.set("industry", state.industry);

  const exportQs = new URLSearchParams({ scenario: state.scenario });
  if (state.industry && state.industry !== "All") exportQs.set("industry", state.industry);
  document.getElementById("exportBtn").href = `/api/export/exposure.csv?${exportQs.toString()}`;

  const res = await fetch(`/api/dashboard?${qs.toString()}`);
  const data = await res.json();
  if (data.empty) return;

  renderHeader(data);
  renderHero(data);
  renderMacroCards(data);
  renderCharts(data);
  renderTable(data);
}

function renderHeader(data) {
  const badge = document.getElementById("modeBadge");
  if (data.is_stressed) {
    badge.className = "mode-badge stressed";
    badge.textContent = `Modeled Stress: ${data.active_scenario.scenario_name}`;
  } else {
    badge.className = "mode-badge baseline";
    badge.textContent = "Observed Historical Baseline";
  }
  document.getElementById("asOfBadge").textContent = `Period As Of ${data.as_of_period}`;
}

function renderHero(data) {
  const s = data.active_scenario;
  const pill = document.getElementById("riskBandBadge");
  pill.textContent = s.risk_band;
  pill.className = `risk-pill ${bandClass(s.risk_band)}`;

  document.getElementById("riskScore").textContent = s.risk_index;
  document.getElementById("flowShock").textContent = `${s.flow_disruption_pct.toFixed(1)}%`;
  document.getElementById("oilShock").textContent = `+${s.oil_shock_pct.toFixed(1)}%`;
  document.getElementById("freightShock").textContent = `+${s.freight_shock_pct.toFixed(1)}%`;
  document.getElementById("infShock").textContent = `+${s.inflation_pressure_pct.toFixed(1)}%`;
  document.getElementById("riskSummary").textContent = data.risk_summary;

  if (state.charts.gauge) state.charts.gauge.destroy();
  state.charts.gauge = new Chart(document.getElementById("riskGaugeChart"), {
    type: "doughnut",
    data: {
      datasets: [{
        data: [s.risk_index, 100 - s.risk_index],
        backgroundColor: [bandColor(s.risk_band), "#1f2d49"],
        borderWidth: 0,
      }],
    },
    options: {
      rotation: -90,
      circumference: 180,
      cutout: "74%",
      responsive: false,
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
    },
  });

  const c = data.chokepoint_stats;
  const tiles = [
    [`${c.barrels_per_day_millions}M bbl/d`, "Petroleum Transit Volume"],
    [`${c.global_oil_consumption_pct}%`, "Global Oil Consumption"],
    [`${c.global_seaborne_oil_pct}%`, "Global Seaborne Oil"],
    [`${c.global_lng_trade_pct}%`, "Global LNG Trade"],
    [`${c.asia_crude_share_pct}%`, "Exports Bound for Asia"],
    [`${c.saudi_crude_share_pct}%`, "Saudi Arabia Share"],
  ];
  document.getElementById("chokepointGrid").innerHTML = tiles
    .map(([v, l]) => `<div class="choke-tile"><div class="choke-val">${v}</div><div class="choke-lbl">${l}</div></div>`)
    .join("");
}

function renderMacroCards(data) {
  const order = ["brent", "wti", "diesel", "gasoline", "freight", "transport_cpi", "energy_cpi", "ppi"];
  document.getElementById("macroCards").innerHTML = order
    .map((key) => {
      const m = data.macro_cards[key];
      const shown = data.is_stressed ? m.modeled_value : m.observed_value;
      const yoyClass = m.yoy_delta_pct >= 0 ? "yoy-up" : "yoy-down";
      const yoySign = m.yoy_delta_pct >= 0 ? "+" : "";
      const subLeft = data.is_stressed
        ? `Obs: ${fmtNum(m.observed_value, m.unit)} ${m.unit}`
        : `Observed Baseline`;
      return `
        <article class="macro-card">
          <div class="macro-title">${m.label}</div>
          <div class="macro-val-row">
            <span class="macro-val">${fmtNum(shown, m.unit)}</span>
            <span class="macro-unit">${m.unit}</span>
          </div>
          <div class="macro-sub">
            <span>${subLeft}</span>
            <span class="${yoyClass}">12M YoY ${yoySign}${m.yoy_delta_pct}%</span>
          </div>
        </article>`;
    })
    .join("");
}

function renderCharts(data) {
  const series = data.macro_series.slice(-36);
  const labels = series.map((r) => r.year_month);
  const brent = series.map((r) => r.brent_usd);
  const wti = series.map((r) => r.wti_usd);
  const oilLabels = data.is_stressed ? [...labels, "Stress Target"] : labels;
  const brentPlot = data.is_stressed ? [...brent, data.macro_cards.brent.modeled_value] : brent;
  const wtiPlot = data.is_stressed ? [...wti, data.macro_cards.wti.modeled_value] : wti;

  if (state.charts.oil) state.charts.oil.destroy();
  state.charts.oil = new Chart(document.getElementById("oilChart"), {
    type: "line",
    data: {
      labels: oilLabels,
      datasets: [
        { label: "Brent Crude ($/bbl)", data: brentPlot, borderColor: "#38bdf8", backgroundColor: "rgba(56,189,248,0.12)", tension: 0.25, pointRadius: 2 },
        { label: "WTI Crude ($/bbl)", data: wtiPlot, borderColor: "#f59e0b", backgroundColor: "rgba(245,158,11,0.08)", tension: 0.25, pointRadius: 2 },
      ],
    },
    options: { maintainAspectRatio: false, plugins: { legend: { position: "top" } } },
  });

  if (state.charts.matrix) state.charts.matrix.destroy();
  const scens = data.all_scenarios;
  state.charts.matrix = new Chart(document.getElementById("scenarioMatrixChart"), {
    type: "bar",
    data: {
      labels: scens.map((s) => s.scenario_name),
      datasets: [
        { label: "Flow Disruption %", data: scens.map((s) => s.flow_disruption_pct), backgroundColor: "#38bdf8" },
        { label: "Oil Shock %", data: scens.map((s) => s.oil_shock_pct), backgroundColor: "#ef4444" },
        { label: "Freight Shock %", data: scens.map((s) => s.freight_shock_pct), backgroundColor: "#f59e0b" },
      ],
    },
    options: { maintainAspectRatio: false, plugins: { legend: { position: "top" } } },
  });

  if (state.charts.inf) state.charts.inf.destroy();
  state.charts.inf = new Chart(document.getElementById("inflationChart"), {
    type: "line",
    data: {
      labels,
      datasets: [
        { label: "Freight Index", data: series.map((r) => r.freight_index), borderColor: "#a78bfa", tension: 0.25, pointRadius: 1.5 },
        { label: "Transportation CPI", data: series.map((r) => r.transportation_cpi), borderColor: "#34d399", tension: 0.25, pointRadius: 1.5 },
        { label: "Energy CPI", data: series.map((r) => r.energy_cpi), borderColor: "#fb7185", tension: 0.25, pointRadius: 1.5 },
      ],
    },
    options: { maintainAspectRatio: false, plugins: { legend: { position: "top" } } },
  });

  if (state.charts.corp) state.charts.corp.destroy();
  const corp = data.corporate_exposure;
  state.charts.corp = new Chart(document.getElementById("companyImpactChart"), {
    type: "bar",
    data: {
      labels: corp.map((c) => `${c.ticker} (${c.industry})`),
      datasets: [{
        label: "Modeled Equity Impact (%)",
        data: corp.map((c) => c.modeled_scenario_impact_pct),
        backgroundColor: corp.map((c) => (c.modeled_scenario_impact_pct >= 0 ? "#10b981" : "#ef4444")),
      }],
    },
    options: {
      indexAxis: "y",
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { title: { display: true, text: "Estimated Stress Impact (%)" } } },
    },
  });
}

function renderTable(data) {
  const tbody = document.getElementById("exposureTableBody");
  tbody.innerHTML = data.corporate_exposure
    .map((r) => {
      const tierCls = r.impact_tier === "Very High" ? "tier-vh" : r.impact_tier === "High" ? "tier-h" : "tier-m";
      const retCls = r.return_1m_pct >= 0 ? "pos" : "neg";
      const modCls = r.modeled_scenario_impact_pct >= 0 ? "pos" : "neg";
      const retSign = r.return_1m_pct >= 0 ? "+" : "";
      const modSign = r.modeled_scenario_impact_pct >= 0 ? "+" : "";
      return `
        <tr>
          <td><strong>${r.ticker}</strong></td>
          <td>${r.company_name}</td>
          <td>${r.industry}</td>
          <td><span class="tier-badge ${tierCls}">${r.impact_tier}</span></td>
          <td class="num">${r.base_exposure_score}/100</td>
          <td class="num">$${r.latest_close_usd.toFixed(2)}</td>
          <td class="num ${retCls}">${retSign}${r.return_1m_pct.toFixed(2)}%</td>
          <td class="num ${modCls}">${modSign}${r.modeled_scenario_impact_pct.toFixed(2)}%</td>
        </tr>`;
    })
    .join("");
}

init();
