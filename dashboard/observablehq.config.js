export default {
  title: "Dunkelflaute Radar",
  root: "src",
  theme: "near-midnight",
  sidebar: false,
  pager: false,
  header: "",
  footer: "",
  // Python loaders run in the repo's uv environment (duckdb lives there).
  interpreters: {".py": ["uv", "run", "python"]}
};
