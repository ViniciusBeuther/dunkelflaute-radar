---
toc: false
---

```js
import * as topojson from "npm:topojson-client";

const capacity = await FileAttachment("data/capacity.json").json();
const world = await FileAttachment("data/countries-50m.json").json();
const insights = await FileAttachment("data/insights.json").json();

const germany = topojson.feature(world, world.objects.countries).features.find((d) => d.properties.name === "Germany");
const borders = topojson.mesh(world, world.objects.countries, (a, b) => a !== b);

const gw = (mw) => mw / 1000;
const fmt1 = d3.format(".1f");
const fmt0 = d3.format(".0f");
const pct = d3.format(".0%");

const colors = {
  Wind: "#6fd3ff",
  Solar: "#ffc247",
  Gas: "#c792ea",
  "Brown coal": "#a07a52",
  "Hard coal": "#8b93a1"
};
const ramps = {
  wind_mw: d3.interpolateRgb("#0d1b2a", colors.Wind),
  solar_mw: d3.interpolateRgb("#2a1706", colors.Solar)
};

// Share of a capacity column that sits north of a latitude.
const northShare = (key, lat = 51.5) =>
  d3.sum(capacity.filter((d) => d.lat >= lat), (d) => d[key]) / d3.sum(capacity, (d) => d[key]);

function capacityMap(key, id) {
  const w = 520, h = 640, ramp = ramps[key];
  const points = capacity.filter((d) => d[key] > 0);
  const proj = d3.geoMercator().fitExtent([[10, 10], [w - 10, h - 10]], germany);
  const path = d3.geoPath(proj);
  const svg = d3.create("svg").attr("viewBox", [0, 0, w, h]).style("max-width", "100%").style("height", "auto");

  svg.append("clipPath").attr("id", id).append("path").attr("d", path(germany));
  svg.append("path").attr("d", path(borders)).attr("fill", "none").attr("stroke", "var(--theme-foreground-faintest)");
  svg.append("path").attr("d", path(germany)).attr("fill", ramp(0));

  const surface = d3.contourDensity()
    .x((d) => proj([d.lon, d.lat])[0])
    .y((d) => proj([d.lon, d.lat])[1])
    .weight((d) => d[key])
    .size([w, h])
    .bandwidth(24);
  const top = d3.max(surface.thresholds(40)(points), (d) => d.value);
  // Cap the color scale below the peak so one hotspot does not wash out the rest.
  const cap = top * 0.65;
  const color = d3.scaleSequential(ramp).domain([0, cap]).clamp(true);
  const levels = surface.thresholds(d3.range(1, 19).map((i) => (cap * i) / 18))(points);

  svg.append("g").attr("clip-path", `url(#${id})`)
    .selectAll("path").data(levels).join("path")
    .attr("d", d3.geoPath()).attr("fill", (d) => color(d.value));
  svg.append("path").attr("d", path(germany)).attr("fill", "none")
    .attr("stroke", "var(--theme-foreground-muted)").attr("stroke-width", 1.2);

  return html`<div class="card">
    ${svg.node()}
    <div style="display:flex;align-items:center;gap:8px;font-size:12px;color:var(--theme-foreground-muted);margin-top:8px">
      <span>Less capacity</span>
      <span style="flex:0 0 160px;height:8px;border-radius:4px;background:linear-gradient(to right, ${ramp(0)}, ${ramp(1)})"></span>
      <span>More capacity</span>
    </div>
    <p class="muted" style="font-size:12px;margin:8px 0 0">Smoothed from a 0.5° grid of capacity-weighted points. Source: Marktstammdatenregister.</p>
  </div>`;
}

const bigStat = (value, label) => html`<div style="margin:0 0 1.4rem">
  <div style="font-family:var(--serif);font-size:3rem;line-height:1.05">${value}</div>
  <div class="muted" style="max-width:34ch">${label}</div>
</div>`;

const s = insights.summary;
const hour = (h) => insights.by_hour.find((d) => d.hour_of_day === h);
const weakest = insights.by_decile[0];
const strongest = insights.by_decile.at(-1);
const months = insights.by_month;
const monthName = (m) => d3.utcFormat("%B")(d3.utcParse("%Y-%m")(m));
const dayLabel = (d) => d3.utcFormat("%b %-d")(d3.utcParse("%Y-%m-%d")(d));
```

<style>
  .lede { font-size: 1.25rem; max-width: 52ch; color: var(--theme-foreground-muted); }
  .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); gap: 1.5rem; margin: 2rem 0 3rem; }
  .section-head { margin-top: 3.5rem; }
  .section-head h2 { font-size: 1.9rem; margin-bottom: 0.2rem; }
  .split { display: grid; grid-template-columns: repeat(auto-fit, minmax(20rem, 1fr)); gap: 2rem; align-items: center; }
</style>

# Dunkelflaute Radar

<p class="lede">What ${s.n_days} days of German wind, solar and fossil generation say about a grid that depends on the weather.</p>

<div class="stats">
  ${bigStat(fmt1(gw(insights.lowest_day.renewables)) + " GW", html`Lowest day for wind + solar combined, on ${dayLabel(insights.lowest_day.day)}.`)}
  ${bigStat((weakest.fossil / strongest.fossil).toFixed(1) + "×", "More fossil power on the weakest renewable days than on the strongest.")}
  ${bigStat(fmt0(s.max_wind / s.min_wind) + "×", "Gap between Germany's calmest and windiest day for wind output.")}
</div>

*Dunkelflaute* ("dark doldrum") is a stretch of days with almost no wind and little sun. Here is where Germany's renewable capacity sits, and what the grid does when the weather lets it down.

<div class="section-head">

## Wind: strong, but mostly in the north

</div>

<div class="split">
  ${capacityMap("wind_mw", "clip-wind")}
  <div>
    ${bigStat(pct(northShare("wind_mw")), "of installed wind capacity sits north of 51.5°N, roughly north of Göttingen.")}
    ${bigStat(fmt0(gw(d3.sum(capacity, (d) => d.wind_mw))) + " GW", "installed in total.")}
    <p class="muted">Daily average wind output ranged from ${fmt1(gw(s.min_wind))} GW to ${fmt1(gw(s.max_wind))} GW. When a calm settles over the north, there is little the rest of the country can do about it.</p>
  </div>
</div>

<div class="section-head">

## Solar: the south, and only by day

</div>

<div class="split">
  <div>
    ${bigStat(fmt0(gw(hour(11).solar)) + " GW", "average solar output at 11:00 UTC, its midday peak.")}
    ${bigStat(fmt0(gw(d3.sum(capacity, (d) => d.solar_mw))) + " GW", "installed in total, " + pct(1 - northShare("solar_mw")) + " of it south of 51.5°N.")}
    <p class="muted">By 20:00 UTC solar output is about zero. Whatever the weather, the sun does not cover the evening.</p>
  </div>
  ${capacityMap("solar_mw", "clip-solar")}
</div>

<div class="section-head">

## A day on the grid

Average generation by hour of day across ${s.n_days} days. Hours are UTC; Germany is one to two hours ahead.

</div>

<div class="card">

```js
const hourRows = insights.by_hour.flatMap((d) => [
  {hour: d.hour_of_day, source: "Wind", gw: gw(d.wind)},
  {hour: d.hour_of_day, source: "Solar", gw: gw(d.solar)},
  {hour: d.hour_of_day, source: "Hard coal", gw: gw(d.hard_coal)},
  {hour: d.hour_of_day, source: "Brown coal", gw: gw(d.lignite)},
  {hour: d.hour_of_day, source: "Gas", gw: gw(d.gas)}
]);
display(resize((width) => Plot.plot({
  width,
  height: 380,
  marginLeft: 44,
  x: {label: "Hour of day (UTC)", tickFormat: (h) => `${h}:00`, ticks: 8},
  y: {label: "Average generation (GW)", grid: true},
  color: {legend: true, domain: Object.keys(colors), range: Object.values(colors)},
  marks: [
    Plot.areaY(hourRows, {x: "hour", y: "gw", fill: "source", order: ["Wind", "Solar", "Hard coal", "Brown coal", "Gas"], curve: "monotone-x", tip: {format: {x: (h) => `${h}:00`}}}),
    Plot.ruleY([0])
  ]
})));
```

</div>

Gas steps in as the sun sets: it averages ${fmt1(gw(hour(11).gas))} GW at 11:00 and ${fmt1(gw(hour(18).gas))} GW at 18:00, ${(hour(18).gas / hour(11).gas).toFixed(1)}× as much. Wind barely changes through the day, so it cannot take over that evening shift.

<div class="section-head">

## When renewables fall, fossil fills the gap

Every day grouped into ten tiers by wind + solar output. The weakest tier is on the left.

</div>

<div class="card">

```js
const tierRows = insights.by_decile.flatMap((d) => [
  {tier: `${fmt0(gw(d.renewables))} GW`, source: "Hard coal", gw: gw(d.hard_coal)},
  {tier: `${fmt0(gw(d.renewables))} GW`, source: "Brown coal", gw: gw(d.lignite)},
  {tier: `${fmt0(gw(d.renewables))} GW`, source: "Gas", gw: gw(d.gas)}
]);
const fossilColors = ["Hard coal", "Brown coal", "Gas"];
display(resize((width) => Plot.plot({
  width,
  height: 380,
  marginLeft: 44,
  x: {label: "Average wind + solar output of the tier", domain: insights.by_decile.map((d) => `${fmt0(gw(d.renewables))} GW`)},
  y: {label: "Average fossil generation (GW)", grid: true},
  color: {legend: true, domain: fossilColors, range: fossilColors.map((k) => colors[k])},
  marks: [
    Plot.barY(tierRows, {x: "tier", y: "gw", fill: "source", order: fossilColors, tip: true}),
    Plot.ruleY([0])
  ]
})));
```

</div>

On the ten weakest-renewable days, fossil plants average ${fmt1(gw(weakest.fossil))} GW. On the ten strongest it is ${fmt1(gw(strongest.fossil))} GW. Gas more than doubles, from ${fmt1(gw(strongest.gas))} GW to ${fmt1(gw(weakest.gas))} GW, and brown coal rises from ${fmt1(gw(strongest.lignite))} GW to ${fmt1(gw(weakest.lignite))} GW.

<div class="section-head">

## Summer is ending

Monthly average generation. ${monthName(months.at(-1).month)} covers only ${months.at(-1).n_days} days so far.

</div>

<div class="card">

```js
const monthRows = months.flatMap((m) => [
  {month: monthName(m.month), source: "Solar", gw: gw(m.solar)},
  {month: monthName(m.month), source: "Wind", gw: gw(m.wind)},
  {month: monthName(m.month), source: "Fossil", gw: gw(m.fossil)}
]);
const monthColors = {Solar: colors.Solar, Wind: colors.Wind, Fossil: "#8b93a1"};
display(resize((width) => Plot.plot({
  width,
  height: 360,
  marginLeft: 44,
  fx: {label: null, domain: months.map((m) => monthName(m.month))},
  x: {axis: null, domain: Object.keys(monthColors)},
  y: {label: "Average generation (GW)", grid: true},
  color: {legend: true, domain: Object.keys(monthColors), range: Object.values(monthColors)},
  marks: [
    Plot.barY(monthRows, {fx: "month", x: "source", y: "gw", fill: "source", tip: true}),
    Plot.ruleY([0])
  ]
})));
```

</div>

From ${monthName(months[0].month)} to early ${monthName(months.at(-1).month)}, average solar output fell ${pct(1 - months.at(-1).solar / months[0].solar)} and fossil generation rose ${pct(months.at(-1).fossil / months[0].fossil - 1)}. The five weakest days in the data are all in autumn. True Dunkelflaute season is winter, and this window ends before it starts.

<div class="section-head">

## About this data

</div>

<p class="muted" style="max-width:70ch">Generation figures come from the ENTSO-E Transparency Platform for the DE-LU bidding zone, ${dayLabel(s.first_day)} to ${dayLabel(s.last_day)}, 2026. Installed capacity comes from the German Marktstammdatenregister, spread over a 0.5° grid. "Fossil" is gas, brown coal (lignite) and hard coal. The window contains no winter Dunkelflaute, so these charts describe how the grid behaves as autumn begins, not a detected event. Built with Python, Airflow, dbt, DuckDB and Observable Framework.</p>
