import { afterEach, describe, expect, it, vi } from "vitest";
import { getMilkyWay } from "../src/api/client";

describe("portal API client", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("requests Milky Way views through the portal API proxy", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ lens: "value_stream", sectors: [] })
    } as Response);

    await getMilkyWay("value_stream");

    expect(fetch).toHaveBeenCalledWith("/api/views/milky-way?lens=value_stream");
  });

  it("raises a useful error when the API returns a non-OK response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 502,
      statusText: "Bad Gateway"
    } as Response);

    await expect(getMilkyWay("organization")).rejects.toThrow(
      "Modeler API request failed: 502 Bad Gateway"
    );
  });
});
