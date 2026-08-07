import { useEffect, useState } from "react";
import { cancelScan, getAppInfo, listenToScanProgress, scanFiles, type ScanItem, type ScanResponse } from "./lib/tauri";
import { profileFilters, scanProfiles, type ScanProfile } from "./features/scan/scanProfiles";

type AppInfo = { name: string; version: string };

export function App() {
  const [profile, setProfile] = useState<ScanProfile>("custom");
  const [scanning, setScanning] = useState(false);
  const [status, setStatus] = useState("Klaar voor een veilige scan.");
  const [results, setResults] = useState<ScanItem[]>([]);
  const [scanResponse, setScanResponse] = useState<ScanResponse | null>(null);
  const [query, setQuery] = useState("");
  const [appInfo, setAppInfo] = useState<AppInfo>({ name: "Safe Mac Cleaner", version: "3.0.0-alpha.1" });

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
      const response = await scanFiles(profileFilters[profile]);
      setScanResponse(response);
      setResults(response.results);
      if (response.stats.cancelled) {
        setStatus(`Scan geannuleerd na ${response.stats.inspected_files} onderzochte bestanden.`);
      } else if (response.results.length > 0) {
        setStatus(`${response.results.length} geschikte bestanden gevonden.`);
      } else {
        setStatus(`Geen bestanden gevonden. ${response.stats.inspected_files} bestanden onderzocht.`);
      }
    } catch (error) {
      setStatus("Scan mislukt.");
      setScanResponse({
        results: [],
        errors: [error instanceof Error ? error.message : "Onbekende scanfout"],
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

  const visibleResults = results.filter((item) => item.path.toLowerCase().includes(query.toLowerCase()));

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
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
          <select id="profile" value={profile} onChange={(event) => setProfile(event.target.value as ScanProfile)}>
            {Object.entries(scanProfiles).map(([key, value]) => (
              <option key={key} value={key}>{value.label}</option>
            ))}
          </select>
          <p className="control-hint">{scanProfiles[profile].description}</p>
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
              <span>{scanResponse?.errors[0] ?? "Start een scan om lokale resultaten te bekijken."}</span>
            </div>
          ) : (
            <div className="result-list">
              {visibleResults.map((item) => (
                <div className="result-row" key={item.path}>
                  <div><strong>{item.path.split("/").pop()}</strong><span>{item.path}</span></div>
                  <b>{item.size_mb.toFixed(1)} MB</b>
                </div>
              ))}
            </div>
          )}
          <div className="result-footer">
            <input aria-label="Zoek in resultaten" placeholder="Zoek in resultaten..." value={query} onChange={(event) => setQuery(event.target.value)} />
            <span>{scanResponse ? `${scanResponse.stats.inspected_files} onderzocht · ${scanResponse.stats.skipped_packages} pakketten overgeslagen` : ""}</span>
          </div>
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
