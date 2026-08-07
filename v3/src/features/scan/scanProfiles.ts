export type ScanProfile = "custom" | "large" | "old" | "downloads";

export const scanProfiles: Record<ScanProfile, { label: string; description: string }> = {
  custom: { label: "Aangepaste scan", description: "Gebruik je eigen filters" },
  large: { label: "Grote bestanden", description: "Vanaf 1 GB" },
  old: { label: "Oude bestanden", description: "Ouder dan 180 dagen" },
  downloads: { label: "Oude downloads", description: "Downloads ouder dan 30 dagen" },
};
