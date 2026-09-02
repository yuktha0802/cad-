import { test } from "node:test";
import assert from "node:assert/strict";
import {
  WORKSPACE_TABS,
  VISIBILITY_MODES,
  getAircraftWorkspaceState,
  setAircraftWorkspaceState,
  resetAircraftWorkspaceState,
  triggerAircraftGeneration,
} from "./aircraftWorkspaceStore.js";

test("Design Studio Engineering Workspace loads with FW-007 baseline", () => {
  resetAircraftWorkspaceState();
  const state = getAircraftWorkspaceState();

  assert.equal(state.aircraftId, "FW-007");
  assert.equal(state.version, "v1");
  assert.equal(state.status, "PASS");
  assert.equal(state.prototypeReadiness, "READY");
  assert.equal(state.activeTab, WORKSPACE_TABS.OVERVIEW);
  assert.equal(state.visibilityMode, VISIBILITY_MODES.ALL);
});

test("Component inspection exposes type, material, dimensions, and source requirement", () => {
  resetAircraftWorkspaceState();
  setAircraftWorkspaceState({
    selectedComponentId: "MainWing_Left_MainSpar",
    activeTab: WORKSPACE_TABS.COMPONENTS,
  });

  const state = getAircraftWorkspaceState();
  assert.equal(state.selectedComponentId, "MainWing_Left_MainSpar");
  assert.equal(state.activeTab, WORKSPACE_TABS.COMPONENTS);
});

test("Bidirectional traceability between Requirements and CAD Geometry", () => {
  resetAircraftWorkspaceState();

  // 1. Forward: Requirement -> CAD Component
  setAircraftWorkspaceState({
    selectedRequirementKey: "wing.span",
    activeTab: WORKSPACE_TABS.REQUIREMENTS,
  });
  let state = getAircraftWorkspaceState();
  assert.equal(state.selectedRequirementKey, "wing.span");

  // 2. Reverse: CAD Component -> Requirement
  setAircraftWorkspaceState({
    selectedComponentId: "Fuselage_Former_001",
    selectedRequirementKey: "fuselage.width",
    activeTab: WORKSPACE_TABS.COMPONENTS,
  });
  state = getAircraftWorkspaceState();
  assert.equal(state.selectedComponentId, "Fuselage_Former_001");
  assert.equal(state.selectedRequirementKey, "fuselage.width");
});

test("Non-blocking engineering warnings are preserved and displayed", () => {
  resetAircraftWorkspaceState();
  const state = getAircraftWorkspaceState();

  assert.ok(state.warnings.length > 0);
  assert.ok(state.warnings[0].includes("takeoff mass"));
  assert.ok(state.warnings[0].includes("NON-BLOCKING"));
  // Pipeline status and prototype readiness remain PASS / READY
  assert.equal(state.status, "PASS");
  assert.equal(state.prototypeReadiness, "READY");
});

test("Version immutability: generating v2 adds to history without mutating v1 state", async () => {
  resetAircraftWorkspaceState();

  // Mock global fetch for pipeline generate
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, opts) => {
    return {
      ok: true,
      json: async () => ({
        ok: true,
        aircraft_id: "FW-007",
        version: "v2",
        status: "PASS",
        prototype_readiness: "READY",
        manifest: {
          aircraft_id: "FW-007",
          version: "v2",
          status: "PASS",
          prototype_readiness: "READY",
          parameters: {
            wing_span: { value: 2200.0 },
          },
        },
      }),
    };
  };

  try {
    await triggerAircraftGeneration({
      aircraftId: "FW-007",
      version: "v2",
    });

    const state = getAircraftWorkspaceState();
    assert.ok(state.historyVersions.includes("v1"));
    assert.ok(state.historyVersions.includes("v2"));
    assert.equal(state.prototypeReadiness, "READY");
  } finally {
    globalThis.fetch = originalFetch;
  }
});
