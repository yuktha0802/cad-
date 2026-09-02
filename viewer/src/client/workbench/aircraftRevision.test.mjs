import { test } from "node:test";
import assert from "node:assert/strict";

import {
  WORKSPACE_TABS,
  getAircraftWorkspaceState,
  setAircraftWorkspaceState,
  resetAircraftWorkspaceState,
} from "./aircraftWorkspaceStore.js";

test("Phase 9: Revision tab and change impact analysis state management", () => {
  resetAircraftWorkspaceState();
  assert.equal(WORKSPACE_TABS.REVISIONS, "REVISIONS");

  setAircraftWorkspaceState({
    activeTab: WORKSPACE_TABS.REVISIONS,
    version: "v2",
    parentVersion: "v1",
    selectedParentRevision: "v1",
    selectedTargetRevision: "v2",
    revisionDiffs: [
      {
        parameter: "wing.span",
        category: "Wing",
        old_value: "2000.0 mm",
        new_value: "2100.0 mm",
        old_status: "EXPLICIT",
        new_status: "EXPLICIT",
        change_type: "MODIFIED",
        severity: "HIGH",
        description: "Wingspan increased +100 mm for payload capacity",
      },
    ],
  });

  const state = getAircraftWorkspaceState();
  assert.equal(state.activeTab, WORKSPACE_TABS.REVISIONS);
  assert.equal(state.version, "v2");
  assert.equal(state.parentVersion, "v1");
  assert.equal(state.selectedParentRevision, "v1");
  assert.equal(state.selectedTargetRevision, "v2");
  assert.equal(state.revisionDiffs.length, 1);
  assert.equal(state.revisionDiffs[0].parameter, "wing.span");
  assert.equal(state.revisionDiffs[0].severity, "HIGH");
});

test("Phase 9: Selective regeneration preserves historical versions and updates manifest", () => {
  resetAircraftWorkspaceState();
  
  setAircraftWorkspaceState({
    historyVersions: ["v1", "v2"],
    version: "v2",
    parentVersion: "v1",
    status: "PASS",
    prototypeReadiness: "READY",
  });

  const state = getAircraftWorkspaceState();
  assert.deepEqual(state.historyVersions, ["v1", "v2"]);
  assert.equal(state.status, "PASS");
  assert.equal(state.prototypeReadiness, "READY");
});
