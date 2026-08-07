import { useEffect, useState } from "react";
import { getAppInfo } from "./lib/tauri";
import { scanProfiles, type ScanProfile } from "./features/scan/scanProfiles";

type AppInfo = { name: string; version: string };

export function App() {
  const [profile, setProfile] = useState<ScanProfile>("custom");
  const [scanning, setScanning] = useState(false);
  const [status, setStatus] = useState("Klaar voor een veilige scan.");
  const [appInfo, setAppInfo] = useState<AppInfo>({ name: "Safe Mac Cleaner", version: "3.0.0-alpha.1" });

  useEffect(() => {
    getAppInfo().then(setAppInfo).catch(() => undefined);
  }, []);

  function startScan() {
    setScanning(true);
    setStatus("Scan voorbereiden...");
    window.setTimeout(() => {
      setScanning(false);
      setStatus("V3-preview: de Rust scanengine wordt in de volgende stap aangesloten.");
    }, 450);
  }

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
          <button className="primary-button" onClick={startScan} disabled={scanning}>
            {scanning ? "Scan wordt voorbereid..." : "Start scan"}
          </button>
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
          <div className="empty-state">
            <div className="empty-mark">⌁</div>
            <p>Je scanresultaten verschijnen hier.</p>
            <span>De v3-interface is klaar voor de nieuwe Rust safety-engine.</span>
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
