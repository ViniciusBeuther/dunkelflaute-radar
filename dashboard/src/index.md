---
toc: false
---

<style>
#observablehq-main, #observablehq-center { max-width: none; margin: 0; padding: 0; }
#observablehq-main { padding: 14px 18px 18px; }
.dash { font-family: var(--sans-serif); display: grid; gap: 14px; min-height: calc(100vh - 32px);
  grid-template-columns: minmax(320px, 0.82fr) minmax(0, 1fr) minmax(0, 1fr);
  grid-template-rows: auto auto minmax(300px, 1fr) minmax(300px, 1fr);
  grid-template-areas: "bar bar bar" "kpi kpi kpi" "map donut mix" "map days days"; }
.dash > * { min-width: 0; }
@media (max-width: 1000px) { .dash { grid-template-columns: minmax(0, 1fr); grid-template-rows: auto;
  grid-template-areas: "bar" "kpi" "map" "donut" "mix" "days"; } }
.topbar { grid-area: bar; display: flex; flex-wrap: wrap; align-items: center; gap: 10px 22px; padding: 10px 16px;
  border: 1px solid var(--theme-foreground-faintest); border-radius: 10px; background: var(--theme-background-alt); }
.topbar h1 { margin: 0 auto 0 0; font-family: var(--sans-serif); font-size: 1.1rem; font-weight: 700; letter-spacing: 0.01em; }
.topbar h1 span { font-weight: 400; color: var(--theme-foreground-muted); }
.group { display: flex; align-items: center; gap: 8px; font-size: 12px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--theme-foreground-muted); }
.seg { display: inline-flex; border: 1px solid var(--theme-foreground-faintest); border-radius: 8px; overflow: hidden; }
.seg button { all: unset; cursor: pointer; padding: 6px 18px; font-size: 13px; text-transform: none; letter-spacing: 0; color: var(--theme-foreground-muted); }
.seg button.on { background: var(--theme-foreground-focus); color: #0b0f14; font-weight: 600; }
.seg button:hover:not(.on) { background: var(--theme-background); }
.topbar select { font: inherit; font-size: 13px; padding: 5px 10px; border-radius: 8px; background: var(--theme-background); color: var(--theme-foreground); border: 1px solid var(--theme-foreground-faintest); }
.btn-reset { all: unset; cursor: pointer; font-size: 13px; padding: 5px 12px; border-radius: 8px; color: var(--theme-foreground); border: 1px solid var(--theme-foreground-faintest); text-transform: none; letter-spacing: 0; }
.btn-reset:hover { background: var(--theme-background); }
.kpis { grid-area: kpi; display: grid; grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr)); gap: 14px; }
.kpi { border: 1px solid var(--theme-foreground-faintest); border-radius: 10px; background: var(--theme-background-alt); padding: 12px 16px; }
.kpi .label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--theme-foreground-muted); }
.kpi .value { margin-top: 2px; font-size: 2rem; font-weight: 600; line-height: 1.15; font-variant-numeric: tabular-nums; }
.kpi .value small { font-size: 0.85rem; font-weight: 400; color: var(--theme-foreground-muted); margin-left: 4px; }
.kpi .sub { font-size: 12px; color: var(--theme-foreground-muted); }
.panel { display: flex; flex-direction: column; border: 1px solid var(--theme-foreground-faintest); border-radius: 10px; background: var(--theme-background-alt); padding: 0 16px 14px; min-height: 0; }
.panel-h { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; padding: 12px 0 9px; margin-bottom: 10px; border-bottom: 1px solid var(--theme-foreground-faintest); }
.panel-h h2 { margin: 0; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; }
.panel-h .hint { font-size: 12px; color: var(--theme-foreground-muted); text-align: right; }
.panel figure { margin: 0; }
.map-wrap { display: flex; flex-direction: column; align-items: center; gap: 10px; }
.legend-bar { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--theme-foreground-muted); }
.legend-bar i { flex: 0 0 140px; height: 8px; border-radius: 4px; }
.donut-wrap { display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 12px 20px; }
.mix-list { display: grid; grid-template-columns: auto 1fr auto auto; gap: 5px 10px; font-size: 13px; align-items: center; font-variant-numeric: tabular-nums; }
.mix-list i { width: 10px; height: 10px; border-radius: 2px; }
.mix-list .m { color: var(--theme-foreground-muted); }
#p-map { grid-area: map; } #p-donut { grid-area: donut; } #p-mix { grid-area: mix; } #p-days { grid-area: days; }
</style>

```js
const dailyMix = await FileAttachment("data/daily_mix.json").json();
const weather = await FileAttachment("data/weather_daily.json").json();
const world = await FileAttachment("data/countries-50m.json").json();
const topojson = await import("npm:topojson-client");

const germany = topojson.feature(world, world.objects.countries).features.find((d) => d.properties.name === "Germany");
const borders = topojson.mesh(world, world.objects.countries, (a, b) => a !== b);

const SOURCES = ["Wind", "Solar", "Other", "Hard coal", "Brown coal", "Gas"];
const COLORS = {Wind: "#6fd3ff", Solar: "#ffc247", Other: "#5b6b82", "Hard coal": "#8b93a1", "Brown coal": "#a07a52", Gas: "#c792ea"};
const KEY = {Wind: "wind", Solar: "solar", Other: "other", "Hard coal": "hard_coal", "Brown coal": "lignite", Gas: "gas"};

const parseDay = d3.utcParse("%Y-%m-%d");
const days = dailyMix.map((d) => ({...d, date: parseDay(d.day), month: d.day.slice(0, 7)}));
const months = [...new Set(days.map((d) => d.month))];
const monthShort = (m) => d3.utcFormat("%b")(d3.utcParse("%Y-%m")(m));
const monthLabel = (m) => d3.utcFormat("%b %Y")(d3.utcParse("%Y-%m")(m));
const dayLabel = (d) => d3.utcFormat("%b %-d")(parseDay(d));
const gw = (mw) => mw / 1000;
const total = (d) => d3.sum(SOURCES, (s) => d[KEY[s]]);
```

```js
// Shared filter state. Every panel reads `selection`; clicks call `select`.
const selection = Mutable({metric: "Wind", month: null, day: null});
const select = (patch) => { selection.value = {...selection.value, ...patch}; };
const resetSelection = () => { selection.value = {...selection.value, month: null, day: null}; };
```

```js
const filtered = selection.day
  ? days.filter((d) => d.day === selection.day)
  : selection.month
    ? days.filter((d) => d.month === selection.month)
    : days;
const periodLabel = selection.day ? dayLabel(selection.day) : selection.month ? monthLabel(selection.month) : `All ${days.length} days`;
const inPeriod = (d) => filtered.includes(d);
const activeMonth = selection.day ? selection.day.slice(0, 7) : selection.month;
const panel = (id, title, hint, ...body) => html`<section class="panel" id=${id}>
  <div class="panel-h"><h2>${title}</h2><span class="hint">${hint}</span></div>${body}</section>`;
```

```js
const topbar = html`<div class="topbar">
  <h1>Dunkelflaute Radar <span>· Germany</span></h1>
  <div class="group">Map
    <div class="seg">${["Wind", "Solar"].map((m) => html`<button class=${selection.metric === m ? "on" : ""} onclick=${() => select({metric: m})}>${m}</button>`)}</div>
  </div>
  <div class="group">Period
    <select onchange=${(e) => select({month: e.target.value || null, day: null})}>
      <option value="" selected=${!selection.month && !selection.day}>All days</option>
      ${months.map((m) => html`<option value=${m} selected=${selection.month === m}>${monthLabel(m)}</option>`)}
    </select>
    <button class="btn-reset" onclick=${resetSelection}>Reset</button>
  </div>
</div>`;

const windSolarShare = d3.sum(filtered, (d) => d.wind + d.solar) / d3.sum(filtered, total);
const fossilAvg = d3.mean(filtered, (d) => d.gas + d.lignite + d.hard_coal);
const lowest = d3.least(filtered, (d) => d.wind + d.solar);

const kpis = html`<div class="kpis">
  <div class="kpi"><div class="label">Wind + solar share</div>
    <div class="value">${d3.format(".0%")(windSolarShare)}</div><div class="sub">of generation · ${periodLabel}</div></div>
  <div class="kpi"><div class="label">Average fossil output</div>
    <div class="value">${d3.format(".1f")(gw(fossilAvg))}<small>GW</small></div><div class="sub">gas + brown coal + hard coal</div></div>
  <div class="kpi"><div class="label">Lowest wind + solar day</div>
    <div class="value">${d3.format(".1f")(gw(lowest.wind + lowest.solar))}<small>GW</small></div><div class="sub">${dayLabel(lowest.day)}</div></div>
  <div class="kpi"><div class="label">Days in view</div>
    <div class="value">${filtered.length}</div><div class="sub">of ${days.length} analysed</div></div>
</div>`;
```

```js
// Weather map: average of the chosen weather variable over the selected days at each
// of the 293 grid points, interpolated to a smooth surface (Gaussian-weighted average).
const mapView = (() => {
  const W = 440, H = 560, STEP = 5, SIGMA = 26;
  const key = selection.metric === "Wind" ? "wind" : "solar";
  const unit = key === "wind" ? "km/h" : "W/m²";
  const ramp = key === "wind" ? d3.interpolateRgb("#0d1b2a", "#6fd3ff") : d3.interpolateRgb("#2a1706", "#ffc247");
  const idx = filtered.map((d) => weather.days.indexOf(d.day)).filter((i) => i >= 0);
  const proj = d3.geoMercator().fitExtent([[10, 10], [W - 10, H - 10]], germany);
  const path = d3.geoPath(proj);
  const pts = weather.points.map((p) => {
    const [x, y] = proj([p.lon, p.lat]);
    return {x, y, v: d3.mean(idx, (i) => p[key][i]), inside: d3.geoContains(germany, [p.lon, p.lat])};
  });
  const [lo, hi] = d3.extent(pts.filter((p) => p.inside), (p) => p.v);

  const nx = Math.ceil(W / STEP), ny = Math.ceil(H / STEP), s2 = 2 * SIGMA * SIGMA;
  const grid = new Float64Array(nx * ny);
  for (let j = 0; j < ny; j++) {
    for (let i = 0; i < nx; i++) {
      const gx = (i + 0.5) * STEP, gy = (j + 0.5) * STEP;
      let num = 0, den = 0;
      for (const p of pts) {
        const w = Math.exp(-((p.x - gx) ** 2 + (p.y - gy) ** 2) / s2);
        num += w * p.v; den += w;
      }
      grid[j * nx + i] = num / den;
    }
  }
  const levels = d3.range(14).map((i) => lo + ((hi - lo) * i) / 13);
  const color = d3.scaleSequential(ramp).domain([lo, hi]).clamp(true);
  const contours = d3.contours().size([nx, ny]).thresholds(levels)(grid);
  const toPx = d3.geoPath(d3.geoIdentity().scale(STEP));

  const svg = d3.create("svg").attr("viewBox", [0, 0, W, H]).style("width", "100%").style("max-height", "60vh").style("height", "auto");
  svg.append("clipPath").attr("id", "clip-de").append("path").attr("d", path(germany));
  svg.append("path").attr("d", path(borders)).attr("fill", "none").attr("stroke", "var(--theme-foreground-faintest)");
  svg.append("path").attr("d", path(germany)).attr("fill", ramp(0));
  svg.append("g").attr("clip-path", "url(#clip-de)").selectAll("path").data(contours).join("path")
    .attr("d", toPx).attr("fill", (d) => color(d.value));
  svg.append("path").attr("d", path(germany)).attr("fill", "none").attr("stroke", "var(--theme-foreground-muted)").attr("stroke-width", 1.2);

  const fmt = d3.format(".0f");
  return panel("p-map",
    key === "wind" ? "Average wind speed" : "Average solar radiation",
    `${key === "wind" ? "80 m wind speed" : "shortwave radiation"} · ${periodLabel}`,
    html`<div class="map-wrap">${svg.node()}
      <div class="legend-bar"><span>${fmt(lo)} ${unit}</span><i style="background:linear-gradient(to right, ${ramp(0)}, ${ramp(1)})"></i><span>${fmt(hi)} ${unit}</span></div>
    </div>`);
})();
```

```js
const mixTotals = SOURCES.map((s) => ({source: s, mw: d3.mean(filtered, (d) => d[KEY[s]])}));
const mixSum = d3.sum(mixTotals, (d) => d.mw);

const donutView = (() => {
  const size = 210, r = size / 2 - 4;
  const arcs = d3.pie().sort(null).value((d) => d.mw).padAngle(0.015)(mixTotals);
  const arc = d3.arc().innerRadius(r * 0.64).outerRadius(r).cornerRadius(2);
  const svg = d3.create("svg").attr("viewBox", [-size / 2, -size / 2, size, size]).attr("width", size).attr("height", size);
  svg.selectAll("path").data(arcs).join("path").attr("d", arc).attr("fill", (d) => COLORS[d.data.source])
    .append("title").text((d) => `${d.data.source}: ${d3.format(".1f")(gw(d.data.mw))} GW`);
  svg.append("text").attr("text-anchor", "middle").attr("y", -2).style("fill", "var(--theme-foreground)")
    .style("font-size", "26px").style("font-weight", "600").text(d3.format(".1f")(gw(mixSum)));
  svg.append("text").attr("text-anchor", "middle").attr("y", 18).style("fill", "var(--theme-foreground-muted)")
    .style("font-size", "11px").text("GW average");
  const list = html`<div class="mix-list">${mixTotals.flatMap((d) => [
    html`<i style="background:${COLORS[d.source]}"></i>`,
    html`<span>${d.source}</span>`,
    html`<b>${d3.format(".0%")(d.mw / mixSum)}</b>`,
    html`<span class="m">${d3.format(".1f")(gw(d.mw))} GW</span>`
  ])}</div>`;
  return panel("p-donut", "Generation mix", periodLabel, html`<div class="donut-wrap">${svg.node()}${list}</div>`);
})();
```

```js
const mixChart = resize((width) => {
  const labelOf = (m) => (days.filter((d) => d.month === m).length < 28 ? `${monthShort(m)} (${days.filter((d) => d.month === m).length}d)` : monthShort(m));
  const monthByLabel = new Map(months.map((m) => [labelOf(m), m]));
  const rows = months.flatMap((m) => {
    const ds = days.filter((d) => d.month === m);
    const sum = d3.sum(ds, total) / ds.length;
    return SOURCES.map((s) => {
      const mw = d3.mean(ds, (d) => d[KEY[s]]);
      return {label: labelOf(m), month: m, source: s, mw, share: mw / sum};
    });
  });
  const chart = Plot.plot({
    width, height: 270, marginLeft: 64, marginBottom: 40,
    x: {percent: true, label: "% of generation", grid: true},
    y: {label: null, domain: months.map(labelOf)},
    color: {domain: SOURCES, range: SOURCES.map((s) => COLORS[s])},
    marks: [
      Plot.barX(rows, {y: "label", x: "mw", fill: "source", order: SOURCES, offset: "normalize",
        fillOpacity: (d) => (!activeMonth || d.month === activeMonth ? 1 : 0.3), inset: 0.5,
        title: (d) => `${labelOf(d.month)} · ${d.source}\n${d3.format(".0%")(d.share)} (${d3.format(".1f")(gw(d.mw))} GW)`, tip: true}),
      Plot.ruleX([0])
    ]
  });
  // Click a row to filter by month (Plot has no click hook, so map the pointer to a band).
  chart.addEventListener("click", (event) => {
    const y = chart.scale("y");
    const py = d3.pointer(event, chart)[1];
    const label = y.domain.find((l) => py >= y.apply(l) && py < y.apply(l) + y.step);
    if (label) select({month: monthByLabel.get(label), day: null});
  });
  chart.style.cursor = "pointer";
  return chart;
});
const mixView = panel("p-mix", "Mix by month", "click a month to filter", mixChart);
```

```js
const dayRows = days.flatMap((d) => SOURCES.map((s) => ({date: d.date, day: d.day, source: s, gw: gw(d[KEY[s]])})));
const dayByKey = new Map(days.map((d) => [d.day, d]));

const dayChart = resize((width) => {
  const chart = Plot.plot({
    width, height: 210, marginLeft: 40,
    x: {label: null},
    y: {label: "GW", grid: true},
    color: {legend: true, domain: SOURCES, range: SOURCES.map((s) => COLORS[s])},
    marks: [
      Plot.rectY(dayRows, {x: "date", interval: "day", y: "gw", fill: "source", order: SOURCES,
        fillOpacity: (d) => (inPeriod(dayByKey.get(d.day)) ? 1 : 0.28),
        tip: {format: {x: (d) => d3.utcFormat("%b %-d")(d), fillOpacity: false}}}),
      Plot.ruleY([0])
    ]
  });
  // Click a bar to select that day (invert the x position back to a date).
  chart.addEventListener("click", (event) => {
    const t = chart.scale("x").invert(d3.pointer(event, chart)[0]);
    if (!t) return;
    const day = d3.utcFormat("%Y-%m-%d")(d3.utcDay.floor(t));
    if (dayByKey.has(day)) select({day, month: null});
  });
  chart.style.cursor = "pointer";
  return chart;
});
const daysView = panel("p-days", "Generation by day", "click a bar to filter the whole dashboard", dayChart);
```

<div class="dash">
  ${topbar}
  ${kpis}
  ${mapView}
  ${donutView}
  ${mixView}
  ${daysView}
</div>
