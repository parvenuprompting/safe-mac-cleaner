import { describe, expect, it } from "vitest";
import { scanProfiles } from "./scanProfiles";

describe("scan profiles", () => {
  it("exposes safe user-facing profiles", () => {
    expect(scanProfiles.custom.label).toBe("Aangepaste scan");
    expect(Object.keys(scanProfiles)).toEqual(["custom", "large", "old", "downloads"]);
  });
});
