import test from "node:test";
import assert from "node:assert/strict";
import {
  WORKSPACE_TABS,
  RELEASE_STATUS,
  getAircraftWorkspaceState,
  setAircraftWorkspaceState,
  resetAircraftWorkspaceState,
} from "./aircraftWorkspaceStore.js";

test("Phase 13: Final Release Gate workspace tab and release status state management", () => {
  resetAircraftWorkspaceState();
  const initial = getAircraftWorkspaceState();

  assert.equal(WORKSPACE_TABS.RELEASE, "RELEASE");
  assert.equal(RELEASE_STATUS.RELEASE_READY, "RELEASE_READY");
  assert.equal(RELEASE_STATUS.READY_WITH_WARNINGS, "READY_WITH_WARNINGS");
  assert.equal(RELEASE_STATUS.RELEASE_BLOCKED, "RELEASE_BLOCKED");

  // Set Release Gate Result state
  const mockReleaseManifest = {
    aircraft_id: "FW-007",
    release_id: "FW-007-v1-RELEASE-001",
    version: "v1",
    release_status: RELEASE_STATUS.READY_WITH_WARNINGS,
    prototype_status: "READY_WITH_WARNINGS",
    checks: [
      { check_id: "REL-CAD-001", category: "CAD_CONSISTENCY", name: "Wingspan", status: "PASS", is_blocking: true },
      { check_id: "REL-STR-001", category: "STRUCTURAL_CONSISTENCY", name: "Solids Count", status: "PASS", is_blocking: true },
      { check_id: "REL-MFG-001", category: "MANUFACTURING_CONSISTENCY", name: "Parts Decomposition", status: "PASS", is_blocking: true },
      { check_id: "REL-BPKG-001", category: "BUILD_PACKAGE_CONSISTENCY", name: "BOM Consistency", status: "PASS", is_blocking: true },
    ],
    warnings: ["Takeoff mass (MTOW) contains non-blocking conflicting values across report sections."],
    blocking_issues: [],
  };

  setAircraftWorkspaceState({
    activeTab: WORKSPACE_TABS.RELEASE,
    releaseGateResult: {
      is_released: true,
      release_status: RELEASE_STATUS.READY_WITH_WARNINGS,
      manifest: mockReleaseManifest,
    },
  });

  const state = getAircraftWorkspaceState();
  assert.equal(state.activeTab, "RELEASE");
  assert.equal(state.releaseGateResult.is_released, true);
  assert.equal(state.releaseGateResult.release_status, "READY_WITH_WARNINGS");
  assert.equal(state.releaseGateResult.manifest.checks.length, 4);
  assert.equal(state.releaseGateResult.manifest.blocking_issues.length, 0);
  assert.equal(state.releaseGateResult.manifest.warnings.length, 1);
});

test("Phase 13: Controlled failure blocks release gate cleanly", () => {
  resetAircraftWorkspaceState();

  const mockBlockedManifest = {
    aircraft_id: "FW-007",
    release_id: "FW-007-v1-RELEASE-BLOCKED",
    version: "v1",
    release_status: RELEASE_STATUS.RELEASE_BLOCKED,
    prototype_status: "NOT_READY",
    checks: [
      { check_id: "REL-ART-001", category: "ARTIFACT_INTEGRITY", name: "Laser DXF", status: "FAIL", is_blocking: true },
    ],
    warnings: [],
    blocking_issues: ["Required fabrication artifact Sheet_01.dxf is missing from release package."],
  };

  setAircraftWorkspaceState({
    releaseGateResult: {
      is_released: false,
      release_status: RELEASE_STATUS.RELEASE_BLOCKED,
      manifest: mockBlockedManifest,
    },
  });

  const state = getAircraftWorkspaceState();
  assert.equal(state.releaseGateResult.is_released, false);
  assert.equal(state.releaseGateResult.release_status, "RELEASE_BLOCKED");
  assert.equal(state.releaseGateResult.manifest.blocking_issues.length, 1);
});
