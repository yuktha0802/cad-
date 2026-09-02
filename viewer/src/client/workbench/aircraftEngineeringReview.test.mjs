import { test } from "node:test";
import assert from "node:assert/strict";

import {
  WORKSPACE_TABS,
  getAircraftWorkspaceState,
  setAircraftWorkspaceState,
  resetAircraftWorkspaceState,
} from "./aircraftWorkspaceStore.js";

test("Phase 10: Engineering Review workspace tab and compliance state management", () => {
  resetAircraftWorkspaceState();
  assert.equal(WORKSPACE_TABS.REVIEW, "REVIEW");

  setAircraftWorkspaceState({
    activeTab: WORKSPACE_TABS.REVIEW,
    aircraftId: "FW-007",
    version: "v1",
    status: "PASS",
    prototypeReadiness: "READY",
    engineeringReview: {
      overall_status: "PASS WITH WARNINGS",
      prototype_status: "READY_WITH_WARNINGS",
      warnings: ["MTOW requirement has conflicting values [5.5 kg, 11.0 kg]."],
      conflicts: ["Takeoff Mass (MTOW) discrepancy."],
      blocking_failures: [],
      summary: {
        total_items_reviewed: 18,
        geometry_status: "PASS",
        configuration_status: "PASS",
        structure_status: "PASS",
        manufacturing_status: "PASS",
        mass_status: "CONFLICT",
        cg_status: "NOT_VERIFIABLE",
      },
    },
  });

  const state = getAircraftWorkspaceState();
  assert.equal(state.activeTab, WORKSPACE_TABS.REVIEW);
  assert.equal(state.aircraftId, "FW-007");
  assert.equal(state.engineeringReview.overall_status, "PASS WITH WARNINGS");
  assert.equal(state.engineeringReview.prototype_status, "READY_WITH_WARNINGS");
  assert.equal(state.engineeringReview.summary.geometry_status, "PASS");
  assert.equal(state.engineeringReview.summary.mass_status, "CONFLICT");
  assert.equal(state.engineeringReview.summary.cg_status, "NOT_VERIFIABLE");
});
