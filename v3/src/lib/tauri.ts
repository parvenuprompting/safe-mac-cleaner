import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";

export const isTauri = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

export type ScanItem = {
  path: string;
  size_mb: number;
  age_days: number;
  file_type: string;
};

export type ScanResponse = {
  results: ScanItem[];
  errors: string[];
  stats: {
    inspected_files: number;
    candidates: number;
    skipped_age: number;
    skipped_size: number;
    skipped_packages: number;
    permission_errors: number;
    cancelled: boolean;
  };
};

export type ScanProgress = { path: string; inspected_files: number };

export async function getAppInfo(): Promise<{ name: string; version: string }> {
  if (!isTauri) {
    return { name: "Safe Mac Cleaner", version: "3.0.0-alpha.1" };
  }
  return invoke("get_app_info");
}

export async function scanFiles(options: {
  minSizeMb: number;
  minAgeDays: number;
  topN?: number;
}): Promise<ScanResponse> {
  if (!isTauri) {
    return {
      results: [],
      errors: ["Start de desktop-app om lokale mappen te scannen."],
      stats: {
        inspected_files: 0,
        candidates: 0,
        skipped_age: 0,
        skipped_size: 0,
        skipped_packages: 0,
        permission_errors: 0,
        cancelled: false,
      },
    };
  }
  return invoke("scan_files", {
    directories: [],
    min_size_mb: options.minSizeMb,
    min_age_days: options.minAgeDays,
    age_mode: "last_modified",
    top_n: options.topN ?? 100,
  });
}

export async function cancelScan(): Promise<void> {
  if (isTauri) await invoke("cancel_scan");
}

export function listenToScanProgress(handler: (progress: ScanProgress) => void) {
  if (!isTauri) return Promise.resolve(() => undefined);
  return listen<ScanProgress>("scan-progress", (event) => handler(event.payload));
}
