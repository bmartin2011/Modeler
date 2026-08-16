import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "../src/App";

describe("App", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("loads the selected Milky Way projection through the API proxy", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          lens: "value_stream",
          sectors: [{ id: "vs.discover", name: "Discover Opportunity", rings: ["purpose"] }],
          overlays: [],
          collapsible_branches: []
        })
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          lens: "organization",
          sectors: [{ id: "person.john", name: "John", rings: ["leader"] }],
          overlays: [],
          collapsible_branches: []
        })
      } as Response);

    render(<App />);

    expect(await screen.findByText("Discover Opportunity")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Organization Lens" }));

    expect(await screen.findByText("John")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith("/api/views/milky-way?lens=organization");
  });

  it("shows a retry path when the Milky Way request fails", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockRejectedValueOnce(new Error("API unavailable"))
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          lens: "value_stream",
          sectors: [{ id: "vs.discover", name: "Discover Opportunity", rings: ["purpose"] }],
          overlays: [],
          collapsible_branches: []
        })
      } as Response);

    render(<App />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Unable to load the Milky Way.");
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));

    expect(await screen.findByText("Discover Opportunity")).toBeInTheDocument();
  });
});
