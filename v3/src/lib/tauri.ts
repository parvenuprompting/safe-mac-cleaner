import { invoke } from "@tauri-apps/api/core";

export const isTauri = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

export async function getAppInfo(): Promise<{ name: string; version: string }> {
  if (!isTauri) {
    return { name: "Safe Mac Cleaner", version: "3.0.0-alpha.1" };
  }
  return invoke("get_app_info");
}
