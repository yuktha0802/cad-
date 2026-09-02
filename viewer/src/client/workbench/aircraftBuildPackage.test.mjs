import { test } from "node:test";
import assert from "node:assert/strict";

import {
  WORKSPACE_TABS,
  getAircraftWorkspaceState,
  setAircraftWorkspaceState,
  resetAircraftWorkspaceState,
} from "./aircraftWorkspaceStore.js";

test("Phase 11: Prototype Build workspace tab and package state management", () => {
  resetAircraftWorkspaceState();
  assert.equal(WORKSPACE_TABS.BUILD, "BUILD");

  setAircraftWorkspaceState({
    activeTab: WORKSPACE_TABS.BUILD,
    aircraftId: "FW-007",
    version: "v1",
    status: "PASS",
    prototypeReadiness: "READY",
    prototypeBuildPackage: {
      aircraft_id: "FW-007",
      version: "v1",
      prototype_readiness: "READY",
      parts_count: 48,
      laser_parts_count: 47,
      printable_parts_count: 1,
      joints_count: 69,
      laser_sheets_count: 3,
      assembly_steps_count: 5,
      summary: {
        total_parts: 48,
        laser_parts: 47,
        printable_parts: 1,
        total_joints: 69,
        total_sheets: 3,
        total_assembly_steps: 5,
        build_validation_status: "READY",
      },
    },
  });

  const state = getAircraftWorkspaceState();
  assert.equal(state.activeTab, WORKSPACE_TABS.BUILD);
  assert.equal(state.aircraftId, "FW-007");
  assert.equal(state.prototypeBuildPackage.parts_count, 48);
  assert.equal(state.prototypeBuildPackage.laser_parts_count, 47);
  assert.equal(state.prototypeBuildPackage.printable_parts_count, 1);
  assert.equal(state.prototypeBuildPackage.joints_count, 69);
  assert.equal(state.prototypeBuildPackage.assembly_steps_count, 5);
});
