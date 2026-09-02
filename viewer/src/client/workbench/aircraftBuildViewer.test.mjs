import test from "node:test";
import assert from "node:assert/strict";
import {
  WORKSPACE_TABS,
  BUILD_VIEW_MODES,
  BUILD_HIGHLIGHT_MODES,
  BUILD_PROGRESS_STATUS,
  getAircraftWorkspaceState,
  setAircraftWorkspaceState,
  resetAircraftWorkspaceState,
} from "./aircraftWorkspaceStore.js";

test("Phase 12: 3D Build Visualization workspace tab and view mode state management", () => {
  resetAircraftWorkspaceState();
  const initial = getAircraftWorkspaceState();

  assert.equal(WORKSPACE_TABS.BUILD_3D, "BUILD_3D");
  assert.equal(initial.buildViewMode, BUILD_VIEW_MODES.ASSEMBLED);
  assert.equal(initial.buildHighlightMode, BUILD_HIGHLIGHT_MODES.NONE);

  // Switch to EXPLODED view mode with factor
  setAircraftWorkspaceState({
    activeTab: WORKSPACE_TABS.BUILD_3D,
    buildViewMode: BUILD_VIEW_MODES.EXPLODED,
    explodedOffsetFactor: 1.5,
  });

  const state = getAircraftWorkspaceState();
  assert.equal(state.activeTab, "BUILD_3D");
  assert.equal(state.buildViewMode, "EXPLODED");
  assert.equal(state.explodedOffsetFactor, 1.5);
});

test("Phase 12: Part inspection, joint inspection, and traceability state management", () => {
  resetAircraftWorkspaceState();

  setAircraftWorkspaceState({
    selectedPartId: "SPAR-L-MAIN",
    selectedJointId: "JOINT-TAB-001",
    selectedStepId: "STEP-02",
    buildHighlightMode: BUILD_HIGHLIGHT_MODES.PART,
  });

  const state = getAircraftWorkspaceState();
  assert.equal(state.selectedPartId, "SPAR-L-MAIN");
  assert.equal(state.selectedJointId, "JOINT-TAB-001");
  assert.equal(state.selectedStepId, "STEP-02");
  assert.equal(state.buildHighlightMode, "PART");
});

test("Phase 12: Step navigation and build progress tracking separation from engineering status", () => {
  resetAircraftWorkspaceState();

  // Initial build progress
  const initial = getAircraftWorkspaceState();
  assert.equal(initial.status, "PASS"); // Engineering status
  assert.equal(initial.buildProgressState.completedParts.length, 0);

  // Mark step 1 and part complete
  setAircraftWorkspaceState((curr) => ({
    buildProgressState: {
      ...curr.buildProgressState,
      completedParts: ["FORMER-000", "FORMER-001"],
      completedSteps: ["STEP-01"],
      partStatuses: { "FORMER-000": BUILD_PROGRESS_STATUS.COMPLETE, "FORMER-001": BUILD_PROGRESS_STATUS.COMPLETE },
      stepStatuses: { "STEP-01": BUILD_PROGRESS_STATUS.COMPLETE },
    },
  }));

  const updated = getAircraftWorkspaceState();
  // Engineering status remains strictly VALID / PASS
  assert.equal(updated.status, "PASS");
  assert.equal(updated.buildProgressState.completedParts.length, 2);
  assert.equal(updated.buildProgressState.completedSteps.length, 1);
  assert.equal(updated.buildProgressState.partStatuses["FORMER-000"], "COMPLETE");
});

test("Phase 12: Reset operations restore clean view state without altering CAD source", () => {
  resetAircraftWorkspaceState();

  setAircraftWorkspaceState({
    buildViewMode: BUILD_VIEW_MODES.EXPLODED,
    explodedOffsetFactor: 2.0,
    isolatedComponentId: "Fuselage",
    buildHighlightMode: BUILD_HIGHLIGHT_MODES.SUBASSEMBLY,
  });

  // Reset view action
  setAircraftWorkspaceState({
    buildViewMode: BUILD_VIEW_MODES.ASSEMBLED,
    explodedOffsetFactor: 1.0,
    isolatedComponentId: null,
    buildHighlightMode: BUILD_HIGHLIGHT_MODES.NONE,
  });

  const state = getAircraftWorkspaceState();
  assert.equal(state.buildViewMode, "ASSEMBLED");
  assert.equal(state.explodedOffsetFactor, 1.0);
  assert.equal(state.isolatedComponentId, null);
  assert.equal(state.buildHighlightMode, "NONE");
});
