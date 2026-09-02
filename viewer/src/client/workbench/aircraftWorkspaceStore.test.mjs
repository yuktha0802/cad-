import { test } from "node:test";
import assert from "node:assert/strict";
import {
  PIPELINE_PHASES,
  WORKSPACE_TABS,
  VISIBILITY_MODES,
  getAircraftWorkspaceState,
  setAircraftWorkspaceState,
  resetAircraftWorkspaceState,
  subscribeAircraftWorkspace,
} from "./aircraftWorkspaceStore.js";

test("AircraftWorkspaceStore initializes with authoritative defaults", () => {
  resetAircraftWorkspaceState();
  const state = getAircraftWorkspaceState();
  assert.equal(state.aircraftId, "FW-007");
  assert.equal(state.version, "v1");
  assert.equal(state.prototypeReadiness, "READY");
  assert.equal(state.activeTab, WORKSPACE_TABS.OVERVIEW);
  assert.equal(state.visibilityMode, VISIBILITY_MODES.ALL);
  assert.equal(PIPELINE_PHASES.length, 9);
});

test("AircraftWorkspaceStore notifies subscribers on state changes", () => {
  resetAircraftWorkspaceState();
  let callCount = 0;
  let receivedTab = "";

  const unsubscribe = subscribeAircraftWorkspace((s) => {
    callCount++;
    receivedTab = s.activeTab;
  });

  setAircraftWorkspaceState({ activeTab: WORKSPACE_TABS.MANUFACTURING });
  assert.equal(callCount, 1);
  assert.equal(receivedTab, WORKSPACE_TABS.MANUFACTURING);
  assert.equal(getAircraftWorkspaceState().activeTab, WORKSPACE_TABS.MANUFACTURING);

  unsubscribe();
  setAircraftWorkspaceState({ activeTab: WORKSPACE_TABS.VALIDATION });
  assert.equal(callCount, 1); // No new notification after unsubscribe
});

test("AircraftWorkspaceStore handles component and requirement selection", () => {
  resetAircraftWorkspaceState();
  setAircraftWorkspaceState({
    selectedComponentId: "Fuselage_Former_001",
    selectedRequirementKey: "fuselage.length",
    selectedPartId: "FMR-001",
    selectedSheetId: "Sheet_02",
  });

  const state = getAircraftWorkspaceState();
  assert.equal(state.selectedComponentId, "Fuselage_Former_001");
  assert.equal(state.selectedRequirementKey, "fuselage.length");
  assert.equal(state.selectedPartId, "FMR-001");
  assert.equal(state.selectedSheetId, "Sheet_02");
});
