import { useEffect, useState } from "react";
import { cancelScan, getAppInfo, listenToScanProgress, moveToTrash, revealInFinder, scanFiles, type ScanItem, type ScanResponse } from "./lib/tauri";
import { profileFilters, scanProfiles, type ScanProfile } from "./features/scan/scanProfiles";

type AppInfo = { name: string; version: string };
type CustomFilters = { minSizeMb: number; minAgeDays: number; topN: number };

function describeError(error: unknown): string {
  if (typeof error === "string") return error;
  if (error instanceof Error) return error.message;
  if (error && typeof error === "object") {
    try {
      return JSON.stringify(error);
    } catch {
      return "Onbekende scanfout (niet serialiseerbaar object).";
    }
  }
  return `Onbekende scanfout: ${String(error)}`;
}

export function App() {
  const [profile, setProfile] = useState<ScanProfile>("custom");
  const [filters, setFilters] = useState<CustomFilters>({ ...profileFilters.custom, topN: 100 });
  const [scanning, setScanning] = useState(false);
  const [status, setStatus] = useState("Klaar voor een veilige scan.");
  const [results, setResults] = useState<ScanItem[]>([]);
  const [scanResponse, setScanResponse] = useState<ScanResponse | null>(null);
  const [query, setQuery] = useState("");
  const [selectedPaths, setSelectedPaths] = useState<Set<string>>(new Set());
  const [deleting, setDeleting] = useState(false);
  const [appInfo, setAppInfo] = useState<AppInfo>({ name: "Safe Mac Cleaner", version: "3.0.0-alpha.2" });

  useEffect(() => {
    getAppInfo().then(setAppInfo).catch(() => undefined);
    const unlisten = listenToScanProgress(({ path, inspected_files }) => {
      setStatus(`Onderzocht: ${inspected_files} bestanden · ${path}`);
    });
    return () => { void unlisten.then((cleanup) => cleanup()); };
  }, []);

  async function startScan() {
    setScanning(true);
    setStatus("Lokale mappen worden onderzocht...");
    try {
      const response = await scanFiles(filters);
      setScanResponse(response);
      setResults(response.results);
      setSelectedPaths(new Set());
      if (response.stats.cancelled) {
        setStatus(`Scan geannuleerd na ${response.stats.inspected_files} onderzochte bestanden.`);
      } else if (response.results.length > 0) {
        setStatus(`${response.results.length} geschikte bestanden gevonden.`);
      } else {
        setStatus(`Geen bestanden gevonden. ${response.stats.inspected_files} bestanden onderzocht.`);
      }
    } catch (error) {
      const message = describeError(error);
      console.error("Safe Mac Cleaner v3 scan failed", error);
      setStatus("Scan mislukt.");
      setScanResponse({
        results: [],
        errors: [message],
        stats: { inspected_files: 0, candidates: 0, skipped_age: 0, skipped_size: 0, skipped_packages: 0, permission_errors: 0, cancelled: false },
      });
      setResults([]);
    } finally {
      setScanning(false);
    }
  }

  async function stopScan() {
    await cancelScan();
    setStatus("Scan wordt geannuleerd...");
  }

  async function deleteSelected() {
    const selected = results.filter((item) => selectedPaths.has(item.path));
    if (!selected.length || !window.confirm(`Verplaats ${selected.length} bestanden (${selected.reduce((sum, item) => sum + item.size_mb, 0).toFixed(1)} MB) naar de Prullenbak?`)) return;
    setDeleting(true);
    const response = await moveToTrash(selected);
    setDeleting(false);
    if (response.failed.length) {
      setStatus(`${response.succeeded.length} verplaatst, ${response.failed.length} niet verplaatst.`);
    } else {
      setStatus(`${response.succeeded.length} bestanden naar de Prullenbak verplaatst.`);
    }
    setSelectedPaths(new Set());
    if (response.succeeded.length) {
      setResults((current) => current.filter((item) => !response.succeeded.includes(item.path)));
    }
  }

  const visibleResults = results.filter((item) => item.path.toLowerCase().includes(query.toLowerCase()));

  function selectProfile(nextProfile: ScanProfile) {
    setProfile(nextProfile);
    setFilters({ ...profileFilters[nextProfile], topN: 100 });
  }

  function updateFilter(name: keyof CustomFilters, value: string) {
    const parsed = Number.parseInt(value, 10);
    if (!Number.isFinite(parsed)) return;
    const limits = { minSizeMb: [0, 1_000_000], minAgeDays: [0, 36_500], topN: [1, 10_000] }[name];
    setFilters((current) => ({ ...current, [name]: Math.max(limits[0], Math.min(limits[1], parsed)) }));
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <img className="brand-mark" src="/v3-logo.svg" alt="Safe Mac Cleaner v3" />
          <p className="eyebrow">SAFE MAC CLEANER / V3</p>
          <h1>Ruimte terug, zonder giswerk.</h1>
          <p className="lede">Een rustige, lokale bestandsbrowser voor je Mac.</p>
        </div>
        <div className="version-pill">{appInfo.version}</div>
      </header>

      <section className="hero-card" aria-labelledby="scan-heading">
        <div className="hero-copy">
          <span className="status-dot" aria-hidden="true" />
          <p className="eyebrow">LOKAAL EN OMKEERBAAR</p>
          <h2 id="scan-heading">Wat wil je vandaag opruimen?</h2>
          <p>Scan alleen geselecteerde gebruikersmappen. Niets gaat rechtstreeks verloren: verwijderde bestanden gaan naar de Prullenbak.</p>
        </div>
        <div className="scan-controls">
          <label htmlFor="profile">Scanprofiel</label>
          <select id="profile" value={profile} onChange={(event) => selectProfile(event.target.value as ScanProfile)}>
            {Object.entries(scanProfiles).map(([key, value]) => (
              <option key={key} value={key}>{value.label}</option>
            ))}
          </select>
          <p className="control-hint">{scanProfiles[profile].description}</p>
          <div className={`custom-filters ${profile === "custom" ? "" : "is-hidden"}`} aria-label="Aangepaste filters">
            <label>Minimale grootte (MB)<input type="number" min="0" max="1000000" value={filters.minSizeMb} onChange={(event) => updateFilter("minSizeMb", event.target.value)} /></label>
            <label>Minimale ouderdom (dagen)<input type="number" min="0" max="36500" value={filters.minAgeDays} onChange={(event) => updateFilter("minAgeDays", event.target.value)} /></label>
            <label>Maximale resultaten<input type="number" min="1" max="10000" value={filters.topN} onChange={(event) => updateFilter("topN", event.target.value)} /></label>
          </div>
          <div className="button-row">
            <button className="primary-button" onClick={startScan} disabled={scanning}>
              {scanning ? "Scan bezig..." : "Start scan"}
            </button>
            {scanning && <button className="secondary-button" onClick={stopScan}>Stop scan</button>}
          </div>
        </div>
      </section>

      <section className="workspace-grid">
        <article className="panel empty-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">RESULTATEN</p>
              <h3>{status}</h3>
            </div>
            <span className="count-badge">0</span>
          </div>
          {visibleResults.length === 0 ? (
            <div className="empty-state">
              <div className="empty-mark">⌁</div>
              <p>{results.length ? "Geen resultaten voor deze zoekopdracht." : "Je scanresultaten verschijnen hier."}</p>
              <span className="error-text">{scanResponse?.errors[0] ?? "Start een scan om lokale resultaten te bekijken."}</span>
            </div>
          ) : (
            <div className="result-list">
              {visibleResults.map((item) => (
                <div className="result-row" key={item.path}>
                  <div className="result-main"><input type="checkbox" checked={selectedPaths.has(item.path)} onChange={() => setSelectedPaths((current) => { const next = new Set(current); next.has(item.path) ? next.delete(item.path) : next.add(item.path); return next; })} /><div><strong>{item.path.split("/").pop()}</strong><span>{item.path}</span></div></div>
                  <button className="finder-button" onClick={() => revealInFinder(item.path)} aria-label={`Toon ${item.path} in Finder`}>Finder</button>
                  <b>{item.size_mb.toFixed(1)} MB</b>
                </div>
              ))}
            </div>
          )}
          <div className="result-footer">
            <input aria-label="Zoek in resultaten" placeholder="Zoek in resultaten..." value={query} onChange={(event) => setQuery(event.target.value)} />
            <span>{scanResponse ? `${scanResponse.stats.inspected_files} onderzocht · ${scanResponse.stats.skipped_packages} pakketten overgeslagen` : ""}</span>
          </div>
          {selectedPaths.size > 0 && <button className="danger-button" onClick={deleteSelected} disabled={deleting}>{deleting ? "Bezig..." : `Verplaats ${selectedPaths.size} naar Prullenbak`}</button>}
        </article>
        <aside className="panel safety-panel">
          <p className="eyebrow">VEILIGHEID EERST</p>
          <h3>De app beslist niet voor jou.</h3>
          <ul>
            <li>Lokale verwerking</li>
            <li>Beschermde macOS-pakketten blijven dicht</li>
            <li>Altijd eerst een controleerbare selectie</li>
          </ul>
        </aside>
      </section>

      <footer>© 2026 Tiëndo Welles · {appInfo.name} v3 in ontwikkeling</footer>
    </main>
  );
}
