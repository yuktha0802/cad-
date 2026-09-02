/**
 * Aircraft Engineering Workspace Store
 * Manages reactive state for the Design Studio Engineering Aircraft Workspace.
 */

export const PIPELINE_PHASES = [
  "PHASE_3_REQUIREMENTS",
  "PHASE_4_CAD",
  "PHASE_5_STRUCTURE",
  "PHASE_6A_MANUFACTURING_MODEL",
  "PHASE_6B_CLASSIFICATION",
  "PHASE_6C_FABRICATION",
  "PHASE_6D_LASER",
  "PHASE_6E_PRINT",
  "PHASE_6F_VALIDATION",
];

export const WORKSPACE_TABS = {
  OVERVIEW: "OVERVIEW",
  COMPONENTS: "COMPONENTS",
  REQUIREMENTS: "REQUIREMENTS",
  STRUCTURE: "STRUCTURE",
  MANUFACTURING: "MANUFACTURING",
  VALIDATION: "VALIDATION",
  REVIEW: "REVIEW",
  BUILD: "BUILD",
  BUILD_3D: "BUILD_3D",
  RELEASE: "RELEASE",
  ARTIFACTS: "ARTIFACTS",
  VERSIONS: "VERSIONS",
  REVISIONS: "REVISIONS",
};

export const RELEASE_STATUS = {
  RELEASE_READY: "RELEASE_READY",
  READY_WITH_WARNINGS: "READY_WITH_WARNINGS",
  RELEASE_BLOCKED: "RELEASE_BLOCKED",
  INCOMPLETE: "INCOMPLETE",
  STALE: "STALE",
  FAILED: "FAILED",
};

export const VISIBILITY_MODES = {
  ALL: "ALL",
  EXTERNAL: "EXTERNAL",
  STRUCTURE: "STRUCTURE",
  BAYS: "BAYS",
};

export const BUILD_VIEW_MODES = {
  ASSEMBLED: "ASSEMBLED",
  EXPLODED: "EXPLODED",
  STRUCTURE: "STRUCTURE",
  MANUFACTURING: "MANUFACTURING",
  PARTS: "PARTS",
  SUBASSEMBLY: "SUBASSEMBLY",
};

export const BUILD_HIGHLIGHT_MODES = {
  NONE: "NONE",
  PART: "PART",
  SUBASSEMBLY: "SUBASSEMBLY",
  STEP: "STEP",
  JOINT: "JOINT",
  SHEET: "SHEET",
  PRINT_PART: "PRINT_PART",
};

export const BUILD_PROGRESS_STATUS = {
  NOT_STARTED: "NOT_STARTED",
  IN_PROGRESS: "IN_PROGRESS",
  COMPLETE: "COMPLETE",
  BLOCKED: "BLOCKED",
};

function createInitialState() {
  return {
    aircraftId: "FW-007",
    projectId: "PROJ_SURVEY_001",
    version: "v1",
    parentVersion: "",
    manufacturingProfile: "FW007_Production_Profile",
    activeTab: WORKSPACE_TABS.OVERVIEW,
    visibilityMode: VISIBILITY_MODES.ALL,
    buildViewMode: BUILD_VIEW_MODES.ASSEMBLED,
    buildHighlightMode: BUILD_HIGHLIGHT_MODES.NONE,
    selectedComponentId: "MainWing_Left_MainSpar",
    selectedRequirementKey: "wing.span",
    selectedPartId: "RIB-L-001",
    selectedSheetId: "Sheet_01",
    selectedPrintPartId: "PRINT-WING-ATTACH-001",
    selectedStepId: "STEP-01",
    selectedJointId: "JOINT-001",
    isolatedComponentId: null,
    explodedOffsetFactor: 1.0,
    filterQuery: "",
    isGenerating: false,
    generationProgress: 1.0,
    generationPhase: "PHASE_6F_VALIDATION",
    status: "PASS",
    prototypeReadiness: "READY",
    manifest: null,
    historyVersions: ["v1"],
    revisionManifest: null,
    engineeringReview: null,
    prototypeBuildPackage: null,
    buildVisualizationPackage: null,
    releaseGateResult: null,
    buildProgressState: {
      completedParts: [],
      completedSteps: [],
      partStatuses: {},
      stepStatuses: {},
    },
    revisionDiffs: [],
    selectedParentRevision: "v1",
    selectedTargetRevision: "v2",
    errors: [],
    warnings: ["Conflict detected for takeoff mass: [5.5, 11.0] (NON-BLOCKING - CAD CONTINUED)"],
  };
}

let storeState = createInitialState();
const listeners = new Set();

export function getAircraftWorkspaceState() {
  return storeState;
}

export function subscribeAircraftWorkspace(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function setAircraftWorkspaceState(patch) {
  storeState = {
    ...storeState,
    ...(typeof patch === "function" ? patch(storeState) : patch),
  };
  for (const listener of listeners) {
    try {
      listener(storeState);
    } catch (e) {
      console.error("Aircraft workspace listener error:", e);
    }
  }
}

export function resetAircraftWorkspaceState() {
  setAircraftWorkspaceState(createInitialState());
}

export async function fetchAircraftStatus(aircraftId = storeState.aircraftId, version = storeState.version) {
  try {
    const res = await fetch(`/__cad/pipeline/aircraft/status?aircraft=${encodeURIComponent(aircraftId)}&version=${encodeURIComponent(version)}`);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const data = await res.json();
    if (data.manifest) {
      setAircraftWorkspaceState({
        aircraftId,
        version,
        status: data.manifest.status || "PASS",
        prototypeReadiness: data.manifest.prototype_readiness || "READY",
        manifest: data.manifest,
        errors: data.manifest.errors || [],
        warnings: data.manifest.warnings || [],
      });
    }
    return data;
  } catch (error) {
    console.warn("Could not fetch aircraft status from server, using local manifest if present:", error);
    return null;
  }
}

export async function triggerAircraftGeneration({
  aircraftId = storeState.aircraftId,
  version = storeState.version,
  profile = storeState.manufacturingProfile,
  specText = "",
  projectId = storeState.projectId,
} = {}) {
  setAircraftWorkspaceState({ isGenerating: true, generationProgress: 0.1, generationPhase: "PHASE_3_REQUIREMENTS" });
  try {
    const res = await fetch("/__cad/pipeline/aircraft/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        aircraft_id: aircraftId,
        project_id: projectId,
        version: version,
        manufacturingProfile: profile,
        specText: specText,
      }),
    });
    if (!res.ok) {
      throw new Error(`Pipeline generation request failed with ${res.status}`);
    }
    const data = await res.json();
    setAircraftWorkspaceState((current) => ({
      isGenerating: false,
      generationProgress: 1.0,
      generationPhase: "PHASE_6F_VALIDATION",
      status: data.status || "PASS",
      prototypeReadiness: data.prototype_readiness || "READY",
      manifest: data.manifest || current.manifest,
      historyVersions: current.historyVersions.includes(version) ? current.historyVersions : [...current.historyVersions, version],
      errors: data.manifest?.errors || [],
      warnings: data.manifest?.warnings || current.warnings,
    }));
    return data;
  } catch (error) {
    setAircraftWorkspaceState({
      isGenerating: false,
      errors: [error.message],
    });
    throw error;
  }
}
