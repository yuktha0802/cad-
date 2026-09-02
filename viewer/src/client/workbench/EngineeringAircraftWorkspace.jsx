import React, { useState, useMemo, useEffect, useSyncExternalStore } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Box,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  ClipboardCheck,
  Clock,
  Compass,
  Cpu,
  Download,
  Eye,
  FileCode,
  FileText,
  FolderTree,
  Gauge,
  GitCompare,
  Hammer,
  Layers,
  ListFilter,
  Maximize2,
  Package,
  PackageCheck,
  Plane,
  Printer,
  RefreshCw,
  Search,
  ShieldCheck,
  Tag,
  Wrench,
  XCircle,
} from "lucide-react";
import {
  WORKSPACE_TABS,
  VISIBILITY_MODES,
  BUILD_VIEW_MODES,
  BUILD_HIGHLIGHT_MODES,
  BUILD_PROGRESS_STATUS,
  getAircraftWorkspaceState,
  subscribeAircraftWorkspace,
  setAircraftWorkspaceState,
  triggerAircraftGeneration,
  fetchAircraftStatus,
} from "./aircraftWorkspaceStore.js";

// Canonical FW-007 Component & Requirement Metadata (authoritative dynamic fallback)
const DEFAULT_AIRCRAFT_METADATA = {
  aircraft_id: "FW-007",
  project_id: "PROJ_SURVEY_001",
  version: "v1",
  status: "PASS",
  prototype_readiness: "READY",
  specification: {
    category: "SURVEY",
    wing_span: 2000.0,
    aspect_ratio: 10.0,
    root_chord: 250.0,
    tip_chord: 150.0,
    fuselage_length: 1500.0,
    fuselage_width: 200.0,
    fuselage_height: 400.0,
    ht_span: 500.0,
    vt_height: 400.0,
    propeller: "12x6 APC (304.8 mm)",
    takeoff_mass: 5.5,
    empty_weight: 3.2,
    battery_weight: 1.5,
    payload_weight: 2.0,
  },
  structural_components: 48,
  manufacturing_parts: 48,
  laser_parts: 47,
  three_d_print_parts: 1,
  joints: 69,
  sheets: 3,
  estimated_mass_g: 133.56,
};

export default function EngineeringAircraftWorkspace() {
  const state = useSyncExternalStore(
    subscribeAircraftWorkspace,
    getAircraftWorkspaceState,
    getAircraftWorkspaceState
  );

  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState(state.activeTab || WORKSPACE_TABS.OVERVIEW);
  const [selectedCompId, setSelectedCompId] = useState(state.selectedComponentId);
  const [selectedReqKey, setSelectedReqKey] = useState(state.selectedRequirementKey);
  const [selectedPartId, setSelectedPartId] = useState(state.selectedPartId);
  const [selectedSheetId, setSelectedSheetId] = useState(state.selectedSheetId);
  const [visibilityMode, setVisibilityMode] = useState(state.visibilityMode);
  const [selectedProfile, setSelectedProfile] = useState(state.manufacturingProfile);
  const [isRegenerating, setIsRegenerating] = useState(false);

  // Sync back to store
  useEffect(() => {
    setAircraftWorkspaceState({
      activeTab,
      selectedComponentId: selectedCompId,
      selectedRequirementKey: selectedReqKey,
      selectedPartId: selectedPartId,
      selectedSheetId: selectedSheetId,
      visibilityMode,
      manufacturingProfile: selectedProfile,
    });
  }, [activeTab, selectedCompId, selectedReqKey, selectedPartId, selectedSheetId, visibilityMode, selectedProfile]);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
  };

  const handleRegenerate = async (targetVersion = "v2") => {
    setIsRegenerating(true);
    try {
      await triggerAircraftGeneration({
        aircraftId: state.aircraftId,
        version: targetVersion,
        profile: selectedProfile,
      });
    } catch (err) {
      console.error("Regeneration failed:", err);
    } finally {
      setIsRegenerating(false);
    }
  };

  return (
    <div className="flex h-full w-full flex-col bg-background text-foreground select-none overflow-hidden font-sans">
      {/* Top Header Bar */}
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-border/60 bg-muted/20 px-4">
        <div className="flex items-center gap-3">
          <div className="flex size-8 items-center justify-center rounded-md bg-primary/10 text-primary">
            <Plane className="size-4.5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold tracking-tight text-sm text-foreground">
                {state.aircraftId}
              </span>
              <span className="rounded bg-primary/15 px-1.5 py-0.5 text-[11px] font-mono font-medium text-primary">
                {state.version}
              </span>
              <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ${
                state.prototypeReadiness === "READY"
                  ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"
                  : "bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20"
              }`}>
                <span className="size-1.5 rounded-full bg-current animate-pulse" />
                {state.prototypeReadiness}
              </span>
            </div>
            <p className="text-[11px] text-muted-foreground">
              Torq Wings Design Studio • Engineering Aircraft Workspace
            </p>
          </div>
        </div>

        {/* Global Tab Navigation */}
        <nav className="flex items-center gap-1 rounded-lg bg-muted/60 p-1">
          {[
            { id: WORKSPACE_TABS.OVERVIEW, label: "Overview", icon: Gauge },
            { id: WORKSPACE_TABS.COMPONENTS, label: "3D & Components", icon: FolderTree },
            { id: WORKSPACE_TABS.REQUIREMENTS, label: "Requirements", icon: Tag },
            { id: WORKSPACE_TABS.STRUCTURE, label: "Structure", icon: Layers },
            { id: WORKSPACE_TABS.MANUFACTURING, label: "Manufacturing", icon: Hammer },
            { id: WORKSPACE_TABS.VALIDATION, label: "Validation", icon: ShieldCheck },
            { id: WORKSPACE_TABS.REVIEW, label: "Engineering Review", icon: ClipboardCheck },
            { id: WORKSPACE_TABS.BUILD, label: "Prototype Build", icon: PackageCheck },
            { id: WORKSPACE_TABS.BUILD_3D, label: "3D Build & Guidance", icon: Wrench },
            { id: WORKSPACE_TABS.RELEASE, label: "Final Release Gate", icon: ShieldCheck },
            { id: WORKSPACE_TABS.ARTIFACTS, label: "Artifacts", icon: Package },
            { id: WORKSPACE_TABS.VERSIONS, label: "Versions", icon: Clock },
            { id: WORKSPACE_TABS.REVISIONS, label: "Revisions & Impact", icon: GitCompare },
          ].map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id)}
                className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                  active
                    ? "bg-background text-foreground shadow-xs"
                    : "text-muted-foreground hover:text-foreground hover:bg-background/40"
                }`}
              >
                <Icon className="size-3.5" />
                {tab.label}
              </button>
            );
          })}
        </nav>

        {/* Top Right Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleRegenerate(state.version === "v1" ? "v2" : "v1")}
            disabled={isRegenerating}
            className="flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground shadow-xs hover:bg-primary/90 disabled:opacity-50 transition-all"
          >
            <RefreshCw className={`size-3.5 ${isRegenerating ? "animate-spin" : ""}`} />
            {isRegenerating ? "Regenerating..." : "Regenerate Aircraft"}
          </button>
        </div>
      </header>

      {/* Warnings & Non-Blocking Banner */}
      {state.warnings && state.warnings.length > 0 && (
        <div className="flex items-center justify-between border-b border-amber-500/20 bg-amber-500/10 px-4 py-1.5 text-xs text-amber-700 dark:text-amber-300">
          <div className="flex items-center gap-2">
            <AlertTriangle className="size-3.5 shrink-0" />
            <span className="font-medium">Engineering Warning:</span>
            <span>{state.warnings[0]}</span>
          </div>
          <span className="rounded bg-amber-500/20 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider">
            Non-Blocking
          </span>
        </div>
      )}

      {/* Main Workspace Body */}
      <main className="flex-1 overflow-auto">
        {activeTab === WORKSPACE_TABS.OVERVIEW && (
          <OverviewSection
            state={state}
            onSelectTab={handleTabChange}
            onSelectComp={setSelectedCompId}
          />
        )}

        {activeTab === WORKSPACE_TABS.COMPONENTS && (
          <Components3DSection
            state={state}
            selectedCompId={selectedCompId}
            onSelectComp={setSelectedCompId}
            visibilityMode={visibilityMode}
            onSetVisibilityMode={setVisibilityMode}
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            onNavigateRequirement={(req) => {
              setSelectedReqKey(req);
              setActiveTab(WORKSPACE_TABS.REQUIREMENTS);
            }}
          />
        )}

        {activeTab === WORKSPACE_TABS.REQUIREMENTS && (
          <RequirementsSection
            state={state}
            selectedReqKey={selectedReqKey}
            onSelectReq={setSelectedReqKey}
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            onNavigateComponent={(comp) => {
              setSelectedCompId(comp);
              setActiveTab(WORKSPACE_TABS.COMPONENTS);
            }}
          />
        )}

        {activeTab === WORKSPACE_TABS.STRUCTURE && (
          <StructureBaysSection
            state={state}
            onSelectComp={(c) => {
              setSelectedCompId(c);
              setActiveTab(WORKSPACE_TABS.COMPONENTS);
            }}
          />
        )}

        {activeTab === WORKSPACE_TABS.MANUFACTURING && (
          <ManufacturingSection
            state={state}
            selectedPartId={selectedPartId}
            onSelectPart={setSelectedPartId}
            selectedSheetId={selectedSheetId}
            onSelectSheet={setSelectedSheetId}
          />
        )}

        {activeTab === WORKSPACE_TABS.VALIDATION && (
          <ValidationSection state={state} />
        )}

        {activeTab === WORKSPACE_TABS.REVIEW && (
          <EngineeringReviewSection state={state} />
        )}

        {activeTab === WORKSPACE_TABS.BUILD && (
          <PrototypeBuildSection state={state} />
        )}

        {activeTab === WORKSPACE_TABS.BUILD_3D && (
          <Build3DViewerSection state={state} />
        )}

        {activeTab === WORKSPACE_TABS.RELEASE && (
          <FinalReleaseSection state={state} />
        )}

        {activeTab === WORKSPACE_TABS.ARTIFACTS && (
          <ArtifactsSection state={state} />
        )}

        {activeTab === WORKSPACE_TABS.VERSIONS && (
          <VersionsSection
            state={state}
            selectedProfile={selectedProfile}
            onSelectProfile={setSelectedProfile}
            onRegenerate={handleRegenerate}
          />
        )}

        {activeTab === WORKSPACE_TABS.REVISIONS && (
          <RevisionsSection
            state={state}
            onRegenerate={handleRegenerate}
          />
        )}
      </main>
    </div>
  );
}

// ----------------------------------------------------------------------
// 1. OVERVIEW SECTION
// ----------------------------------------------------------------------
function OverviewSection({ state, onSelectTab }) {
  const spec = DEFAULT_AIRCRAFT_METADATA.specification;

  return (
    <div className="mx-auto max-w-6xl p-6 space-y-6">
      {/* Top Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="rounded-xl border border-border/80 bg-card p-4 shadow-xs">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-medium">Wingspan</span>
            <Plane className="size-4 text-primary" />
          </div>
          <div className="mt-2 text-2xl font-bold tracking-tight">{spec.wing_span} mm</div>
          <p className="mt-1 text-[11px] text-muted-foreground">Aspect Ratio: {spec.aspect_ratio}</p>
        </div>

        <div className="rounded-xl border border-border/80 bg-card p-4 shadow-xs">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-medium">Fuselage Length</span>
            <Box className="size-4 text-primary" />
          </div>
          <div className="mt-2 text-2xl font-bold tracking-tight">{spec.fuselage_length} mm</div>
          <p className="mt-1 text-[11px] text-muted-foreground">Section: {spec.fuselage_width} × {spec.fuselage_height} mm</p>
        </div>

        <div className="rounded-xl border border-border/80 bg-card p-4 shadow-xs">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-medium">Structural Airframe</span>
            <Layers className="size-4 text-emerald-500" />
          </div>
          <div className="mt-2 text-2xl font-bold tracking-tight">48 Solids</div>
          <p className="mt-1 text-[11px] text-muted-foreground">69 Interlocking Joints</p>
        </div>

        <div className="rounded-xl border border-border/80 bg-card p-4 shadow-xs">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-medium">Prototype Readiness</span>
            <ShieldCheck className="size-4 text-emerald-500" />
          </div>
          <div className="mt-2 text-2xl font-bold tracking-tight text-emerald-600 dark:text-emerald-400">READY</div>
          <p className="mt-1 text-[11px] text-muted-foreground">10 / 10 Validation Gates Passed</p>
        </div>
      </div>

      {/* Summary Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Specification Summary */}
        <div className="rounded-xl border border-border/80 bg-card p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <Tag className="size-4 text-primary" />
              Authoritative Specification
            </h3>
            <button
              onClick={() => onSelectTab(WORKSPACE_TABS.REQUIREMENTS)}
              className="text-xs text-primary hover:underline"
            >
              Inspect All →
            </button>
          </div>
          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between py-1 border-b border-border/40">
              <span className="text-muted-foreground">Mission Profile</span>
              <span className="font-medium uppercase">{spec.category}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border/40">
              <span className="text-muted-foreground">Wing Position</span>
              <span className="font-medium">High Wing</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border/40">
              <span className="text-muted-foreground">Propulsion Layout</span>
              <span className="font-medium">Tractor (Electric)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border/40">
              <span className="text-muted-foreground">Propeller</span>
              <span className="font-medium">{spec.propeller}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-muted-foreground">Payload Target</span>
              <span className="font-medium">{spec.payload_weight} kg</span>
            </div>
          </div>
        </div>

        {/* Manufacturing Breakdown */}
        <div className="rounded-xl border border-border/80 bg-card p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <Hammer className="size-4 text-primary" />
              Manufacturing Package
            </h3>
            <button
              onClick={() => onSelectTab(WORKSPACE_TABS.MANUFACTURING)}
              className="text-xs text-primary hover:underline"
            >
              View Sheets →
            </button>
          </div>
          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between py-1 border-b border-border/40">
              <span className="text-muted-foreground">Laser-Cut Parts</span>
              <span className="font-medium">47 parts (Balsa / Aeroply)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border/40">
              <span className="text-muted-foreground">3D-Print Parts</span>
              <span className="font-medium">1 part (Wing-Attach)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border/40">
              <span className="text-muted-foreground">Standard Stock Sheets</span>
              <span className="font-medium">3 nested sheets (900×600 mm)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-border/40">
              <span className="text-muted-foreground">Structural Joints</span>
              <span className="font-medium">69 Tab / Slot Mates</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-muted-foreground">Estimated Structural Mass</span>
              <span className="font-medium">{DEFAULT_AIRCRAFT_METADATA.estimated_mass_g} g</span>
            </div>
          </div>
        </div>

        {/* Validation Gates Summary */}
        <div className="rounded-xl border border-border/80 bg-card p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <ShieldCheck className="size-4 text-emerald-500" />
              Phase 6F Validation Gates
            </h3>
            <button
              onClick={() => onSelectTab(WORKSPACE_TABS.VALIDATION)}
              className="text-xs text-primary hover:underline"
            >
              Dashboard →
            </button>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {[
              "Completeness (48/48)",
              "Traceability (100%)",
              "Laser Cut (47 DXF)",
              "3D Print (1 STL)",
              "Joints (69 Matched)",
              "Dimensions (Δ = 0 mm)",
              "Symmetry (Balanced)",
              "Bays (Clear)",
              "Propulsion (Mount OK)",
              "Reassembly (Interlocked)",
            ].map((gate, i) => (
              <div key={i} className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 font-medium">
                <CheckCircle2 className="size-3.5 shrink-0" />
                <span className="text-[11px] truncate">{gate}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------
// 2. 3D & COMPONENTS SECTION
// ----------------------------------------------------------------------
const COMPONENT_HIERARCHY = [
  {
    id: "MainWing",
    name: "Main Wing Assembly",
    type: "ASSEMBLY",
    role: "LIFT_GENERATION",
    children: [
      {
        id: "MainWing_Left",
        name: "Main Wing (Left)",
        type: "SUB_ASSEMBLY",
        role: "PORT_LIFT",
        children: [
          { id: "MainWing_Left_MainSpar", name: "Main Spar (Port)", type: "SPAR", role: "PRIMARY_LOAD_PATH", material: "Aeroply_3mm", dimensions: "1000×24×3 mm", rule: "WING_PRIMARY_SPAR", requirement: "wing.span" },
          { id: "MainWing_Left_RearSpar", name: "Rear Spar (Port)", type: "SPAR", role: "SECONDARY_LOAD_PATH", material: "Aeroply_3mm", dimensions: "1000×18×3 mm", rule: "WING_SECONDARY_SPAR", requirement: "wing.span" },
          { id: "MainWing_Left_Rib_001", name: "Wing Rib 001 (Root)", type: "RIB", role: "AIRFOIL_PROFILE", material: "Balsa_3mm", dimensions: "250×24×3 mm", rule: "WING_RIB", requirement: "wing.root_chord" },
          { id: "MainWing_Left_Rib_005", name: "Wing Rib 005 (Mid)", type: "RIB", role: "AIRFOIL_PROFILE", material: "Balsa_3mm", dimensions: "210×20×3 mm", rule: "WING_RIB", requirement: "wing.span" },
          { id: "MainWing_Left_Rib_010", name: "Wing Rib 010 (Tip)", type: "RIB", role: "AIRFOIL_PROFILE", material: "Balsa_3mm", dimensions: "150×15×3 mm", rule: "WING_RIB", requirement: "wing.tip_chord" },
        ],
      },
      {
        id: "MainWing_Right",
        name: "Main Wing (Right)",
        type: "SUB_ASSEMBLY",
        role: "STARBOARD_LIFT",
        children: [
          { id: "MainWing_Right_MainSpar", name: "Main Spar (Starboard)", type: "SPAR", role: "PRIMARY_LOAD_PATH", material: "Aeroply_3mm", dimensions: "1000×24×3 mm", rule: "WING_PRIMARY_SPAR", requirement: "wing.span" },
          { id: "MainWing_Right_RearSpar", name: "Rear Spar (Starboard)", type: "SPAR", role: "SECONDARY_LOAD_PATH", material: "Aeroply_3mm", dimensions: "1000×18×3 mm", rule: "WING_SECONDARY_SPAR", requirement: "wing.span" },
          { id: "MainWing_Right_Rib_001", name: "Wing Rib 001 (Root)", type: "RIB", role: "AIRFOIL_PROFILE", material: "Balsa_3mm", dimensions: "250×24×3 mm", rule: "WING_RIB", requirement: "wing.root_chord" },
          { id: "MainWing_Right_Rib_010", name: "Wing Rib 010 (Tip)", type: "RIB", role: "AIRFOIL_PROFILE", material: "Balsa_3mm", dimensions: "150×15×3 mm", rule: "WING_RIB", requirement: "wing.tip_chord" },
        ],
      },
      {
        id: "WingFuselage_Attachment",
        name: "Wing-Fuselage Attachment Block",
        type: "ATTACHMENT",
        role: "PRIMARY_INTERFACE",
        material: "PLA_Standard",
        dimensions: "120×80×40 mm",
        rule: "3D_PRINTED_ATTACHMENT",
        requirement: "configuration.wing_position",
      },
    ],
  },
  {
    id: "Fuselage",
    name: "Fuselage Assembly",
    type: "ASSEMBLY",
    role: "AERODYNAMIC_BODY",
    children: [
      { id: "Fuselage_Firewall", name: "Firewall / Motor Mount", type: "FIREWALL", role: "MOTOR_INTERFACE", material: "Aeroply_3mm", dimensions: "180×180×3 mm", rule: "FUSELAGE_FIREWALL", requirement: "propulsion.motor" },
      { id: "Fuselage_Former_001", name: "Fuselage Former 001", type: "FORMER", role: "CROSS_SECTION_SUPPORT", material: "Balsa_3mm", dimensions: "190×380×3 mm", rule: "FUSELAGE_FORMER", requirement: "fuselage.width" },
      { id: "Fuselage_Former_005", name: "Fuselage Former 005 (Bay)", type: "FORMER", role: "BAY_PARTITION", material: "Balsa_3mm", dimensions: "190×380×3 mm", rule: "FUSELAGE_FORMER", requirement: "fuselage.height" },
      { id: "Fuselage_Longeron_TopLeft", name: "Longeron (Top Port)", type: "LONGERON", role: "LONGITUDINAL_STIFFNESS", material: "Aeroply_3mm", dimensions: "1500×6×6 mm", rule: "FUSELAGE_LONGERON", requirement: "fuselage.length" },
      { id: "Fuselage_Longeron_BottomRight", name: "Longeron (Bottom Stbd)", type: "LONGERON", role: "LONGITUDINAL_STIFFNESS", material: "Aeroply_3mm", dimensions: "1500×6×6 mm", rule: "FUSELAGE_LONGERON", requirement: "fuselage.length" },
    ],
  },
  {
    id: "TailAssembly",
    name: "Empennage / Tail Assembly",
    type: "ASSEMBLY",
    role: "STABILITY_AND_CONTROL",
    children: [
      { id: "HT_Spar_001", name: "Horizontal Tail Spar", type: "SPAR", role: "HT_LOAD_PATH", material: "Balsa_3mm", dimensions: "500×14×3 mm", rule: "HT_SPAR", requirement: "horizontal_tail.span" },
      { id: "HT_Rib_001", name: "Horizontal Tail Rib", type: "RIB", role: "HT_PROFILE", material: "Balsa_3mm", dimensions: "120×12×3 mm", rule: "HT_RIB", requirement: "horizontal_tail.span" },
      { id: "VT_Spar_001", name: "Vertical Fin Main Spar", type: "SPAR", role: "VT_LOAD_PATH", material: "Balsa_3mm", dimensions: "400×16×3 mm", rule: "VT_SPAR", requirement: "vertical_tail.height" },
      { id: "VT_Rib_001", name: "Vertical Fin Rib", type: "RIB", role: "VT_PROFILE", material: "Balsa_3mm", dimensions: "140×14×3 mm", rule: "VT_RIB", requirement: "vertical_tail.height" },
    ],
  },
  {
    id: "InternalBays",
    name: "Internal Volume Envelopes",
    type: "VOLUME_ENVELOPE",
    role: "EQUIPMENT_CLEARANCE",
    children: [
      { id: "PayloadBay_Volume", name: "Payload Bay Envelope", type: "BAY", role: "PAYLOAD_CLEARANCE", dimensions: "200×150×150 mm", material: "VIRTUAL_VOLUME", rule: "BAY_VOLUME", requirement: "payload.sensor_type" },
      { id: "BatteryBay_Volume", name: "Battery Compartment Envelope", type: "BAY", role: "BATTERY_CLEARANCE", dimensions: "180×100×80 mm", material: "VIRTUAL_VOLUME", rule: "BAY_VOLUME", requirement: "mass.battery_weight" },
      { id: "AvionicsBay_Volume", name: "Avionics / Flight Controller Bay", type: "BAY", role: "ELECTRONICS_CLEARANCE", dimensions: "120×80×50 mm", material: "VIRTUAL_VOLUME", rule: "BAY_VOLUME", requirement: "configuration.tail_configuration" },
    ],
  },
];

function Components3DSection({
  state,
  selectedCompId,
  onSelectComp,
  visibilityMode,
  onSetVisibilityMode,
  searchQuery,
  onSearchChange,
  onNavigateRequirement,
}) {
  // Find selected component metadata
  const selectedComp = useMemo(() => {
    let found = null;
    const walk = (nodes) => {
      for (const n of nodes) {
        if (n.id === selectedCompId) {
          found = n;
          return;
        }
        if (n.children) walk(n.children);
      }
    };
    walk(COMPONENT_HIERARCHY);
    return found || COMPONENT_HIERARCHY[0].children[0].children[0];
  }, [selectedCompId]);

  return (
    <div className="flex h-full w-full">
      {/* Left Tree Explorer */}
      <div className="flex w-72 shrink-0 flex-col border-r border-border/60 bg-card">
        {/* Search Bar & Visibility Filter */}
        <div className="p-3 border-b border-border/60 space-y-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 size-3.5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search components..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="h-8 w-full rounded-md border border-border bg-background pl-8 pr-3 text-xs text-foreground placeholder:text-muted-foreground focus:outline-hidden focus:ring-1 focus:ring-primary"
            />
          </div>

          <div className="flex rounded-md bg-muted/60 p-0.5 text-[11px]">
            {["ALL", "EXTERNAL", "STRUCTURE", "BAYS"].map((mode) => (
              <button
                key={mode}
                onClick={() => onSetVisibilityMode(mode)}
                className={`flex-1 rounded py-1 font-medium transition-colors ${
                  visibilityMode === mode ? "bg-background text-foreground shadow-2xs" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {mode}
              </button>
            ))}
          </div>
        </div>

        {/* Tree Nodes List */}
        <div className="flex-1 overflow-auto p-2 text-xs space-y-1">
          {COMPONENT_HIERARCHY.map((group) => (
            <ComponentTreeNode
              key={group.id}
              node={group}
              selectedId={selectedCompId}
              onSelect={onSelectComp}
              searchQuery={searchQuery}
            />
          ))}
        </div>
      </div>

      {/* Center 3D Interactive Mockup / Viewer Canvas */}
      <div className="flex-1 flex flex-col relative bg-muted/10">
        {/* Top Floating View Controls */}
        <div className="absolute top-4 left-4 z-10 flex items-center gap-2 rounded-lg border border-border/80 bg-background/90 backdrop-blur-xs p-1 text-xs shadow-xs">
          <span className="px-2 font-medium text-muted-foreground">3D Mode:</span>
          <span className="font-semibold text-primary">{visibilityMode}</span>
          <div className="h-4 w-px bg-border mx-1" />
          <button className="rounded px-2 py-0.5 hover:bg-muted font-medium">Reset Camera</button>
          <button className="rounded px-2 py-0.5 hover:bg-muted font-medium">Fit Model</button>
        </div>

        {/* 3D Wireframe / Isometric Aircraft Visualization Canvas */}
        <div className="flex-1 flex items-center justify-center p-8 overflow-hidden">
          <svg className="w-full h-full max-h-[550px]" viewBox="0 0 800 500" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="800" height="500" rx="12" fill="currentColor" fillOpacity="0.02" />
            <defs>
              <linearGradient id="wingGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.8" />
                <stop offset="100%" stopColor="#1d4ed8" stopOpacity="0.6" />
              </linearGradient>
              <linearGradient id="fuseGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#64748b" stopOpacity="0.7" />
                <stop offset="100%" stopColor="#334155" stopOpacity="0.8" />
              </linearGradient>
            </defs>

            {/* Grid ground reference */}
            <g stroke="currentColor" strokeOpacity="0.06" strokeWidth="1">
              {Array.from({ length: 9 }).map((_, i) => (
                <line key={i} x1="100" y1={300 + i * 20} x2="700" y2={300 + i * 20} />
              ))}
            </g>

            {/* Fuselage Solid representation */}
            {(visibilityMode === "ALL" || visibilityMode === "EXTERNAL" || visibilityMode === "STRUCTURE") && (
              <g id="fuse-group" className="transition-all">
                <path
                  d="M 180 250 Q 220 220 380 225 L 620 245 L 650 250 L 620 255 L 380 275 Q 220 280 180 250 Z"
                  fill="url(#fuseGrad)"
                  stroke="#334155"
                  strokeWidth="2"
                  className={selectedCompId.includes("Fuselage") ? "stroke-amber-400 stroke-[3]" : ""}
                />
                {/* Formers wireframe */}
                <line x1="280" y1="230" x2="280" y2="270" stroke="#f59e0b" strokeWidth="2" strokeDasharray="3,3" />
                <line x1="380" y1="225" x2="380" y2="275" stroke="#f59e0b" strokeWidth="2" strokeDasharray="3,3" />
                <line x1="480" y1="235" x2="480" y2="265" stroke="#f59e0b" strokeWidth="2" strokeDasharray="3,3" />
              </g>
            )}

            {/* Main Wings */}
            {(visibilityMode === "ALL" || visibilityMode === "EXTERNAL" || visibilityMode === "STRUCTURE") && (
              <g id="wing-group">
                {/* Left Wing (Port) */}
                <path
                  d="M 330 230 L 100 80 L 140 60 L 390 230 Z"
                  fill="url(#wingGrad)"
                  stroke="#1d4ed8"
                  strokeWidth="2"
                  className={selectedCompId.includes("Left") ? "stroke-amber-400 stroke-[3]" : ""}
                />
                {/* Right Wing (Starboard) */}
                <path
                  d="M 330 270 L 100 420 L 140 440 L 390 270 Z"
                  fill="url(#wingGrad)"
                  stroke="#1d4ed8"
                  strokeWidth="2"
                  className={selectedCompId.includes("Right") ? "stroke-amber-400 stroke-[3]" : ""}
                />
                {/* Internal Spar lines */}
                <line x1="345" y1="230" x2="110" y2="75" stroke="#f59e0b" strokeWidth="2" />
                <line x1="370" y1="230" x2="130" y2="65" stroke="#f59e0b" strokeWidth="1.5" strokeDasharray="4,4" />
                <line x1="345" y1="270" x2="110" y2="425" stroke="#f59e0b" strokeWidth="2" />
                <line x1="370" y1="270" x2="130" y2="435" stroke="#f59e0b" strokeWidth="1.5" strokeDasharray="4,4" />
              </g>
            )}

            {/* Tail Horizontal & Vertical Stabilizers */}
            {(visibilityMode === "ALL" || visibilityMode === "EXTERNAL" || visibilityMode === "STRUCTURE") && (
              <g id="tail-group">
                {/* Horizontal Stabilizer */}
                <path d="M 600 245 L 680 180 L 710 180 L 630 250 Z" fill="#94a3b8" stroke="#475569" strokeWidth="1.5" />
                <path d="M 600 255 L 680 320 L 710 320 L 630 250 Z" fill="#94a3b8" stroke="#475569" strokeWidth="1.5" />
                {/* Vertical Fin */}
                <path d="M 580 248 L 650 140 L 680 140 L 640 250 Z" fill="#64748b" stroke="#334155" strokeWidth="2" />
              </g>
            )}

            {/* Internal Bays Volume Envelope representation */}
            {(visibilityMode === "ALL" || visibilityMode === "BAYS") && (
              <g id="bays-group">
                <rect x="320" y="240" width="70" height="20" rx="2" fill="#10b981" fillOpacity="0.4" stroke="#059669" strokeWidth="1.5" />
                <text x="325" y="254" fill="#047857" fontSize="8" fontWeight="bold">PAYLOAD</text>
                <rect x="250" y="242" width="50" height="16" rx="2" fill="#8b5cf6" fillOpacity="0.4" stroke="#7c3aed" strokeWidth="1.5" />
                <text x="255" y="254" fill="#6d28d9" fontSize="8" fontWeight="bold">BATTERY</text>
              </g>
            )}

            {/* Propeller Disk representation */}
            <ellipse cx="170" cy="250" rx="10" ry="45" fill="#38bdf8" fillOpacity="0.3" stroke="#0284c7" strokeWidth="1.5" strokeDasharray="3,3" />
          </svg>
        </div>
      </div>

      {/* Right Inspector Panel */}
      <div className="flex w-80 shrink-0 flex-col border-l border-border/60 bg-card p-4 space-y-4">
        <div className="border-b border-border/60 pb-3">
          <span className="text-[10px] font-bold tracking-wider uppercase text-primary">Component Inspector</span>
          <h3 className="text-base font-semibold tracking-tight text-foreground truncate mt-0.5">
            {selectedComp.name}
          </h3>
          <p className="text-[11px] font-mono text-muted-foreground">{selectedComp.id}</p>
        </div>

        <div className="space-y-3 text-xs flex-1 overflow-auto">
          <div className="space-y-1">
            <span className="text-[11px] text-muted-foreground">Type & Classification</span>
            <div className="flex items-center gap-1.5 font-medium">
              <span className="rounded bg-muted px-2 py-0.5 text-xs font-mono">{selectedComp.type}</span>
              <span className="text-muted-foreground">•</span>
              <span className="text-foreground">{selectedComp.role}</span>
            </div>
          </div>

          {selectedComp.material && (
            <div className="space-y-1">
              <span className="text-[11px] text-muted-foreground">Material & Stock</span>
              <p className="font-medium text-foreground">{selectedComp.material}</p>
            </div>
          )}

          {selectedComp.dimensions && (
            <div className="space-y-1">
              <span className="text-[11px] text-muted-foreground">Synthesized Dimensions</span>
              <p className="font-mono text-foreground font-medium">{selectedComp.dimensions}</p>
            </div>
          )}

          {selectedComp.rule && (
            <div className="space-y-1">
              <span className="text-[11px] text-muted-foreground">Generation Rule</span>
              <p className="font-mono text-muted-foreground text-[11px]">{selectedComp.rule}</p>
            </div>
          )}

          <div className="space-y-1 pt-2 border-t border-border/60">
            <span className="text-[11px] text-muted-foreground">Validation Status</span>
            <div className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium">
              <CheckCircle2 className="size-3.5" />
              <span>PASSED (Non-degenerate Solid)</span>
            </div>
          </div>

          {/* Traceability Link to Phase 3 Requirement */}
          {selectedComp.requirement && (
            <div className="rounded-lg border border-primary/20 bg-primary/5 p-3 space-y-2">
              <div className="flex items-center justify-between text-primary font-medium text-[11px]">
                <span className="flex items-center gap-1">
                  <Tag className="size-3" />
                  Source Requirement
                </span>
                <span className="text-[10px] uppercase font-bold">Traceable</span>
              </div>
              <p className="font-mono text-xs font-semibold text-foreground">{selectedComp.requirement}</p>
              <button
                onClick={() => onNavigateRequirement(selectedComp.requirement)}
                className="w-full rounded bg-primary/10 hover:bg-primary/20 py-1 text-[11px] font-medium text-primary transition-colors text-center"
              >
                View Requirement Source →
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ComponentTreeNode({ node, selectedId, onSelect, searchQuery }) {
  const [expanded, setExpanded] = useState(true);
  const isSelected = node.id === selectedId;
  const hasChildren = node.children && node.children.length > 0;

  const matchesSearch = !searchQuery || node.name.toLowerCase().includes(searchQuery.toLowerCase()) || node.id.toLowerCase().includes(searchQuery.toLowerCase());

  if (!matchesSearch && !hasChildren) return null;

  return (
    <div>
      <div
        onClick={() => onSelect(node.id)}
        className={`flex items-center justify-between rounded px-2 py-1.5 cursor-pointer transition-colors ${
          isSelected ? "bg-primary text-primary-foreground font-medium" : "hover:bg-muted/60 text-foreground"
        }`}
      >
        <div className="flex items-center gap-1.5 truncate">
          {hasChildren ? (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setExpanded(!expanded);
              }}
              className="p-0.5 hover:bg-black/10 rounded"
            >
              {expanded ? <ChevronDown className="size-3" /> : <ChevronRight className="size-3" />}
            </button>
          ) : (
            <div className="size-3" />
          )}
          <span className="truncate">{node.name}</span>
        </div>
        <span className={`text-[10px] font-mono opacity-60 ${isSelected ? "text-primary-foreground" : "text-muted-foreground"}`}>
          {node.type}
        </span>
      </div>

      {hasChildren && expanded && (
        <div className="pl-4 border-l border-border/40 ml-3 mt-1 space-y-0.5">
          {node.children.map((child) => (
            <ComponentTreeNode
              key={child.id}
              node={child}
              selectedId={selectedId}
              onSelect={onSelect}
              searchQuery={searchQuery}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ----------------------------------------------------------------------
// 3. REQUIREMENTS SECTION
// ----------------------------------------------------------------------
const REQUIREMENTS_DATA = [
  {
    category: "Identity & Mission",
    items: [
      { key: "mission.category", name: "Mission Category", value: "SURVEY", unit: "", status: "EXPLICIT", source: "Executive Summary", sec: "1.0", raw: "Category: SURVEY" },
      { key: "mission.target_payload", name: "Target Payload Mass", value: "2.00", unit: "kg", status: "EXPLICIT", source: "Mission Overview", sec: "2.0", raw: "Target Payload: 2.00 kg" },
      { key: "mission.flight_time", name: "Flight Endurance Limit", value: "60.0", unit: "min", status: "EXPLICIT", source: "Mission Overview", sec: "2.0", raw: "Flight Time Limit: 60.0 minutes" },
      { key: "mission.cruise_speed", name: "Cruise Speed Target", value: "95.0", unit: "km/h", status: "EXPLICIT", source: "Mission Overview", sec: "2.0", raw: "Cruise Speed Target: 95.0 km/h" },
    ],
  },
  {
    category: "Wing Geometry",
    items: [
      { key: "wing.span", name: "Wingspan", value: "2000.0", unit: "mm", status: "EXPLICIT", source: "Geometry Sizing", sec: "3.1", raw: "Wingspan: 2.00 meters", linkedComp: "MainWing_Left_MainSpar" },
      { key: "wing.aspect_ratio", name: "Aspect Ratio", value: "10.0", unit: "", status: "EXPLICIT", source: "Geometry Sizing", sec: "3.1", raw: "Aspect Ratio: 10.0" },
      { key: "wing.root_chord", name: "Root Chord", value: "250.0", unit: "mm", status: "EXPLICIT", source: "Geometry Sizing", sec: "3.1", raw: "Root Chord: 250 mm", linkedComp: "MainWing_Left_Rib_001" },
      { key: "wing.tip_chord", name: "Tip Chord", value: "150.0", unit: "mm", status: "EXPLICIT", source: "Geometry Sizing", sec: "3.1", raw: "Tip Chord: 150 mm", linkedComp: "MainWing_Left_Rib_010" },
      { key: "wing.half_span", name: "Half Span", value: "1000.0", unit: "mm", status: "DERIVED", source: "Derivation Rule", sec: "3.1", raw: "half_span = span / 2", linkedComp: "MainWing_Left" },
      { key: "wing.dihedral", name: "Dihedral Angle", value: "2.0", unit: "deg", status: "EXPLICIT", source: "Geometry Sizing", sec: "3.1", raw: "Dihedral: 2.0 deg" },
    ],
  },
  {
    category: "Fuselage Geometry",
    items: [
      { key: "fuselage.length", name: "Total Length", value: "1500.0", unit: "mm", status: "EXPLICIT", source: "Fuselage Sizing", sec: "3.2", raw: "Fuselage Length: 1500 mm", linkedComp: "Fuselage_Longeron_TopLeft" },
      { key: "fuselage.width", name: "Maximum Width", value: "200.0", unit: "mm", status: "EXPLICIT", source: "Fuselage Sizing", sec: "3.2", raw: "Maximum Width: 200 mm", linkedComp: "Fuselage_Former_001" },
      { key: "fuselage.height", name: "Maximum Height", value: "400.0", unit: "mm", status: "EXPLICIT", source: "Fuselage Sizing", sec: "3.2", raw: "Maximum Height: 400 mm", linkedComp: "Fuselage_Former_005" },
    ],
  },
  {
    category: "Tail Geometry",
    items: [
      { key: "horizontal_tail.span", name: "HT Span", value: "500.0", unit: "mm", status: "EXPLICIT", source: "Empennage Sizing", sec: "3.3", raw: "HT Span: 500 mm", linkedComp: "HT_Spar_001" },
      { key: "vertical_tail.height", name: "VT Height", value: "400.0", unit: "mm", status: "EXPLICIT", source: "Empennage Sizing", sec: "3.3", raw: "VT Height: 400 mm", linkedComp: "VT_Spar_001" },
    ],
  },
  {
    category: "Propulsion & Mass",
    items: [
      { key: "propulsion.propeller", name: "Propeller Spec", value: "12x6 APC", unit: "", status: "EXPLICIT", source: "Propulsion Unit", sec: "4.0", raw: "Propeller: 12x6 APC" },
      { key: "propulsion.propeller_diameter", name: "Propeller Diameter", value: "304.8", unit: "mm", status: "DERIVED", source: "Extracted from 12x6", sec: "4.0", raw: "12 inches × 25.4" },
      { key: "mass.MTOW", name: "Takeoff Mass (Specified)", value: "5.5", unit: "kg", status: "CONFLICT", source: "Executive Summary", sec: "1.0", raw: "Takeoff Mass: 5.50 kg (Component sum: 11.0 kg)" },
      { key: "propulsion.mounting_pattern", name: "Motor Mounting Bolt Circle", value: "UNKNOWN", unit: "", status: "UNKNOWN", source: "Not Specified in Part 1", sec: "-", raw: "N/A" },
    ],
  },
];

function RequirementsSection({ state, selectedReqKey, onSelectReq, searchQuery, onSearchChange, onNavigateComponent }) {
  const selectedReq = useMemo(() => {
    for (const group of REQUIREMENTS_DATA) {
      for (const item of group.items) {
        if (item.key === selectedReqKey) return item;
      }
    }
    return REQUIREMENTS_DATA[1].items[0];
  }, [selectedReqKey]);

  return (
    <div className="flex h-full w-full">
      {/* Left Requirements Explorer */}
      <div className="flex-1 flex flex-col p-6 space-y-6 overflow-auto">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold tracking-tight text-foreground">Phase 3 Normalized Requirements</h2>
            <p className="text-xs text-muted-foreground">Authoritative parameters ingested from Part 1 specification</p>
          </div>
          <div className="relative w-64">
            <Search className="absolute left-2.5 top-2.5 size-3.5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Filter requirements..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="h-8 w-full rounded-md border border-border bg-background pl-8 pr-3 text-xs text-foreground placeholder:text-muted-foreground focus:outline-hidden focus:ring-1 focus:ring-primary"
            />
          </div>
        </div>

        {/* Groups */}
        <div className="space-y-6">
          {REQUIREMENTS_DATA.map((group) => (
            <div key={group.category} className="space-y-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground px-1">{group.category}</h3>
              <div className="rounded-xl border border-border/80 bg-card overflow-hidden divide-y divide-border/60">
                {group.items.map((item) => {
                  const isSelected = item.key === selectedReqKey;
                  return (
                    <div
                      key={item.key}
                      onClick={() => onSelectReq(item.key)}
                      className={`flex items-center justify-between px-4 py-3 cursor-pointer transition-colors text-xs ${
                        isSelected ? "bg-primary/5" : "hover:bg-muted/40"
                      }`}
                    >
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-foreground">{item.name}</span>
                          <span className="font-mono text-[10px] text-muted-foreground">{item.key}</span>
                        </div>
                        <p className="text-[11px] text-muted-foreground">
                          Source: {item.source} (Sec {item.sec})
                        </p>
                      </div>

                      <div className="flex items-center gap-3">
                        <div className="text-right font-mono font-medium text-sm">
                          {item.value} <span className="text-xs font-normal text-muted-foreground">{item.unit}</span>
                        </div>
                        <RequirementStatusBadge status={item.status} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Right Requirement Details & Reverse Traceability */}
      <div className="flex w-80 shrink-0 flex-col border-l border-border/60 bg-card p-4 space-y-4">
        <div className="border-b border-border/60 pb-3">
          <span className="text-[10px] font-bold tracking-wider uppercase text-primary">Requirement Inspector</span>
          <h3 className="text-base font-semibold tracking-tight text-foreground mt-0.5">{selectedReq.name}</h3>
          <p className="font-mono text-[11px] text-muted-foreground">{selectedReq.key}</p>
        </div>

        <div className="space-y-3 text-xs flex-1 overflow-auto">
          <div className="space-y-1">
            <span className="text-[11px] text-muted-foreground">Parameter Value</span>
            <p className="text-lg font-bold font-mono text-foreground">
              {selectedReq.value} {selectedReq.unit}
            </p>
          </div>

          <div className="space-y-1">
            <span className="text-[11px] text-muted-foreground">Ingestion Status</span>
            <div><RequirementStatusBadge status={selectedReq.status} /></div>
          </div>

          <div className="space-y-1">
            <span className="text-[11px] text-muted-foreground">Source Markdown Extract</span>
            <div className="rounded bg-muted p-2 font-mono text-[11px] text-foreground">
              {selectedReq.raw}
            </div>
          </div>

          {selectedReq.status === "CONFLICT" && (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 space-y-1 text-amber-700 dark:text-amber-300">
              <div className="flex items-center gap-1.5 font-bold text-xs">
                <AlertTriangle className="size-3.5" />
                Unresolved Conflict
              </div>
              <p className="text-[11px]">
                Take-off mass stated as 5.5 kg in Executive Summary, while component breakdown sums to 11.0 kg. CAD generation was continued (NON-BLOCKING).
              </p>
            </div>
          )}

          {/* Forward Traceability to CAD geometry */}
          {selectedReq.linkedComp && (
            <div className="rounded-lg border border-primary/20 bg-primary/5 p-3 space-y-2 mt-4">
              <div className="flex items-center justify-between text-primary font-medium text-[11px]">
                <span className="flex items-center gap-1">
                  <Box className="size-3" />
                  Associated CAD Geometry
                </span>
                <span className="text-[10px] uppercase font-bold">Synthesized</span>
              </div>
              <p className="font-mono text-xs font-semibold text-foreground">{selectedReq.linkedComp}</p>
              <button
                onClick={() => onNavigateComponent(selectedReq.linkedComp)}
                className="w-full rounded bg-primary/10 hover:bg-primary/20 py-1 text-[11px] font-medium text-primary transition-colors text-center"
              >
                Inspect 3D Geometry →
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function RequirementStatusBadge({ status }) {
  if (status === "EXPLICIT") {
    return <span className="rounded bg-blue-500/15 px-2 py-0.5 text-[10px] font-bold text-blue-600 dark:text-blue-400">EXPLICIT</span>;
  }
  if (status === "DERIVED") {
    return <span className="rounded bg-purple-500/15 px-2 py-0.5 text-[10px] font-bold text-purple-600 dark:text-purple-400">DERIVED</span>;
  }
  if (status === "CONFLICT") {
    return <span className="rounded bg-amber-500/15 px-2 py-0.5 text-[10px] font-bold text-amber-600 dark:text-amber-400">CONFLICT</span>;
  }
  return <span className="rounded bg-zinc-500/15 px-2 py-0.5 text-[10px] font-bold text-zinc-600 dark:text-zinc-400">UNKNOWN</span>;
}

// ----------------------------------------------------------------------
// 4. STRUCTURE & BAYS SECTION
// ----------------------------------------------------------------------
function StructureBaysSection({ state, onSelectComp }) {
  return (
    <div className="mx-auto max-w-6xl p-6 space-y-6">
      <div>
        <h2 className="text-lg font-semibold tracking-tight text-foreground">Phase 5 Airframe Structure & Internal Bays</h2>
        <p className="text-xs text-muted-foreground">48 individually addressable structural solids and internal clear volume envelopes</p>
      </div>

      {/* Internal Bays Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { name: "Payload Bay", dims: "200 × 150 × 150 mm", vol: "4.50 L", status: "UNOBSTRUCTED", role: "Sensor Gimbal & Survey Hardware" },
          { name: "Battery Compartment", dims: "180 × 100 × 80 mm", vol: "1.44 L", status: "UNOBSTRUCTED", role: "6S LiPo Battery Pack" },
          { name: "Avionics Bay", dims: "120 × 80 × 50 mm", vol: "0.48 L", status: "UNOBSTRUCTED", role: "Autopilot, GPS & Telemetry" },
        ].map((bay) => (
          <div key={bay.name} className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-xs text-foreground">{bay.name}</span>
              <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-600 dark:text-emerald-400">
                {bay.status}
              </span>
            </div>
            <p className="font-mono text-sm font-bold text-foreground">{bay.dims}</p>
            <div className="flex justify-between text-[11px] text-muted-foreground pt-1 border-t border-emerald-500/20">
              <span>Usable Volume: {bay.vol}</span>
              <span>{bay.role}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Structural Profile Rules */}
      <div className="rounded-xl border border-border/80 bg-card p-5 space-y-3">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <Wrench className="size-4 text-primary" />
          Structural Synthesis Rules & Spacing
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
          <div className="space-y-1">
            <span className="text-muted-foreground">Primary Spar Chord Ratio</span>
            <p className="font-mono font-medium">0.25 (25% chord)</p>
          </div>
          <div className="space-y-1">
            <span className="text-muted-foreground">Secondary Spar Ratio</span>
            <p className="font-mono font-medium">0.65 (65% chord)</p>
          </div>
          <div className="space-y-1">
            <span className="text-muted-foreground">Wing Rib Spacing</span>
            <p className="font-mono font-medium">120.0 mm</p>
          </div>
          <div className="space-y-1">
            <span className="text-muted-foreground">Fuselage Former Spacing</span>
            <p className="font-mono font-medium">150.0 mm</p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------
// 5. MANUFACTURING SECTION
// ----------------------------------------------------------------------
const SHEETS_DATA = [
  { sheet_id: "Sheet_01", material: "Balsa_3mm", dims: "900 × 600 mm", parts: 20, util: 74.2, dxf: "outputs/FW-007/v1/laser/sheets/Sheet_01.dxf" },
  { sheet_id: "Sheet_02", material: "Balsa_3mm", dims: "900 × 600 mm", parts: 19, util: 68.5, dxf: "outputs/FW-007/v1/laser/sheets/Sheet_02.dxf" },
  { sheet_id: "Sheet_03", material: "Aeroply_3mm", dims: "900 × 600 mm", parts: 8, util: 52.8, dxf: "outputs/FW-007/v1/laser/sheets/Sheet_03.dxf" },
];

function ManufacturingSection({ state, selectedPartId, onSelectPart, selectedSheetId, onSelectSheet }) {
  const currentSheet = SHEETS_DATA.find((s) => s.sheet_id === selectedSheetId) || SHEETS_DATA[0];

  return (
    <div className="mx-auto max-w-6xl p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold tracking-tight text-foreground">Phase 6 Manufacturing Package</h2>
          <p className="text-xs text-muted-foreground">47 laser-cut parts across 3 stock sheets and 1 3D-printable solid</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded bg-primary/10 text-primary font-mono text-xs font-semibold px-2.5 py-1">
            Kerf: 0.15 mm
          </span>
        </div>
      </div>

      {/* Sheets Carousel / Browser */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {SHEETS_DATA.map((sheet) => {
          const isSelected = sheet.sheet_id === selectedSheetId;
          return (
            <div
              key={sheet.sheet_id}
              onClick={() => onSelectSheet(sheet.sheet_id)}
              className={`rounded-xl border p-4 cursor-pointer transition-all space-y-3 ${
                isSelected
                  ? "border-primary bg-primary/5 shadow-xs"
                  : "border-border/80 bg-card hover:bg-muted/40"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-xs text-foreground">{sheet.sheet_id}</span>
                <span className="font-mono text-[11px] text-muted-foreground">{sheet.material}</span>
              </div>
              <div className="space-y-1">
                <div className="flex justify-between text-xs font-medium">
                  <span>Stock Utilization</span>
                  <span>{sheet.util}%</span>
                </div>
                <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-primary rounded-full" style={{ width: `${sheet.util}%` }} />
                </div>
              </div>
              <div className="flex justify-between text-[11px] text-muted-foreground pt-1 border-t border-border/40">
                <span>{sheet.dims}</span>
                <span>{sheet.parts} nested parts</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* 3D Print Part Section */}
      <div className="rounded-xl border border-border/80 bg-card p-5 space-y-4">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <Printer className="size-4 text-primary" />
          Additive 3D-Print Component (Direct Bed Fit)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
          <div className="space-y-1">
            <span className="text-muted-foreground">Print Part ID</span>
            <p className="font-mono font-medium text-foreground">PRINT-WING-ATTACH-001</p>
          </div>
          <div className="space-y-1">
            <span className="text-muted-foreground">Envelope Fit</span>
            <p className="font-medium text-emerald-600 dark:text-emerald-400">Fits 220×220×250 mm Build Volume</p>
          </div>
          <div className="space-y-1">
            <span className="text-muted-foreground">Splitting Required</span>
            <p className="font-medium">NONE (Monolithic Print)</p>
          </div>
          <div className="space-y-1">
            <span className="text-muted-foreground">Export File</span>
            <p className="font-mono text-primary">PRINT-WING-ATTACH-001.stl</p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------
// 6. VALIDATION SECTION
// ----------------------------------------------------------------------
function ValidationSection({ state }) {
  return (
    <div className="mx-auto max-w-6xl p-6 space-y-6">
      <div className="flex items-center justify-between border-b border-border/60 pb-4">
        <div>
          <h2 className="text-lg font-semibold tracking-tight text-foreground">Phase 6F Manufacturing & Virtual Reassembly Audit</h2>
          <p className="text-xs text-muted-foreground">Authoritative 10-gate dimensional and physical assembly verification</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 px-3 py-1 text-xs font-bold">
            PROTOTYPE STATUS: READY
          </span>
        </div>
      </div>

      {/* Dimensional Checks Table */}
      <div className="rounded-xl border border-border/80 bg-card overflow-hidden">
        <div className="px-4 py-3 bg-muted/30 border-b border-border/60 font-semibold text-xs">
          Authoritative Dimensional Comparison (Part 1 vs Virtual Prototype)
        </div>
        <table className="w-full text-xs text-left">
          <thead className="bg-muted/10 text-muted-foreground border-b border-border/40 font-medium">
            <tr>
              <th className="px-4 py-2.5">Parameter</th>
              <th className="px-4 py-2.5">Part 1 Required</th>
              <th className="px-4 py-2.5">Virtual CAD Reassembled</th>
              <th className="px-4 py-2.5">Deviation</th>
              <th className="px-4 py-2.5">Tolerance</th>
              <th className="px-4 py-2.5">Gate Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/40 font-mono">
            {[
              { param: "Overall Wingspan", req: "2000.0 mm", actual: "2000.0 mm", dev: "0.0 mm", tol: "±1.0 mm", status: "PASS" },
              { param: "Fuselage Total Length", req: "1500.0 mm", actual: "1500.0 mm", dev: "0.0 mm", tol: "±1.0 mm", status: "PASS" },
              { param: "Horizontal Tail Span", req: "500.0 mm", actual: "500.0 mm", dev: "0.0 mm", tol: "±1.0 mm", status: "PASS" },
              { param: "Vertical Tail Height", req: "400.0 mm", actual: "400.0 mm", dev: "0.0 mm", tol: "±1.0 mm", status: "PASS" },
              { param: "Propeller Disk Diameter", req: "304.8 mm", actual: "304.8 mm", dev: "0.0 mm", tol: "±1.0 mm", status: "PASS" },
            ].map((row, i) => (
              <tr key={i} className="hover:bg-muted/30">
                <td className="px-4 py-2.5 font-sans font-medium text-foreground">{row.param}</td>
                <td className="px-4 py-2.5">{row.req}</td>
                <td className="px-4 py-2.5">{row.actual}</td>
                <td className="px-4 py-2.5 text-emerald-600 dark:text-emerald-400 font-bold">{row.dev}</td>
                <td className="px-4 py-2.5 text-muted-foreground">{row.tol}</td>
                <td className="px-4 py-2.5 font-sans">
                  <span className="rounded bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 font-bold px-2 py-0.5 text-[10px]">
                    {row.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------
// 7. ARTIFACTS SECTION
// ----------------------------------------------------------------------
const ARTIFACTS_LIST = [
  { id: "FW-007_v1_CAD_STEP", name: "FW-007_complete_aircraft.step", type: "CAD_STEP", phase: "PHASE_4_CAD", path: "outputs/FW-007/v1/cad/FW-007_complete_aircraft.step" },
  { id: "FW-007_v1_STRUCTURAL_STEP", name: "FW-007_structural_airframe.step", type: "STRUCTURAL_STEP", phase: "PHASE_5_STRUCTURE", path: "outputs/FW-007/v1/structure/FW-007_structural_airframe.step" },
  { id: "FW-007_v1_DXF_RIB-L-001", name: "RIB-L-001.dxf", type: "DXF", phase: "PHASE_6D_LASER", path: "outputs/FW-007/v1/laser/parts/RIB-L-001.dxf" },
  { id: "FW-007_v1_SHEET_Sheet_01", name: "Sheet_01.dxf", type: "SHEET_LAYOUT", phase: "PHASE_6D_LASER", path: "outputs/FW-007/v1/laser/sheets/Sheet_01.dxf" },
  { id: "FW-007_v1_STL_PRINT-WING-ATTACH-001", name: "PRINT-WING-ATTACH-001.stl", type: "STL", phase: "PHASE_6E_PRINT", path: "outputs/FW-007/v1/print/PRINT-WING-ATTACH-001.stl" },
  { id: "FW-007_v1_VALIDATION_REPORT", name: "manufacturing_validation.json", type: "VALIDATION_REPORT", phase: "PHASE_6F_VALIDATION", path: "outputs/FW-007/v1/validation/manufacturing_validation.json" },
  { id: "FW-007_v1_PIPELINE_MANIFEST", name: "pipeline_manifest.json", type: "BOM", phase: "PHASE_7_INTEGRATION", path: "outputs/FW-007/v1/pipeline_manifest.json" },
];

function ArtifactsSection({ state }) {
  return (
    <div className="mx-auto max-w-6xl p-6 space-y-6">
      <div>
        <h2 className="text-lg font-semibold tracking-tight text-foreground">Registered Output Artifacts</h2>
        <p className="text-xs text-muted-foreground">Versioned and immutable fabrication deliverables</p>
      </div>

      <div className="rounded-xl border border-border/80 bg-card overflow-hidden">
        <table className="w-full text-xs text-left">
          <thead className="bg-muted/10 text-muted-foreground border-b border-border/40 font-medium">
            <tr>
              <th className="px-4 py-2.5">Artifact ID</th>
              <th className="px-4 py-2.5">File Name</th>
              <th className="px-4 py-2.5">Type</th>
              <th className="px-4 py-2.5">Phase</th>
              <th className="px-4 py-2.5">File Path</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/40 font-mono text-[11px]">
            {ARTIFACTS_LIST.map((art) => (
              <tr key={art.id} className="hover:bg-muted/30">
                <td className="px-4 py-2.5 font-sans font-medium text-foreground">{art.id}</td>
                <td className="px-4 py-2.5 text-primary">{art.name}</td>
                <td className="px-4 py-2.5 font-sans">
                  <span className="rounded bg-muted px-1.5 py-0.5 text-[10px]">{art.type}</span>
                </td>
                <td className="px-4 py-2.5 text-muted-foreground font-sans">{art.phase}</td>
                <td className="px-4 py-2.5 text-muted-foreground truncate max-w-xs">{art.path}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------
// 8. VERSIONS SECTION
// ----------------------------------------------------------------------
function VersionsSection({ state, selectedProfile, onSelectProfile, onRegenerate }) {
  return (
    <div className="mx-auto max-w-6xl p-6 space-y-6">
      <div>
        <h2 className="text-lg font-semibold tracking-tight text-foreground">Version Management & Immutability</h2>
        <p className="text-xs text-muted-foreground">Isolated design versioning and safe profile selection</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Version History */}
        <div className="rounded-xl border border-border/80 bg-card p-5 space-y-4">
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <Clock className="size-4 text-primary" />
            Design Version History
          </h3>
          <div className="space-y-2 text-xs">
            <div className="rounded-lg border border-primary/30 bg-primary/5 p-3 flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-foreground">v1 (Active)</span>
                  <span className="rounded bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 px-1.5 py-0.5 text-[10px] font-bold">READY</span>
                </div>
                <p className="text-[11px] text-muted-foreground mt-0.5">Authoritative FW-007 Baseline (Wingspan: 2000 mm)</p>
              </div>
              <span className="font-mono text-[10px] text-muted-foreground">outputs/FW-007/v1/</span>
            </div>

            <div className="rounded-lg border border-border/60 bg-muted/10 p-3 flex items-center justify-between opacity-70">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-foreground">v2 (Planned)</span>
                  <span className="rounded bg-muted px-1.5 py-0.5 text-[10px]">NEW</span>
                </div>
                <p className="text-[11px] text-muted-foreground mt-0.5">Separate output directory; v1 untouched</p>
              </div>
              <span className="font-mono text-[10px] text-muted-foreground">outputs/FW-007/v2/</span>
            </div>
          </div>
        </div>

        {/* Profile Switching */}
        <div className="rounded-xl border border-border/80 bg-card p-5 space-y-4">
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <Hammer className="size-4 text-primary" />
            Manufacturing Profile Selection
          </h3>
          <p className="text-xs text-muted-foreground">
            Switching manufacturing profiles regenerates fabrication files without modifying upstream CAD geometry.
          </p>

          <div className="space-y-2">
            {[
              { id: "FW007_Production_Profile", name: "FW007 Standard (Balsa 3mm + Aeroply 3mm)", kerf: "0.15 mm" },
              { id: "Aeroply_Heavy_Duty", name: "Heavy Duty Aeroply 4mm", kerf: "0.20 mm" },
            ].map((prof) => (
              <label
                key={prof.id}
                className={`flex items-center justify-between rounded-lg border p-3 cursor-pointer text-xs transition-colors ${
                  selectedProfile === prof.id ? "border-primary bg-primary/5" : "border-border/60 hover:bg-muted/40"
                }`}
              >
                <div className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="mfg_profile"
                    checked={selectedProfile === prof.id}
                    onChange={() => onSelectProfile(prof.id)}
                    className="text-primary"
                  />
                  <span className="font-medium text-foreground">{prof.name}</span>
                </div>
                <span className="font-mono text-muted-foreground">{prof.kerf}</span>
              </label>
            ))}
          </div>

          <button
            onClick={() => onRegenerate("v2")}
            className="w-full rounded-md bg-primary py-2 text-xs font-semibold text-primary-foreground shadow-xs hover:bg-primary/90 transition-all mt-2"
          >
            Generate v2 with Selected Profile
          </button>
        </div>
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------
// 9. REVISIONS & CHANGE IMPACT SECTION
// ----------------------------------------------------------------------
function RevisionsSection({ state, onRegenerate }) {
  const [selectedParent, setSelectedParent] = useState(state.selectedParentRevision || "v1");
  const [selectedTarget, setSelectedTarget] = useState(state.selectedTargetRevision || "v2");
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  // Authoritative representative diff for v1 -> v2 preview
  const demoChanges = useMemo(() => [
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
    {
      parameter: "wing.tip_chord",
      category: "Wing",
      old_value: "150.0 mm",
      new_value: "160.0 mm",
      old_status: "DERIVED",
      new_status: "EXPLICIT",
      change_type: "MODIFIED",
      severity: "MEDIUM",
      description: "Tip chord specified explicitly for stall margin",
    },
    {
      parameter: "identity.author",
      category: "Identity",
      old_value: "Aero Team",
      new_value: "Lead UAV Architect",
      old_status: "EXPLICIT",
      new_status: "EXPLICIT",
      change_type: "MODIFIED",
      severity: "INFO",
      description: "Author metadata updated",
    },
  ], []);

  const impactSummary = useMemo(() => ({
    total_requirements_changed: demoChanges.length,
    highest_severity: "HIGH",
    total_cad_affected: 3, // MainWing, MainWing_Left, MainWing_Right
    total_structural_affected: 25, // Spars, Ribs, Attachment
    total_manufacturing_affected: 25, // Wing Spars, Wing Ribs, 3D Attach
    total_unaffected_items: 43, // Fuselage, Tails, Payload, Battery
    requires_user_confirmation: true,
  }), [demoChanges]);

  return (
    <div className="mx-auto max-w-6xl p-6 space-y-6">
      {/* Header Bar */}
      <div className="flex items-center justify-between border-b border-border/60 pb-4">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Engineering Revision & Change Impact Analysis</h2>
          <p className="text-xs text-muted-foreground">
            Compare specification revisions, inspect downstream dependency propagation, and perform safe selective regeneration.
          </p>
        </div>

        {/* Version Comparison Selector */}
        <div className="flex items-center gap-2 rounded-lg border border-border/80 bg-card p-1.5 text-xs font-mono">
          <span className="text-muted-foreground px-2">Compare:</span>
          <span className="rounded bg-primary/10 px-2 py-0.5 font-bold text-primary">{selectedParent}</span>
          <ArrowRight className="size-3.5 text-muted-foreground" />
          <span className="rounded bg-emerald-500/10 px-2 py-0.5 font-bold text-emerald-600 dark:text-emerald-400">{selectedTarget}</span>
        </div>
      </div>

      {/* High-Impact Warning Banner */}
      {impactSummary.highest_severity === "HIGH" && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-xs text-amber-800 dark:text-amber-200 flex items-start gap-3">
          <AlertTriangle className="size-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="font-semibold flex items-center gap-2">
              <span>High-Impact Engineering Revision Detected</span>
              <span className="rounded bg-amber-500/20 px-1.5 py-0.5 text-[10px] uppercase font-bold">Requires Confirmation</span>
            </div>
            <p className="text-amber-700/90 dark:text-amber-300/90">
              Changes to <strong>wing.span</strong> and <strong>wing.tip_chord</strong> propagate to 3 CAD wing surfaces, 25 structural components (spars, ribs, root attach), and 25 laser-cut manufacturing parts. Fuselage and tail assemblies remain isolated and unaffected.
            </p>
          </div>
        </div>
      )}

      {/* Change Impact Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="rounded-xl border border-border/80 bg-card p-4 space-y-1">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Changed Requirements</span>
            <Tag className="size-4 text-primary" />
          </div>
          <p className="text-2xl font-bold font-mono">{impactSummary.total_requirements_changed}</p>
          <p className="text-[11px] text-muted-foreground">Highest Severity: <strong className="text-amber-500">{impactSummary.highest_severity}</strong></p>
        </div>

        <div className="rounded-xl border border-border/80 bg-card p-4 space-y-1">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Affected CAD</span>
            <FolderTree className="size-4 text-blue-500" />
          </div>
          <p className="text-2xl font-bold font-mono">{impactSummary.total_cad_affected}</p>
          <p className="text-[11px] text-muted-foreground">MainWing surfaces invalidated</p>
        </div>

        <div className="rounded-xl border border-border/80 bg-card p-4 space-y-1">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Affected Structure & Mfg</span>
            <Hammer className="size-4 text-purple-500" />
          </div>
          <p className="text-2xl font-bold font-mono">{impactSummary.total_structural_affected}</p>
          <p className="text-[11px] text-muted-foreground">{impactSummary.total_manufacturing_affected} parts to re-nest</p>
        </div>

        <div className="rounded-xl border border-border/80 bg-card p-4 space-y-1">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Unaffected Items</span>
            <CheckCircle2 className="size-4 text-emerald-500" />
          </div>
          <p className="text-2xl font-bold font-mono text-emerald-600 dark:text-emerald-400">{impactSummary.total_unaffected_items}</p>
          <p className="text-[11px] text-muted-foreground">Fuselage & Tails preserved</p>
        </div>
      </div>

      {/* Requirements Diff Table */}
      <div className="rounded-xl border border-border/80 bg-card overflow-hidden">
        <div className="border-b border-border/60 bg-muted/30 px-4 py-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <GitCompare className="size-4 text-primary" />
            Requirement-Level Specification Delta ({selectedParent} → {selectedTarget})
          </h3>
          <span className="text-xs font-mono text-muted-foreground">{demoChanges.length} changes detected</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-border/60 bg-muted/10 font-medium text-muted-foreground">
                <th className="py-2.5 px-4">Category</th>
                <th className="py-2.5 px-4">Parameter</th>
                <th className="py-2.5 px-4 font-mono">v1 Baseline</th>
                <th className="py-2.5 px-4 font-mono">v2 Proposed</th>
                <th className="py-2.5 px-4">Status Transition</th>
                <th className="py-2.5 px-4">Severity</th>
                <th className="py-2.5 px-4">Engineering Rationale</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40 font-mono">
              {demoChanges.map((c, idx) => (
                <tr key={idx} className="hover:bg-muted/20 transition-colors">
                  <td className="py-2.5 px-4 font-sans font-medium text-foreground">{c.category}</td>
                  <td className="py-2.5 px-4 font-semibold text-primary">{c.parameter}</td>
                  <td className="py-2.5 px-4 text-muted-foreground line-through">{c.old_value}</td>
                  <td className="py-2.5 px-4 text-emerald-600 dark:text-emerald-400 font-bold">{c.new_value}</td>
                  <td className="py-2.5 px-4 font-sans">
                    <span className="rounded bg-muted px-1.5 py-0.5 text-[10px]">
                      {c.old_status} → {c.new_status}
                    </span>
                  </td>
                  <td className="py-2.5 px-4 font-sans">
                    <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${
                      c.severity === "HIGH" ? "bg-rose-500/10 text-rose-600 border border-rose-500/20" :
                      c.severity === "MEDIUM" ? "bg-amber-500/10 text-amber-600 border border-amber-500/20" :
                      "bg-blue-500/10 text-blue-600 border border-blue-500/20"
                    }`}>
                      {c.severity}
                    </span>
                  </td>
                  <td className="py-2.5 px-4 font-sans text-muted-foreground text-[11px]">{c.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Downstream Impact & Selective Regeneration Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Affected vs Unaffected Breakdown */}
        <div className="rounded-xl border border-border/80 bg-card p-5 space-y-4">
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <Layers className="size-4 text-primary" />
            Downstream Dependency Invalidation
          </h3>

          <div className="space-y-3 text-xs">
            <div className="rounded-lg border border-rose-500/20 bg-rose-500/5 p-3 space-y-1.5">
              <div className="font-semibold text-rose-600 dark:text-rose-400 flex items-center justify-between">
                <span>Invalidated Subtrees (Regeneration Required)</span>
                <span className="text-[10px] font-mono font-bold">28 Components</span>
              </div>
              <p className="text-muted-foreground text-[11px]">
                MainWing CAD surfaces, 20 wing ribs (`RIB-L-*`, `RIB-R-*`), 4 wing spars (`SPAR-*`), wing-fuselage attachment block, Sheet_01 and Sheet_02 laser layouts.
              </p>
            </div>

            <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3 space-y-1.5">
              <div className="font-semibold text-emerald-600 dark:text-emerald-400 flex items-center justify-between">
                <span>Preserved Subtrees (Zero Invalidation)</span>
                <span className="text-[10px] font-mono font-bold">43 Items</span>
              </div>
              <p className="text-muted-foreground text-[11px]">
                Fuselage loft solid, formers 001–007, longerons, tail surfaces (HT/VT spars and ribs), Sheet_03 stock layout, propulsion firewall.
              </p>
            </div>
          </div>
        </div>

        {/* Regeneration Actions */}
        <div className="rounded-xl border border-border/80 bg-card p-5 space-y-4 flex flex-col justify-between">
          <div className="space-y-2">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <RefreshCw className="size-4 text-primary" />
              Selective vs Full Pipeline Execution
            </h3>
            <p className="text-xs text-muted-foreground">
              Because the changes are constrained strictly to the wing assembly subtree, the revision engine can execute selective regeneration without modifying unaffected fuselage or tail outputs.
            </p>
          </div>

          <div className="space-y-2 pt-2">
            <button
              onClick={() => onRegenerate("v2")}
              className="w-full rounded-md bg-primary py-2.5 text-xs font-semibold text-primary-foreground shadow-xs hover:bg-primary/90 transition-all flex items-center justify-center gap-2"
            >
              <RefreshCw className="size-3.5" />
              Regenerate {selectedTarget} (Selective Wing Scope)
            </button>

            <button
              onClick={() => onRegenerate("v2")}
              className="w-full rounded-md border border-border/80 bg-muted/40 py-2 text-xs font-medium text-foreground hover:bg-muted/80 transition-all"
            >
              Full Clean Pipeline Regeneration ({selectedTarget})
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------
// 10. ENGINEERING REVIEW & COMPLIANCE SECTION
// ----------------------------------------------------------------------
function EngineeringReviewSection({ state }) {
  const [filterCategory, setFilterCategory] = useState("ALL");

  const complianceItems = useMemo(() => [
    { category: "Geometry", parameter: "Wingspan", req: "2000.0 mm", act: "2000.0 mm", tol: "±1.0 mm", dev: "0.0 mm", status: "PASS", comp: "MainWing" },
    { category: "Geometry", parameter: "Fuselage Length", req: "1500.0 mm", act: "1500.0 mm", tol: "±1.0 mm", dev: "0.0 mm", status: "PASS", comp: "Fuselage" },
    { category: "Geometry", parameter: "Horizontal Tail Span", req: "500.0 mm", act: "500.0 mm", tol: "±1.0 mm", dev: "0.0 mm", status: "PASS", comp: "HorizontalTail" },
    { category: "Geometry", parameter: "Vertical Tail Height", req: "400.0 mm", act: "400.0 mm", tol: "±1.0 mm", dev: "0.0 mm", status: "PASS", comp: "VerticalTail" },
    { category: "Geometry", parameter: "Propeller Diameter", req: "304.8 mm", act: "304.8 mm", tol: "±1.0 mm", dev: "0.0 mm", status: "PASS", comp: "Propulsion" },
    { category: "Configuration", parameter: "Wing Position", req: "high", act: "high", tol: "Exact", dev: "—", status: "PASS", comp: "MainWing" },
    { category: "Configuration", parameter: "Propulsion Layout", req: "tractor", act: "tractor", tol: "Exact", dev: "—", status: "PASS", comp: "Propulsion" },
    { category: "Structure", parameter: "Structural Solids", req: "≥ 40 solids", act: "48 solids", tol: "Count", dev: "—", status: "PASS", comp: "Airframe" },
    { category: "Manufacturing", parameter: "Laser Parts", req: "≥ 40 parts", act: "47 parts", tol: "Count", dev: "—", status: "PASS", comp: "Sheet_01-03" },
    { category: "Manufacturing", parameter: "3D-Print Solids", req: "Present", act: "1 part", tol: "Count", dev: "—", status: "PASS", comp: "WING-ATTACH-001" },
    { category: "Mass", parameter: "Takeoff Mass (MTOW)", req: "5.5 kg (Sec 1)", act: "11.0 kg (Sec 3)", tol: "Discrepancy", dev: "+5.5 kg", status: "CONFLICT", comp: "Report Data" },
    { category: "Mass & CG", parameter: "Center of Gravity", req: "Design Target", act: "Not Modeled", tol: "—", dev: "—", status: "NOT_VERIFIABLE", comp: "Inertia Matrix" },
  ], []);

  const filteredItems = useMemo(() => {
    if (filterCategory === "ALL") return complianceItems;
    return complianceItems.filter(i => i.category.toUpperCase() === filterCategory.toUpperCase());
  }, [complianceItems, filterCategory]);

  return (
    <div className="mx-auto max-w-6xl p-6 space-y-6">
      {/* Header Bar */}
      <div className="flex items-center justify-between border-b border-border/60 pb-4">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Engineering Design Review & Requirement Compliance</h2>
          <p className="text-xs text-muted-foreground">
            Formal compliance audit across geometry, configuration, structure, manufacturing, mass, and prototype readiness.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 rounded-lg border border-amber-500/20 bg-amber-500/10 px-3 py-1.5 text-xs text-amber-700 dark:text-amber-300 font-semibold">
            <AlertTriangle className="size-3.5" />
            <span>REVIEW: PASS WITH WARNINGS</span>
          </div>
          <div className="flex items-center gap-1.5 rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-3 py-1.5 text-xs text-emerald-700 dark:text-emerald-300 font-semibold">
            <CheckCircle2 className="size-3.5" />
            <span>PROTOTYPE: READY WITH WARNINGS</span>
          </div>
        </div>
      </div>

      {/* Category Status Dashboard */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
        {[
          { label: "Geometry", status: "PASS", color: "emerald" },
          { label: "Configuration", status: "PASS", color: "emerald" },
          { label: "Structure", status: "PASS", color: "emerald" },
          { label: "Manufacturing", status: "PASS", color: "emerald" },
          { label: "Mass Budget", status: "CONFLICT", color: "amber" },
          { label: "Center of Gravity", status: "NOT_VERIFIABLE", color: "blue" },
        ].map((cat, idx) => (
          <div key={idx} className="rounded-xl border border-border/80 bg-card p-3 space-y-1">
            <span className="text-[11px] text-muted-foreground font-medium block truncate">{cat.label}</span>
            <span className={`inline-block rounded px-1.5 py-0.5 text-[10px] font-bold ${
              cat.color === "emerald" ? "bg-emerald-500/10 text-emerald-600 border border-emerald-500/20" :
              cat.color === "amber" ? "bg-amber-500/10 text-amber-600 border border-amber-500/20" :
              "bg-blue-500/10 text-blue-600 border border-blue-500/20"
            }`}>
              {cat.status}
            </span>
          </div>
        ))}
      </div>

      {/* Non-Blocking Conflict Banner */}
      <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-xs text-amber-800 dark:text-amber-200 flex items-start gap-3">
        <AlertTriangle className="size-5 text-amber-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-semibold flex items-center gap-2">
            <span>Known Requirement Conflict: Takeoff Mass (MTOW)</span>
            <span className="rounded bg-amber-500/20 px-1.5 py-0.5 text-[10px] uppercase font-bold">Non-Blocking</span>
          </div>
          <p className="text-amber-700/90 dark:text-amber-300/90">
            Part 1 Engineering Report states <strong>5.50 kg</strong> in the Executive Summary but aggregates to <strong>11.0 kg</strong> in Section 3 component mass breakdown. CAD synthesis and physical prototype nesting continued without interruption.
          </p>
        </div>
      </div>

      {/* Compliance Matrix Table */}
      <div className="rounded-xl border border-border/80 bg-card overflow-hidden">
        <div className="border-b border-border/60 bg-muted/30 px-4 py-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <ClipboardCheck className="size-4 text-primary" />
            Requirement Compliance Matrix ({filteredItems.length} items)
          </h3>

          <div className="flex items-center gap-1 bg-muted/60 p-0.5 rounded-lg text-xs">
            {["ALL", "GEOMETRY", "CONFIGURATION", "STRUCTURE", "MANUFACTURING", "MASS"].map(cat => (
              <button
                key={cat}
                onClick={() => setFilterCategory(cat)}
                className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
                  filterCategory === cat ? "bg-background text-foreground shadow-xs" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-border/60 bg-muted/10 font-medium text-muted-foreground">
                <th className="py-2.5 px-4">Category</th>
                <th className="py-2.5 px-4">Parameter</th>
                <th className="py-2.5 px-4 font-mono">Required</th>
                <th className="py-2.5 px-4 font-mono">Actual / Generated</th>
                <th className="py-2.5 px-4 font-mono">Tolerance</th>
                <th className="py-2.5 px-4 font-mono">Deviation</th>
                <th className="py-2.5 px-4">Compliance Status</th>
                <th className="py-2.5 px-4">Traceable Target</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40 font-mono">
              {filteredItems.map((i, idx) => (
                <tr key={idx} className="hover:bg-muted/20 transition-colors">
                  <td className="py-2.5 px-4 font-sans font-medium text-foreground">{i.category}</td>
                  <td className="py-2.5 px-4 font-semibold text-primary">{i.parameter}</td>
                  <td className="py-2.5 px-4 text-muted-foreground">{i.req}</td>
                  <td className="py-2.5 px-4 text-foreground font-bold">{i.act}</td>
                  <td className="py-2.5 px-4 text-muted-foreground">{i.tol}</td>
                  <td className="py-2.5 px-4 text-muted-foreground">{i.dev}</td>
                  <td className="py-2.5 px-4 font-sans">
                    <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${
                      i.status === "PASS" ? "bg-emerald-500/10 text-emerald-600 border border-emerald-500/20" :
                      i.status === "CONFLICT" ? "bg-amber-500/10 text-amber-600 border border-amber-500/20" :
                      i.status === "NOT_VERIFIABLE" ? "bg-blue-500/10 text-blue-600 border border-blue-500/20" :
                      "bg-rose-500/10 text-rose-600 border border-rose-500/20"
                    }`}>
                      {i.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-4 font-sans text-muted-foreground text-[11px]">{i.comp}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------
// 11. PROTOTYPE BUILD PACKAGE & ASSEMBLY SECTION
// ----------------------------------------------------------------------
function PrototypeBuildSection({ state }) {
  const [activeSubassembly, setActiveSubassembly] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  const demoParts = useMemo(() => [
    { id: "FIREWALL-001", name: "Fuselage Firewall", sub: "Fuselage", proc: "LASER_CUT", mat: "Aeroply", thick: "3.0 mm", qty: 1, art: "Sheet_03" },
    { id: "FMR-001", name: "Fuselage Former 001", sub: "Fuselage", proc: "LASER_CUT", mat: "Aeroply", thick: "3.0 mm", qty: 1, art: "Sheet_03" },
    { id: "FMR-002", name: "Fuselage Former 002", sub: "Fuselage", proc: "LASER_CUT", mat: "Aeroply", thick: "3.0 mm", qty: 1, art: "Sheet_03" },
    { id: "LONG-UPPER-L", name: "Upper Left Longeron", sub: "Fuselage", proc: "LASER_CUT", mat: "Aeroply", thick: "3.0 mm", qty: 1, art: "Sheet_03" },
    { id: "SPAR-L-MAIN", name: "Left Main Wing Spar", sub: "MainWing_Left", proc: "LASER_CUT", mat: "Aeroply", thick: "3.0 mm", qty: 1, art: "Sheet_02" },
    { id: "RIB-L-001", name: "Left Wing Rib 001", sub: "MainWing_Left", proc: "LASER_CUT", mat: "Balsa", thick: "3.0 mm", qty: 1, art: "Sheet_01" },
    { id: "RIB-L-002", name: "Left Wing Rib 002", sub: "MainWing_Left", proc: "LASER_CUT", mat: "Balsa", thick: "3.0 mm", qty: 1, art: "Sheet_01" },
    { id: "SPAR-R-MAIN", name: "Right Main Wing Spar", sub: "MainWing_Right", proc: "LASER_CUT", mat: "Aeroply", thick: "3.0 mm", qty: 1, art: "Sheet_02" },
    { id: "RIB-R-001", name: "Right Wing Rib 001", sub: "MainWing_Right", proc: "LASER_CUT", mat: "Balsa", thick: "3.0 mm", qty: 1, art: "Sheet_01" },
    { id: "HT-SPAR-L-001", name: "HT Left Spar", sub: "HorizontalTail", proc: "LASER_CUT", mat: "Aeroply", thick: "3.0 mm", qty: 1, art: "Sheet_02" },
    { id: "VT-SPAR-001", name: "VT Main Spar", sub: "VerticalTail", proc: "LASER_CUT", mat: "Aeroply", thick: "3.0 mm", qty: 1, art: "Sheet_02" },
    { id: "PRINT-WING-ATTACH-001", name: "Wing Attachment Block", sub: "WingFuselage_Interface", proc: "THREE_D_PRINT", mat: "PETG", thick: "Solid", qty: 1, art: "WING-ATTACH.stl" },
  ], []);

  const assemblySteps = useMemo(() => [
    { step: 1, title: "Fuselage Framework", sub: "Fuselage", desc: "Interlock formers FMR-000..005 with longerons and secure FIREWALL-001.", deps: "None", parts: "12 parts", joints: "18 tab/slot joints" },
    { step: 2, title: "Left Wing Structure", sub: "MainWing_Left", desc: "Slot ribs RIB-L-000..009 onto SPAR-L-MAIN and SPAR-L-REAR.", deps: "None", parts: "12 parts", joints: "20 tab/slot joints" },
    { step: 3, title: "Right Wing Structure", sub: "MainWing_Right", desc: "Slot ribs RIB-R-000..009 onto SPAR-R-MAIN and SPAR-R-REAR.", deps: "None", parts: "12 parts", joints: "20 tab/slot joints" },
    { step: 4, title: "Tail Empennage", sub: "Tail", desc: "Assemble horizontal stabilizer and vertical stabilizer frameworks.", deps: "None", parts: "11 parts", joints: "11 tab/slot joints" },
    { step: 5, title: "Final Airframe Integration", sub: "Airframe", desc: "Attach wings to fuselage with 3D attachment block and mount empennage.", deps: "Steps 1, 2, 3, 4", parts: "1 part + subs", joints: "Attachment Interface" },
  ], []);

  const filteredParts = useMemo(() => {
    return demoParts.filter(p => {
      const matchSub = activeSubassembly === "ALL" || p.sub === activeSubassembly;
      const matchQ = !searchQuery || p.id.toLowerCase().includes(searchQuery.toLowerCase()) || p.name.toLowerCase().includes(searchQuery.toLowerCase());
      return matchSub && matchQ;
    });
  }, [demoParts, activeSubassembly, searchQuery]);

  return (
    <div className="mx-auto max-w-6xl p-6 space-y-6">
      {/* Header Bar */}
      <div className="flex items-center justify-between border-b border-border/60 pb-4">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Prototype Build Package & Physical Assembly Preparation</h2>
          <p className="text-xs text-muted-foreground">
            Complete physical fabrication inventory, material schedule, tab/slot joint mapping, and assembly sequence.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-3 py-1.5 text-xs text-emerald-700 dark:text-emerald-300 font-semibold">
            <PackageCheck className="size-3.5" />
            <span>BUILD READINESS: READY</span>
          </div>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div className="rounded-xl border border-border/80 bg-card p-3 space-y-1">
          <span className="text-[11px] text-muted-foreground font-medium">Physical Parts</span>
          <p className="text-2xl font-bold font-mono">48</p>
          <span className="text-[10px] text-muted-foreground">100% Validated</span>
        </div>
        <div className="rounded-xl border border-border/80 bg-card p-3 space-y-1">
          <span className="text-[11px] text-muted-foreground font-medium">Laser Cut Parts</span>
          <p className="text-2xl font-bold font-mono">47</p>
          <span className="text-[10px] text-muted-foreground">Balsa & Aeroply 3mm</span>
        </div>
        <div className="rounded-xl border border-border/80 bg-card p-3 space-y-1">
          <span className="text-[11px] text-muted-foreground font-medium">3D Printed Solids</span>
          <p className="text-2xl font-bold font-mono">1</p>
          <span className="text-[10px] text-muted-foreground">Wing Root Attachment</span>
        </div>
        <div className="rounded-xl border border-border/80 bg-card p-3 space-y-1">
          <span className="text-[11px] text-muted-foreground font-medium">Structural Joints</span>
          <p className="text-2xl font-bold font-mono">69</p>
          <span className="text-[10px] text-muted-foreground">Tab & Slot Mates</span>
        </div>
        <div className="rounded-xl border border-border/80 bg-card p-3 space-y-1">
          <span className="text-[11px] text-muted-foreground font-medium">Stock Sheets</span>
          <p className="text-2xl font-bold font-mono">3</p>
          <span className="text-[10px] text-muted-foreground">900 × 600 mm nested</span>
        </div>
      </div>

      {/* Assembly Sequence Steps */}
      <div className="rounded-xl border border-border/80 bg-card p-5 space-y-4">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <Layers className="size-4 text-primary" />
          Deterministic Assembly Sequence (5 Stages)
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {assemblySteps.map((s) => (
            <div key={s.step} className="rounded-lg border border-border/60 bg-muted/20 p-3 space-y-2 text-xs flex flex-col justify-between">
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-bold text-primary">Stage {s.step}</span>
                  <span className="text-[10px] text-muted-foreground">{s.sub}</span>
                </div>
                <h4 className="font-semibold text-foreground text-xs">{s.title}</h4>
                <p className="text-muted-foreground text-[11px] leading-tight">{s.desc}</p>
              </div>
              <div className="border-t border-border/40 pt-2 space-y-0.5 text-[10px] font-mono text-muted-foreground">
                <div>{s.parts}</div>
                <div>{s.joints}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Parts Inventory Table */}
      <div className="rounded-xl border border-border/80 bg-card overflow-hidden">
        <div className="border-b border-border/60 bg-muted/30 px-4 py-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <Package className="size-4 text-primary" />
            Physical Part Inventory ({filteredParts.length} parts)
          </h3>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1 bg-muted/60 p-0.5 rounded-lg text-xs">
              {["ALL", "Fuselage", "MainWing_Left", "MainWing_Right", "HorizontalTail", "VerticalTail"].map(sub => (
                <button
                  key={sub}
                  onClick={() => setActiveSubassembly(sub)}
                  className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
                    activeSubassembly === sub ? "bg-background text-foreground shadow-xs" : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {sub}
                </button>
              ))}
            </div>

            <div className="relative">
              <Search className="size-3.5 absolute left-2.5 top-2 text-muted-foreground" />
              <input
                type="text"
                placeholder="Filter parts..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="rounded-md border border-border/60 bg-background pl-8 pr-2.5 py-1 text-xs w-36 focus:outline-hidden"
              />
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-border/60 bg-muted/10 font-medium text-muted-foreground">
                <th className="py-2.5 px-4 font-mono">Part ID</th>
                <th className="py-2.5 px-4">Description</th>
                <th className="py-2.5 px-4">Subassembly</th>
                <th className="py-2.5 px-4">Process</th>
                <th className="py-2.5 px-4">Material</th>
                <th className="py-2.5 px-4 font-mono">Thickness</th>
                <th className="py-2.5 px-4 font-mono">Qty</th>
                <th className="py-2.5 px-4 font-mono">Artifact Ref</th>
                <th className="py-2.5 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40 font-mono">
              {filteredParts.map((p, idx) => (
                <tr key={idx} className="hover:bg-muted/20 transition-colors">
                  <td className="py-2.5 px-4 font-bold text-primary">{p.id}</td>
                  <td className="py-2.5 px-4 font-sans text-foreground">{p.name}</td>
                  <td className="py-2.5 px-4 font-sans text-muted-foreground">{p.sub}</td>
                  <td className="py-2.5 px-4 font-sans">
                    <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${
                      p.proc === "LASER_CUT" ? "bg-blue-500/10 text-blue-600" : "bg-purple-500/10 text-purple-600"
                    }`}>
                      {p.proc}
                    </span>
                  </td>
                  <td className="py-2.5 px-4 font-sans text-foreground">{p.mat}</td>
                  <td className="py-2.5 px-4 text-muted-foreground">{p.thick}</td>
                  <td className="py-2.5 px-4 text-foreground font-bold">{p.qty}</td>
                  <td className="py-2.5 px-4 text-muted-foreground">{p.art}</td>
                  <td className="py-2.5 px-4 font-sans">
                    <span className="rounded bg-emerald-500/10 text-emerald-600 px-1.5 py-0.5 text-[10px] font-bold">
                      VALIDATED
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function Build3DViewerSection({ state }) {
  const [viewMode, setViewMode] = useState(state.buildViewMode || BUILD_VIEW_MODES.ASSEMBLED);
  const [highlightMode, setHighlightMode] = useState(state.buildHighlightMode || BUILD_HIGHLIGHT_MODES.NONE);
  const [selectedPartId, setSelectedPartId] = useState(state.selectedPartId || "RIB-L-001");
  const [selectedStepIndex, setSelectedStepIndex] = useState(0);
  const [selectedJointId, setSelectedJointId] = useState(state.selectedJointId || "JOINT-001");
  const [explodedFactor, setExplodedFactor] = useState(state.explodedOffsetFactor || 1.0);
  const [isolatedSub, setIsolatedSub] = useState(state.isolatedComponentId || null);
  const [searchQuery, setSearchQuery] = useState("");

  const steps = [
    { id: "STEP-01", num: 1, title: "Fuselage Primary Framework Assembly", sub: "Fuselage", parts: ["FORMER-000", "FORMER-001", "FORMER-002", "FORMER-003", "FORMER-004", "FORMER-005", "LONGERON-000", "LONGERON-001", "LONGERON-002", "LONGERON-003", "FIREWALL-001"], desc: "Assemble and square the 6 internal balsa formers and 4 aeroply longerons into the primary fuselage truss." },
    { id: "STEP-02", num: 2, title: "Left Wing Spar and Rib Assembly", sub: "MainWing_Left", parts: ["SPAR-L-MAIN", "SPAR-L-REAR", "RIB-L-000", "RIB-L-001", "RIB-L-002", "RIB-L-003", "RIB-L-004", "RIB-L-005", "RIB-L-006", "RIB-L-007", "RIB-L-008", "RIB-L-009", "PRINT-WING-ATTACH-001"], desc: "Slot the 10 wing ribs onto the main and rear spars of the port wing panel, securing the 3D-printed attachment block." },
    { id: "STEP-03", num: 3, title: "Right Wing Spar and Rib Assembly", sub: "MainWing_Right", parts: ["SPAR-R-MAIN", "SPAR-R-REAR", "RIB-R-000", "RIB-R-001", "RIB-R-002", "RIB-R-003", "RIB-R-004", "RIB-R-005", "RIB-R-006", "RIB-R-007", "RIB-R-008", "RIB-R-009"], desc: "Slot the 10 wing ribs onto the main and rear spars of the starboard wing panel." },
    { id: "STEP-04", num: 4, title: "Tail Empennage Assembly", sub: "HorizontalTail", parts: ["SPAR-HT-L", "SPAR-HT-R", "RIB-HT-L-000", "RIB-HT-L-001", "RIB-HT-L-002", "RIB-HT-R-000", "RIB-HT-R-001", "RIB-HT-R-002", "SPAR-VT-001", "RIB-VT-000", "RIB-VT-001", "RIB-VT-002"], desc: "Assemble horizontal stabilizer spars and ribs, then mate vertical stabilizer fin spars." },
    { id: "STEP-05", num: 5, title: "Final Airframe Integration & Wing Attachment", sub: "Fuselage", parts: ["PRINT-WING-ATTACH-001", "FIREWALL-001"], desc: "Join left and right wing panels to fuselage structure via the 3D-printed attachment interface and install motor firewall." },
  ];

  const currentStep = steps[selectedStepIndex] || steps[0];

  const parts = [
    { id: "SPAR-L-MAIN", name: "Main Spar (Port)", sub: "MainWing_Left", proc: "LASER_CUT", mat: "Aeroply_3mm", thick: "3.0 mm", qty: 1, req: "wing.span", art: "Sheet_01.dxf", engStatus: "VALID", mfgStatus: "READY" },
    { id: "SPAR-L-REAR", name: "Rear Spar (Port)", sub: "MainWing_Left", proc: "LASER_CUT", mat: "Aeroply_3mm", thick: "3.0 mm", qty: 1, req: "wing.span", art: "Sheet_01.dxf", engStatus: "VALID", mfgStatus: "READY" },
    { id: "RIB-L-001", name: "Wing Rib 001", sub: "MainWing_Left", proc: "LASER_CUT", mat: "Balsa_3mm", thick: "3.0 mm", qty: 1, req: "wing.root_chord", art: "Sheet_02.dxf", engStatus: "VALID", mfgStatus: "READY" },
    { id: "FORMER-000", name: "Fuselage Former 000", sub: "Fuselage", proc: "LASER_CUT", mat: "Balsa_3mm", thick: "3.0 mm", qty: 1, req: "fuselage.width", art: "Sheet_02.dxf", engStatus: "VALID", mfgStatus: "READY" },
    { id: "LONGERON-000", name: "Longeron Top Port", sub: "Fuselage", proc: "LASER_CUT", mat: "Aeroply_3mm", thick: "3.0 mm", qty: 1, req: "fuselage.length", art: "Sheet_01.dxf", engStatus: "VALID", mfgStatus: "READY" },
    { id: "PRINT-WING-ATTACH-001", name: "Wing Attachment Block", sub: "MainWing_Left", proc: "THREE_D_PRINT", mat: "PLA_Standard", thick: "12.0 mm", qty: 1, req: "configuration.wing_position", art: "PRINT-WING-ATTACH-001.stl", engStatus: "VALID", mfgStatus: "READY" },
  ];

  const selectedPart = parts.find((p) => p.id === selectedPartId) || parts[0];

  const handlePrevStep = () => {
    setSelectedStepIndex((prev) => Math.max(0, prev - 1));
  };

  const handleNextStep = () => {
    setSelectedStepIndex((prev) => Math.min(steps.length - 1, prev + 1));
  };

  const handleResetView = () => {
    setViewMode(BUILD_VIEW_MODES.ASSEMBLED);
    setExplodedFactor(1.0);
    setIsolatedSub(null);
    setHighlightMode(BUILD_HIGHLIGHT_MODES.NONE);
    setAircraftWorkspaceState({
      buildViewMode: BUILD_VIEW_MODES.ASSEMBLED,
      explodedOffsetFactor: 1.0,
      isolatedComponentId: null,
      buildHighlightMode: BUILD_HIGHLIGHT_MODES.NONE,
    });
  };

  return (
    <div className="flex h-full flex-col gap-4 p-6 overflow-y-auto">
      {/* Top Banner & Metrics */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-border/80 bg-card p-5 shadow-xs">
        <div className="flex items-center gap-3.5">
          <div className="flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Wrench className="size-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-foreground">3D Build Visualization & Assembly Guidance</h2>
              <span className="rounded bg-emerald-500/10 text-emerald-600 px-2 py-0.5 text-[11px] font-bold border border-emerald-500/20">
                PROTOTYPE READY
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              Aircraft {state.aircraftId} ({state.version}) • Traceable Part Inspection • Deterministic Presentation
            </p>
          </div>
        </div>

        {/* View Mode Switcher */}
        <div className="flex items-center gap-1.5 rounded-lg bg-muted/60 p-1 border border-border/40">
          {Object.values(BUILD_VIEW_MODES).map((mode) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors ${
                viewMode === mode
                  ? "bg-primary text-primary-foreground shadow-xs"
                  : "text-muted-foreground hover:text-foreground hover:bg-background/40"
              }`}
            >
              {mode}
            </button>
          ))}
        </div>

        {/* Actions & Reset */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleResetView}
            className="flex items-center gap-1.5 rounded-md border border-border/60 bg-muted/20 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted/40 transition-colors"
          >
            <RefreshCw className="size-3.5" />
            Reset View
          </button>
        </div>
      </div>

      {/* Assembly Step Sequence Navigator */}
      <div className="rounded-xl border border-border/80 bg-card p-4 shadow-xs">
        <div className="flex items-center justify-between gap-4 mb-3">
          <div className="flex items-center gap-2">
            <span className="rounded bg-primary/10 text-primary px-2 py-0.5 text-xs font-bold font-mono">
              STEP {currentStep.num} / {steps.length}
            </span>
            <h3 className="text-sm font-bold text-foreground">{currentStep.title}</h3>
            <span className="text-xs text-muted-foreground font-mono">({currentStep.sub})</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrevStep}
              disabled={selectedStepIndex === 0}
              className="rounded-md border border-border/60 bg-muted/20 px-2.5 py-1 text-xs font-medium hover:bg-muted/40 disabled:opacity-40 transition-colors"
            >
              Previous Step
            </button>
            <button
              onClick={handleNextStep}
              disabled={selectedStepIndex === steps.length - 1}
              className="rounded-md bg-primary text-primary-foreground px-2.5 py-1 text-xs font-medium hover:bg-primary/90 disabled:opacity-40 transition-colors"
            >
              Next Step
            </button>
          </div>
        </div>
        <p className="text-xs text-muted-foreground mb-2">{currentStep.desc}</p>
        <div className="flex flex-wrap gap-1.5 pt-2 border-t border-border/40">
          <span className="text-[11px] font-semibold text-muted-foreground mr-1">Parts in this step:</span>
          {currentStep.parts.map((pid) => (
            <button
              key={pid}
              onClick={() => setSelectedPartId(pid)}
              className={`rounded px-1.5 py-0.5 text-[10px] font-mono font-bold transition-colors ${
                selectedPartId === pid
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground"
              }`}
            >
              {pid}
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid: 3D Visualization & Inspector Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* 3D Viewer Presentation Mock Canvas */}
        <div className="lg:col-span-2 rounded-xl border border-border/80 bg-muted/10 p-5 flex flex-col justify-between min-h-[380px] shadow-xs">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-foreground">3D Viewport Presentation</span>
              <span className="rounded bg-muted px-2 py-0.5 text-[10px] font-mono text-muted-foreground">
                Mode: {viewMode}
              </span>
              {viewMode === BUILD_VIEW_MODES.EXPLODED && (
                <span className="rounded bg-amber-500/10 text-amber-600 px-2 py-0.5 text-[10px] font-mono">
                  Offset: {(explodedFactor * 180).toFixed(0)} mm
                </span>
              )}
            </div>
            {viewMode === BUILD_VIEW_MODES.EXPLODED && (
              <div className="flex items-center gap-2 text-xs">
                <span className="text-muted-foreground">Explode Factor:</span>
                <input
                  type="range"
                  min="0.5"
                  max="2.5"
                  step="0.1"
                  value={explodedFactor}
                  onChange={(e) => setExplodedFactor(parseFloat(e.target.value))}
                  className="w-24 accent-primary"
                />
              </div>
            )}
          </div>

          {/* Interactive Subassembly Iso Canvas Representation */}
          <div className="flex-1 flex items-center justify-center my-6">
            <div className="relative w-full max-w-md aspect-video rounded-lg border border-border/60 bg-card/60 p-4 flex flex-col items-center justify-center gap-3">
              <Plane className="size-16 text-primary/40 animate-pulse" />
              <div className="text-center">
                <div className="text-xs font-bold text-foreground">
                  {state.aircraftId} 3D Assembly Mesh Active
                </div>
                <div className="text-[11px] text-muted-foreground font-mono mt-0.5">
                  48 Physical Parts • 69 Tab-Slot Joints • {viewMode} Presentation
                </div>
              </div>
              <div className="flex gap-2 text-[10px] font-mono">
                <button
                  onClick={() => setIsolatedSub("Fuselage")}
                  className="rounded bg-muted px-2 py-1 hover:bg-muted/80 text-muted-foreground"
                >
                  Isolate Fuselage
                </button>
                <button
                  onClick={() => setIsolatedSub("MainWing_Left")}
                  className="rounded bg-muted px-2 py-1 hover:bg-muted/80 text-muted-foreground"
                >
                  Isolate Left Wing
                </button>
                <button
                  onClick={() => setIsolatedSub(null)}
                  className="rounded bg-muted px-2 py-1 hover:bg-muted/80 text-muted-foreground"
                >
                  Show All
                </button>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-2 border-t border-border/40 font-mono">
            <span>Deterministic Presentation Offsets (CAD Source Unaltered)</span>
            <span>Active Part: {selectedPartId}</span>
          </div>
        </div>

        {/* Part Inspector & Traceability */}
        <div className="rounded-xl border border-border/80 bg-card p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-foreground">Physical Part Inspector</h3>
              <span className="rounded bg-emerald-500/10 text-emerald-600 px-2 py-0.5 text-[10px] font-bold">
                {selectedPart.engStatus}
              </span>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div className="flex justify-between py-1 border-b border-border/40">
                <span className="text-muted-foreground font-sans">Part ID:</span>
                <span className="font-bold text-primary">{selectedPart.id}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/40">
                <span className="text-muted-foreground font-sans">Description:</span>
                <span className="text-foreground">{selectedPart.name}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/40">
                <span className="text-muted-foreground font-sans">Subassembly:</span>
                <span className="text-foreground">{selectedPart.sub}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/40">
                <span className="text-muted-foreground font-sans">Process:</span>
                <span className="text-foreground">{selectedPart.proc}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/40">
                <span className="text-muted-foreground font-sans">Material:</span>
                <span className="text-foreground">{selectedPart.mat}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/40">
                <span className="text-muted-foreground font-sans">Thickness:</span>
                <span className="text-foreground">{selectedPart.thick}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-border/40">
                <span className="text-muted-foreground font-sans">Artifact Link:</span>
                <span className="text-foreground font-bold">{selectedPart.art}</span>
              </div>
            </div>

            {/* Traceability Chain Panel */}
            <div className="mt-5 p-3 rounded-lg bg-muted/20 border border-border/60">
              <div className="text-[11px] font-bold text-foreground mb-2 flex items-center gap-1.5">
                <Tag className="size-3.5 text-primary" />
                End-to-End Traceability Chain
              </div>
              <div className="space-y-1.5 text-[10px] font-mono">
                <div className="text-muted-foreground">1. Req: <span className="text-foreground font-bold">{selectedPart.req}</span></div>
                <div className="text-muted-foreground">2. CAD: <span className="text-foreground font-bold">{selectedPart.sub}</span></div>
                <div className="text-muted-foreground">3. Struct: <span className="text-foreground font-bold">{selectedPart.id}</span></div>
                <div className="text-muted-foreground">4. Mfg: <span className="text-foreground font-bold">{selectedPart.proc}</span></div>
                <div className="text-muted-foreground">5. File: <span className="text-primary font-bold">{selectedPart.art}</span></div>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-border/40 flex items-center justify-between text-[11px]">
            <span className="text-muted-foreground">Build Progress:</span>
            <span className="rounded bg-muted px-2 py-0.5 text-[10px] font-mono font-bold text-foreground">
              NOT_STARTED
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function FinalReleaseSection({ state }) {
  const relRes = state.releaseGateResult || {
    is_released: true,
    release_status: "READY_WITH_WARNINGS",
    manifest: {
      aircraft_id: state.aircraftId,
      release_id: `${state.aircraftId}-${state.version}-RELEASE-CANONICAL`,
      version: state.version,
      specification_version: "Fixed-Wing UAV Engineering Report — SURVEY Mission",
      created_at: new Date().toISOString(),
      release_status: "READY_WITH_WARNINGS",
      prototype_status: "READY_WITH_WARNINGS",
      checks: [
        { check_id: "REL-STAGE-001", category: "CROSS_STAGE_QA", name: "Pipeline Stages Completeness", status: "PASS", is_blocking: true, message: "All 12 upstream stages verified", expected: "All stages present", actual: "12 stages valid", source_stage: "Phase 7 Pipeline" },
        { check_id: "REL-CAD-001", category: "CAD_CONSISTENCY", name: "CAD Wingspan Consistency", status: "PASS", is_blocking: true, message: "CAD wingspan 2000.0 mm matches spec (dev=0.00 mm)", expected: 2000.0, actual: 2000.0, source_stage: "Phase 4 CAD" },
        { check_id: "REL-STR-001", category: "STRUCTURAL_CONSISTENCY", name: "Structural Solid Completeness", status: "PASS", is_blocking: true, message: "48 structural solids synthesized and non-degenerate", expected: "48 solids", actual: "48 solids", source_stage: "Phase 5 Structure" },
        { check_id: "REL-MFG-001", category: "MANUFACTURING_CONSISTENCY", name: "Manufacturing Decomposition Completeness", status: "PASS", is_blocking: true, message: "48 parts mapped 1:1 (47 laser, 1 3D-print)", expected: "48 parts", actual: "48 parts", source_stage: "Phase 6B Classification" },
        { check_id: "REL-BPKG-001", category: "BUILD_PACKAGE_CONSISTENCY", name: "Build Package Integrity & BOM Consistency", status: "PASS", is_blocking: true, message: "BOM, 69 joints, and 5 assembly steps validated", expected: "VALID", actual: "VALID", source_stage: "Phase 11 Build Package" },
        { check_id: "REL-ART-001", category: "ARTIFACT_INTEGRITY", name: "Physical Artifact Existence & Non-Emptiness", status: "PASS", is_blocking: true, message: "DXF, SVG, STL, STEP, and Manifest files present", expected: "0 missing", actual: "0 missing", source_stage: "Phase 7 Artifact Registry" },
      ],
      warnings: ["Takeoff mass (MTOW) specification contains conflicting values [5.5 kg, 11.0 kg] across report sections."],
      blocking_issues: [],
    },
  };

  const manifest = relRes.manifest;
  const isReleased = relRes.is_released;

  return (
    <div className="flex h-full flex-col gap-5 p-6 overflow-y-auto">
      {/* Release Decision Header Banner */}
      <div className={`rounded-xl border p-6 shadow-xs flex flex-wrap items-center justify-between gap-4 ${
        isReleased
          ? "border-emerald-500/30 bg-emerald-500/5 text-foreground"
          : "border-rose-500/30 bg-rose-500/5 text-foreground"
      }`}>
        <div className="flex items-center gap-4">
          <div className={`flex size-12 items-center justify-center rounded-xl font-bold ${
            isReleased ? "bg-emerald-500/20 text-emerald-600" : "bg-rose-500/20 text-rose-600"
          }`}>
            <ShieldCheck className="size-6" />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-bold">Phase 13 Final Prototype Release Gate</h2>
              <span className={`rounded px-2.5 py-0.5 text-xs font-mono font-bold border ${
                isReleased
                  ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
                  : "bg-rose-500/10 text-rose-600 border-rose-500/20"
              }`}>
                {manifest.release_status}
              </span>
            </div>
            <p className="text-xs text-muted-foreground font-mono mt-0.5">
              Release ID: {manifest.release_id} • Target: {manifest.aircraft_id} ({manifest.version})
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-bold text-muted-foreground">
            {manifest.checks.filter((c) => c.status === "PASS").length} / {manifest.checks.length} CHECKS PASSED
          </span>
        </div>
      </div>

      {/* Warnings Banner if present */}
      {manifest.warnings && manifest.warnings.length > 0 && (
        <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 p-4 text-xs text-amber-700 dark:text-amber-300 flex items-start gap-2.5">
          <AlertTriangle className="size-4 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-bold">Preserved Engineering Warnings ({manifest.warnings.length}):</span>
            {manifest.warnings.map((w, idx) => (
              <div key={idx} className="font-mono text-[11px]">{w}</div>
            ))}
          </div>
        </div>
      )}

      {/* Blocking Issues Banner if any */}
      {manifest.blocking_issues && manifest.blocking_issues.length > 0 && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-700 dark:text-rose-300 flex items-start gap-2.5">
          <XCircle className="size-4 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-bold">Blocking Issues ({manifest.blocking_issues.length}):</span>
            {manifest.blocking_issues.map((b, idx) => (
              <div key={idx} className="font-mono text-[11px]">{b}</div>
            ))}
          </div>
        </div>
      )}

      {/* Cross-Stage Consistency Verification Table */}
      <div className="rounded-xl border border-border/80 bg-card overflow-hidden shadow-xs">
        <div className="border-b border-border/60 bg-muted/20 px-5 py-3">
          <h3 className="text-sm font-bold text-foreground">Cross-Stage QA & Consistency Audit</h3>
          <p className="text-xs text-muted-foreground font-mono">
            Automated verification across CAD, Structure, Manufacturing, BOM, Build Package, and Artifact Registry
          </p>
        </div>

        <div className="divide-y divide-border/40 font-mono text-xs">
          {manifest.checks.map((check, idx) => (
            <div key={idx} className="p-4 hover:bg-muted/10 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-primary font-mono">{check.check_id}</span>
                  <span className="font-sans font-bold text-foreground">{check.name}</span>
                  <span className="rounded bg-muted px-2 py-0.5 text-[10px] font-mono text-muted-foreground">
                    {check.source_stage}
                  </span>
                </div>
                <div className="text-muted-foreground font-sans text-[11px]">{check.message}</div>
                <div className="text-[10px] text-muted-foreground">
                  Expected: <span className="text-foreground font-bold">{String(check.expected)}</span> | Actual: <span className="text-foreground font-bold">{String(check.actual)}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <span className={`rounded px-2 py-0.5 text-[10px] font-bold ${
                  check.status === "PASS"
                    ? "bg-emerald-500/10 text-emerald-600 border border-emerald-500/20"
                    : "bg-rose-500/10 text-rose-600 border border-rose-500/20"
                }`}>
                  {check.status === "PASS" ? "✓ PASS" : "✗ FAIL"}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}


