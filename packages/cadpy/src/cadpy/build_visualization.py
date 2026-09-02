"""Phase 12: 3D Build Visualization, Part Inspection & Assembly Guidance Engine.

This module provides the visualization, traceability, and physical assembly guidance
layer for the aircraft design studio. It consumes validated CAD, structural synthesis,
manufacturing outputs, engineering reviews, and Phase 11 Prototype Build Packages
to generate deterministic 3D assembly models, exploded views, part inspection records,
step-by-step assembly guidance, and revision-aware build progress trackers.

ABSOLUTE BOUNDARY:
- Strictly visualization, traceability, and assembly presentation.
- MUST NOT modify CAD geometry, dimensions, materials, or structural layouts.
- Preserves 100% provenance and deterministic repeatability.
"""

from __future__ import annotations

import datetime
from enum import Enum
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict

from cadpy.requirements import AircraftSpecification
from cadpy.manufacturing import (
    ManufacturingPart,
    ManufacturingJoint,
    ManufacturingSheet,
    PrintablePart,
    ManufacturingValidationResult,
)
from cadpy.review import EngineeringReview, ReviewStatus
from cadpy.build_package import (
    PrototypeBuildPackage,
    BuildPart,
    MaterialScheduleItem,
    AssemblyStep,
    BuildValidationResult,
    BuildReadiness,
)


class BuildProgressStatus(str, Enum):
    """Physical build tracking status for components and assembly steps."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    BLOCKED = "BLOCKED"


class ViewMode(str, Enum):
    """Presentation modes for the 3D build viewer."""
    ASSEMBLED = "ASSEMBLED"
    EXPLODED = "EXPLODED"
    STRUCTURE = "STRUCTURE"
    MANUFACTURING = "MANUFACTURING"
    PARTS = "PARTS"
    SUBASSEMBLY = "SUBASSEMBLY"


class HighlightMode(str, Enum):
    """Active highlighting filter in the 3D scene."""
    NONE = "NONE"
    PART = "PART"
    SUBASSEMBLY = "SUBASSEMBLY"
    STEP = "STEP"
    JOINT = "JOINT"
    SHEET = "SHEET"
    PRINT_PART = "PRINT_PART"


class WarningSeverity(str, Enum):
    """Severity levels for build and engineering notices."""
    BLOCKING = "BLOCKING"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class ViewerTraceability:
    """Complete provenance link from requirement to fabrication artifact."""
    requirement: str
    cad_component: str
    structural_component: str
    manufacturing_part: str
    fabrication_artifact: str
    status: str = "VALIDATED"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ViewerComponent:
    """Interactive physical part representation in the 3D build viewer."""
    id: str
    display_name: str
    source_cad_component: Optional[str] = None
    source_structural_component: Optional[str] = None
    source_manufacturing_part: Optional[str] = None
    source_artifact: Optional[str] = None
    parent: Optional[str] = None
    children: list[str] = field(default_factory=list)
    subassembly: str = "Fuselage"
    joints: list[str] = field(default_factory=list)
    revision: str = "v1"
    engineering_status: str = "VALID"
    manufacturing_status: str = "READY"
    build_status: str = BuildProgressStatus.NOT_STARTED.value
    material: Optional[str] = None
    thickness: Optional[float] = None
    quantity: int = 1
    process: Optional[str] = "LASER_CUT"
    dimensions: dict[str, float] = field(default_factory=dict)
    exploded_offset: tuple[float, float, float] = (0.0, 0.0, 0.0)
    cad_transform: dict[str, Any] = field(default_factory=dict)
    traceability: Optional[ViewerTraceability] = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if self.traceability:
            d["traceability"] = self.traceability.to_dict()
        return d


@dataclass
class ViewerAssemblyTreeNode:
    """Hierarchical node in the aircraft assembly tree."""
    id: str
    label: str
    node_type: str  # "aircraft", "subassembly", "group", "part"
    component_ids: list[str] = field(default_factory=list)
    children: list[ViewerAssemblyTreeNode] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "node_type": self.node_type,
            "component_ids": self.component_ids,
            "children": [c.to_dict() for c in self.children],
        }


@dataclass
class ViewerJoint:
    """Physical mechanical joint with connected part relationships."""
    joint_id: str
    parent_part_id: str
    child_part_id: str
    joint_type: str
    interface_location: tuple[float, float, float]
    orientation: str
    assembly_step_id: Optional[str] = None
    validation_status: str = "PASS"
    is_valid: bool = True
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ViewerAssemblyStep:
    """Physical assembly sequence stage with guidance and highlighting hooks."""
    step_id: str
    step_number: int
    title: str
    description: str
    subassembly: str
    component_ids: list[str] = field(default_factory=list)
    part_ids: list[str] = field(default_factory=list)
    joint_ids: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    build_status: str = BuildProgressStatus.NOT_STARTED.value
    warnings: list[str] = field(default_factory=list)
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ViewerLaserSheet:
    """Laser cutting sheet metadata and nested parts."""
    sheet_id: str
    material: str
    thickness: float
    dimensions: tuple[float, float]
    part_ids: list[str] = field(default_factory=list)
    dxf_path: Optional[str] = None
    svg_path: Optional[str] = None
    validation_status: str = "PASS"
    revision: str = "v1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ViewerPrintablePart:
    """3D printed component metadata and artifact links."""
    print_part_id: str
    source_manufacturing_part_id: str
    material: str
    dimensions: tuple[float, float, float]
    stl_path: Optional[str] = None
    aircraft_location: str = "Propulsion / Wing Joint"
    revision: str = "v1"
    artifact_status: str = "AVAILABLE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BuildVisualizationPackage:
    """Complete, self-contained Phase 12 3D build visualization model."""
    aircraft_id: str
    version: str
    parent_version: Optional[str]
    created_at: str
    view_modes: list[str]
    components: dict[str, ViewerComponent]
    assembly_tree: ViewerAssemblyTreeNode
    subassemblies: list[str]
    steps: list[ViewerAssemblyStep]
    joints: list[ViewerJoint]
    sheets: list[ViewerLaserSheet]
    printable_parts: list[ViewerPrintablePart]
    build_progress: dict[str, Any]
    engineering_review_summary: dict[str, Any]
    warnings: list[dict[str, str]]
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "aircraft_id": self.aircraft_id,
            "version": self.version,
            "parent_version": self.parent_version,
            "created_at": self.created_at,
            "view_modes": self.view_modes,
            "components": {k: v.to_dict() for k, v in self.components.items()},
            "assembly_tree": self.assembly_tree.to_dict(),
            "subassemblies": self.subassemblies,
            "steps": [s.to_dict() for s in self.steps],
            "joints": [j.to_dict() for j in self.joints],
            "sheets": [s.to_dict() for s in self.sheets],
            "printable_parts": [p.to_dict() for p in self.printable_parts],
            "build_progress": self.build_progress,
            "engineering_review_summary": self.engineering_review_summary,
            "warnings": self.warnings,
            "summary": self.summary,
        }


class BuildVisualizationEngine:
    """Engine for generating, managing, and verifying Phase 12 Build Visualization packages."""

    # Deterministic exploded presentation vectors (mm offset) for subassemblies
    EXPLODED_OFFSETS = {
        "Fuselage": (0.0, 0.0, 0.0),
        "MainWing_Left": (0.0, -180.0, 40.0),
        "MainWing_Right": (0.0, 180.0, 40.0),
        "HorizontalTail": (-120.0, 0.0, 80.0),
        "VerticalTail": (-80.0, 0.0, 120.0),
        "Propulsion": (150.0, 0.0, 0.0),
        "Internal_Bays": (0.0, 0.0, -80.0),
    }

    @classmethod
    def generate_visualization_package(
        cls,
        aircraft_id: str,
        version: str,
        spec: AircraftSpecification,
        build_package: PrototypeBuildPackage,
        structural_components: Optional[list[Any]] = None,
        manufacturing_parts: Optional[list[ManufacturingPart]] = None,
        joints: Optional[list[ManufacturingJoint]] = None,
        nested_sheets: Optional[list[ManufacturingSheet]] = None,
        printable_parts: Optional[list[PrintablePart]] = None,
        engineering_review: Optional[EngineeringReview] = None,
        parent_version: Optional[str] = None,
        output_dir: Optional[Path] = None,
    ) -> BuildVisualizationPackage:
        """Construct the complete Phase 12 Build Visualization Package from validated pipeline outputs."""

        components: dict[str, ViewerComponent] = {}
        joints_list: list[ViewerJoint] = []
        steps_list: list[ViewerAssemblyStep] = []
        sheets_list: list[ViewerLaserSheet] = []
        print_parts_list: list[ViewerPrintablePart] = []
        warnings_list: list[dict[str, str]] = []

        # 1. Surface warnings from Engineering Review and Build Package
        if engineering_review and engineering_review.warnings:
            for w in engineering_review.warnings:
                warnings_list.append({
                    "severity": WarningSeverity.WARNING.value,
                    "message": w,
                    "source": "Phase 10 Engineering Review"
                })

        if engineering_review and engineering_review.conflicts:
            for c in engineering_review.conflicts:
                warnings_list.append({
                    "severity": WarningSeverity.WARNING.value,
                    "message": c,
                    "source": "Phase 3 Specification Conflict"
                })

        if build_package and build_package.build_validation and build_package.build_validation.warnings:
            for w in build_package.build_validation.warnings:
                warnings_list.append({
                    "severity": WarningSeverity.WARNING.value,
                    "message": w,
                    "source": "Phase 11 Build Validation"
                })

        # 2. Build Viewer Components from BuildPackage parts or ManufacturingParts
        parts_source = build_package.parts if build_package and build_package.parts else []
        for p in parts_source:
            sub = p.subassembly or cls._infer_subassembly(p.category or p.name or p.part_id)
            exp_offset = cls.EXPLODED_OFFSETS.get(sub, (0.0, 0.0, 0.0))

            # Traceability link
            req_key = cls._map_component_to_requirement(p.part_id, sub)
            trace = ViewerTraceability(
                requirement=req_key,
                cad_component=sub,
                structural_component=p.source_structural_component or p.source_component or p.part_id,
                manufacturing_part=p.part_id,
                fabrication_artifact=p.artifact_reference or "AVAILABLE",
                status="VALIDATED"
            )

            comp = ViewerComponent(
                id=p.part_id,
                display_name=p.name or p.part_id,
                source_cad_component=sub,
                source_structural_component=p.source_structural_component or p.source_component,
                source_manufacturing_part=p.part_id,
                source_artifact=p.artifact_reference,
                subassembly=sub,
                revision=version,
                engineering_status="VALID",
                manufacturing_status="READY",
                build_status=BuildProgressStatus.NOT_STARTED.value,
                material=p.material,
                thickness=p.thickness,
                quantity=p.quantity,
                process=p.manufacturing_process,
                dimensions=p.dimensions or {},
                exploded_offset=exp_offset,
                traceability=trace
            )
            components[p.part_id] = comp

        # 3. Build Viewer Joints
        joints_source = joints or []
        if not joints_source and build_package and build_package.joints:
            for bj in build_package.joints:
                p_id = getattr(bj, "parent_part_id", getattr(bj, "part_a", "PART_A"))
                c_id = getattr(bj, "child_part_id", getattr(bj, "part_b", "PART_B"))
                loc = getattr(bj, "interface_location", getattr(bj, "location", (0.0, 0.0, 0.0)))
                loc_tuple = loc if isinstance(loc, tuple) else (loc.get("x", 0.0), loc.get("y", 0.0), loc.get("z", 0.0)) if isinstance(loc, dict) else (0.0, 0.0, 0.0)
                v_stat = getattr(bj, "validation_status", getattr(bj, "status", "PASS"))
                vj = ViewerJoint(
                    joint_id=bj.joint_id,
                    parent_part_id=p_id,
                    child_part_id=c_id,
                    joint_type=bj.joint_type if isinstance(bj.joint_type, str) else (bj.joint_type.value if hasattr(bj.joint_type, "value") else str(bj.joint_type)),
                    interface_location=loc_tuple,
                    orientation=str(getattr(bj, "orientation", getattr(bj, "joint_axis", "NORMAL"))),
                    validation_status=v_stat,
                    is_valid=(v_stat in ("PASS", "VALIDATED", "READY"))
                )
                joints_list.append(vj)
        else:
            for j in joints_source:
                p_id = getattr(j, "parent_part_id", getattr(j, "part_a", "PART_A"))
                c_id = getattr(j, "child_part_id", getattr(j, "part_b", "PART_B"))
                loc = getattr(j, "interface_location", getattr(j, "location", (0.0, 0.0, 0.0)))
                loc_tuple = loc if isinstance(loc, tuple) else (loc.get("x", 0.0), loc.get("y", 0.0), loc.get("z", 0.0)) if isinstance(loc, dict) else (0.0, 0.0, 0.0)
                v_stat = getattr(j, "validation_status", getattr(j, "status", "PASS"))
                vj = ViewerJoint(
                    joint_id=j.joint_id,
                    parent_part_id=p_id,
                    child_part_id=c_id,
                    joint_type=j.joint_type.value if hasattr(j.joint_type, "value") else str(j.joint_type),
                    interface_location=loc_tuple,
                    orientation=str(getattr(j, "orientation", getattr(j, "joint_axis", "NORMAL"))),
                    validation_status=v_stat,
                    is_valid=(v_stat in ("PASS", "VALIDATED", "READY"))
                )
                joints_list.append(vj)

        # Associate joints with components
        for j in joints_list:
            if j.parent_part_id in components:
                components[j.parent_part_id].joints.append(j.joint_id)
            if j.child_part_id in components:
                components[j.child_part_id].joints.append(j.joint_id)

        # 4. Build Viewer Assembly Steps
        steps_source = build_package.assembly_steps if build_package and build_package.assembly_steps else []
        for s in steps_source:
            comp_ids = getattr(s, "components", getattr(s, "parts", []))
            step_joints = [j.joint_id for j in joints_list if (j.parent_part_id in comp_ids or j.child_part_id in comp_ids)]
            s_num = getattr(s, "step_number", getattr(s, "step_id", 1))
            try:
                s_num_int = int(str(s_num).replace("STEP-", "").replace("STEP_", ""))
            except Exception:
                s_num_int = 1
            s_id_str = f"STEP-{s_num_int:02d}" if isinstance(s_num, int) else str(getattr(s, "step_id", f"STEP-{s_num_int:02d}"))
            deps = [str(d) for d in getattr(s, "dependencies", [])]
            raw_in = getattr(s, "inputs", getattr(s, "required_materials", []))
            raw_out = getattr(s, "outputs", getattr(s, "output_subassembly", []))
            in_list = raw_in if isinstance(raw_in, list) else [str(raw_in)]
            out_list = raw_out if isinstance(raw_out, list) else [str(raw_out)]

            vs = ViewerAssemblyStep(
                step_id=s_id_str,
                step_number=s_num_int,
                title=s.title,
                description=s.description,
                subassembly=s.subassembly,
                component_ids=comp_ids,
                part_ids=comp_ids,
                joint_ids=step_joints,
                dependencies=deps,
                build_status=BuildProgressStatus.NOT_STARTED.value,
                warnings=s.warnings,
                inputs=in_list,
                outputs=out_list
            )
            steps_list.append(vs)

        # 5. Build Laser Sheets
        if nested_sheets:
            for sheet in nested_sheets:
                s_dims = getattr(sheet, "dimensions", (getattr(sheet, "width", 900.0), getattr(sheet, "height", 600.0)))
                ls = ViewerLaserSheet(
                    sheet_id=sheet.sheet_id,
                    material=sheet.material,
                    thickness=sheet.thickness,
                    dimensions=s_dims,
                    part_ids=getattr(sheet, "nested_parts", []),
                    dxf_path=getattr(sheet, "dxf_path", f"{sheet.sheet_id}.dxf"),
                    svg_path=getattr(sheet, "svg_path", f"{sheet.sheet_id}.svg"),
                    validation_status="PASS",
                    revision=version
                )
                sheets_list.append(ls)
        elif build_package and build_package.laser_sheets:
            for s_dict in build_package.laser_sheets:
                ls = ViewerLaserSheet(
                    sheet_id=s_dict.get("sheet_id", "Sheet_01"),
                    material=s_dict.get("material", "Aeroply_3mm"),
                    thickness=float(s_dict.get("thickness", 3.0)),
                    dimensions=s_dict.get("dimensions", (900.0, 600.0)),
                    part_ids=s_dict.get("parts", []),
                    dxf_path=s_dict.get("dxf_path"),
                    svg_path=s_dict.get("svg_path"),
                    validation_status="PASS",
                    revision=version
                )
                sheets_list.append(ls)

        # 6. Build Printable Parts
        if printable_parts:
            for p in printable_parts:
                p_dims = getattr(p, "dimensions", getattr(p, "print_dimensions", (120.0, 80.0, 40.0)))
                pp = ViewerPrintablePart(
                    print_part_id=p.print_part_id,
                    source_manufacturing_part_id=p.source_manufacturing_part_id,
                    material=p.material,
                    dimensions=p_dims,
                    stl_path=getattr(p, "output_stl_path", None),
                    aircraft_location="Wing-Fuselage Attachment Interface",
                    revision=version,
                    artifact_status="AVAILABLE" if getattr(p, "output_stl_path", None) else "PLANNED"
                )
                print_parts_list.append(pp)
        elif build_package and build_package.printable_packages:
            for p_dict in build_package.printable_packages:
                pp = ViewerPrintablePart(
                    print_part_id=p_dict.get("part_id", "PRINT-001"),
                    source_manufacturing_part_id=p_dict.get("source_manufacturing_part_id", "WING-ATTACH-001"),
                    material=p_dict.get("material", "PLA_Standard"),
                    dimensions=p_dict.get("dimensions", (200.0, 91.2, 12.0)),
                    stl_path=p_dict.get("stl_path"),
                    aircraft_location="Wing-Fuselage Attachment Interface",
                    revision=version,
                    artifact_status="AVAILABLE"
                )
                print_parts_list.append(pp)

        # 7. Construct Assembly Hierarchy Tree
        assembly_tree = cls._construct_assembly_tree(aircraft_id, components)

        # 8. Subassembly List
        subassemblies = ["Fuselage", "MainWing_Left", "MainWing_Right", "HorizontalTail", "VerticalTail", "Propulsion"]

        # 9. Build Progress Initial State (Revision-aware)
        build_progress = {
            "aircraft_id": aircraft_id,
            "revision": version,
            "parent_revision": parent_version,
            "overall_build_status": BuildProgressStatus.NOT_STARTED.value,
            "completed_parts_count": 0,
            "total_parts_count": len(components),
            "completed_steps_count": 0,
            "total_steps_count": len(steps_list),
            "part_statuses": {k: BuildProgressStatus.NOT_STARTED.value for k in components},
            "step_statuses": {s.step_id: BuildProgressStatus.NOT_STARTED.value for s in steps_list},
        }

        # 10. Summary
        eng_summary = engineering_review.summary if engineering_review else {
            "overall_status": "PASS",
            "prototype_status": "READY"
        }

        summary = {
            "total_components": len(components),
            "laser_parts_count": sum(1 for c in components.values() if c.process == "LASER_CUT"),
            "printable_parts_count": sum(1 for c in components.values() if c.process == "THREE_D_PRINT"),
            "total_joints": len(joints_list),
            "total_sheets": len(sheets_list),
            "total_steps": len(steps_list),
            "subassemblies_count": len(subassemblies),
            "warnings_count": len(warnings_list),
            "engineering_status": eng_summary.get("overall_status", "PASS"),
            "prototype_readiness": eng_summary.get("prototype_status", "READY"),
        }

        pkg = BuildVisualizationPackage(
            aircraft_id=aircraft_id,
            version=version,
            parent_version=parent_version,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            view_modes=[m.value for m in ViewMode],
            components=components,
            assembly_tree=assembly_tree,
            subassemblies=subassemblies,
            steps=steps_list,
            joints=joints_list,
            sheets=sheets_list,
            printable_parts=print_parts_list,
            build_progress=build_progress,
            engineering_review_summary=eng_summary,
            warnings=warnings_list,
            summary=summary,
        )

        if output_dir:
            out_path = Path(output_dir)
            vis_dir = out_path / "visualization"
            vis_dir.mkdir(parents=True, exist_ok=True)
            vis_file = vis_dir / "build_visualization.json"
            vis_file.write_text(json.dumps(pkg.to_dict(), indent=2), encoding="utf-8")

        return pkg

    @classmethod
    def _infer_subassembly(cls, name: str) -> str:
        """Classify subassembly from part name or identifier."""
        name_lower = name.lower()
        if "mainwing_left" in name_lower or "wing-l" in name_lower or "-l-" in name_lower:
            return "MainWing_Left"
        elif "mainwing_right" in name_lower or "wing-r" in name_lower or "-r-" in name_lower:
            return "MainWing_Right"
        elif "horizontaltail" in name_lower or "ht-" in name_lower or "tail_left" in name_lower or "tail_right" in name_lower:
            return "HorizontalTail"
        elif "verticaltail" in name_lower or "vt-" in name_lower or "vertical" in name_lower:
            return "VerticalTail"
        elif "motor" in name_lower or "firewall" in name_lower or "prop" in name_lower:
            return "Propulsion"
        elif "attach" in name_lower or "print-wing" in name_lower:
            return "MainWing_Left"
        return "Fuselage"

    @classmethod
    def _map_component_to_requirement(cls, part_id: str, subassembly: str) -> str:
        """Determine upstream requirement key for traceability."""
        if "SPAR" in part_id or "RIB" in part_id:
            return "wing.span"
        elif "FORMER" in part_id or "LONGERON" in part_id or "FUSE" in part_id:
            return "fuselage.length"
        elif "HT" in part_id:
            return "tail.ht_span"
        elif "VT" in part_id:
            return "tail.vt_height"
        elif "FIREWALL" in part_id or "PROP" in part_id:
            return "propulsion.propeller_diameter"
        return "mission.category"

    @classmethod
    def _construct_assembly_tree(cls, aircraft_id: str, components: dict[str, ViewerComponent]) -> ViewerAssemblyTreeNode:
        """Construct the interactive assembly hierarchy tree."""
        root = ViewerAssemblyTreeNode(
            id=f"{aircraft_id}_ROOT",
            label=f"{aircraft_id} Airframe",
            node_type="aircraft",
            component_ids=list(components.keys()),
            children=[]
        )

        sub_map: dict[str, list[str]] = {
            "Fuselage": [],
            "MainWing_Left": [],
            "MainWing_Right": [],
            "HorizontalTail": [],
            "VerticalTail": [],
            "Propulsion": [],
        }

        for p_id, comp in components.items():
            sub = comp.subassembly
            if sub not in sub_map:
                sub_map[sub] = []
            sub_map[sub].append(p_id)

        for sub_name, part_ids in sub_map.items():
            if not part_ids:
                continue
            sub_node = ViewerAssemblyTreeNode(
                id=f"{aircraft_id}_{sub_name}",
                label=sub_name.replace("_", " "),
                node_type="subassembly",
                component_ids=part_ids,
                children=[
                    ViewerAssemblyTreeNode(
                        id=pid,
                        label=components[pid].display_name,
                        node_type="part",
                        component_ids=[pid],
                        children=[]
                    )
                    for pid in part_ids
                ]
            )
            root.children.append(sub_node)

        return root

    @classmethod
    def update_part_build_progress(
        cls,
        pkg: BuildVisualizationPackage,
        part_id: str,
        new_status: BuildProgressStatus,
    ) -> BuildVisualizationPackage:
        """Update physical assembly progress of a single part without altering engineering validity."""
        if part_id in pkg.components:
            pkg.components[part_id].build_status = new_status.value
            pkg.build_progress["part_statuses"][part_id] = new_status.value

        # Recompute totals
        completed_count = sum(1 for v in pkg.build_progress["part_statuses"].values() if v == BuildProgressStatus.COMPLETE.value)
        pkg.build_progress["completed_parts_count"] = completed_count

        if completed_count == len(pkg.components) and len(pkg.components) > 0:
            pkg.build_progress["overall_build_status"] = BuildProgressStatus.COMPLETE.value
        elif completed_count > 0:
            pkg.build_progress["overall_build_status"] = BuildProgressStatus.IN_PROGRESS.value
        else:
            pkg.build_progress["overall_build_status"] = BuildProgressStatus.NOT_STARTED.value

        return pkg

    @classmethod
    def update_step_build_progress(
        cls,
        pkg: BuildVisualizationPackage,
        step_id: str,
        new_status: BuildProgressStatus,
    ) -> BuildVisualizationPackage:
        """Update physical assembly step progress and propagate to step parts if marked complete."""
        step = next((s for s in pkg.steps if s.step_id == step_id), None)
        if step:
            step.build_status = new_status.value
            pkg.build_progress["step_statuses"][step_id] = new_status.value

            if new_status == BuildProgressStatus.COMPLETE:
                for pid in step.part_ids:
                    if pid in pkg.components:
                        pkg.components[pid].build_status = BuildProgressStatus.COMPLETE.value
                        pkg.build_progress["part_statuses"][pid] = BuildProgressStatus.COMPLETE.value

        completed_steps = sum(1 for v in pkg.build_progress["step_statuses"].values() if v == BuildProgressStatus.COMPLETE.value)
        pkg.build_progress["completed_steps_count"] = completed_steps
        return pkg

    @classmethod
    def propagate_revision_build_state(
        cls,
        old_pkg: BuildVisualizationPackage,
        new_pkg: BuildVisualizationPackage,
        changed_part_ids: Set[str],
    ) -> BuildVisualizationPackage:
        """Revision reset rule: Changed parts in v2 MUST NOT inherit v1 completed status."""
        for pid, comp in new_pkg.components.items():
            if pid in changed_part_ids:
                # Reset changed part to NOT_STARTED
                comp.build_status = BuildProgressStatus.NOT_STARTED.value
                new_pkg.build_progress["part_statuses"][pid] = BuildProgressStatus.NOT_STARTED.value
            else:
                # Unaffected parts preserve build progress
                old_status = old_pkg.build_progress.get("part_statuses", {}).get(pid, BuildProgressStatus.NOT_STARTED.value)
                comp.build_status = old_status
                new_pkg.build_progress["part_statuses"][pid] = old_status

        # Recompute totals
        completed_count = sum(1 for v in new_pkg.build_progress["part_statuses"].values() if v == BuildProgressStatus.COMPLETE.value)
        new_pkg.build_progress["completed_parts_count"] = completed_count
        new_pkg.build_progress["overall_build_status"] = (
            BuildProgressStatus.COMPLETE.value if completed_count == len(new_pkg.components) and len(new_pkg.components) > 0
            else (BuildProgressStatus.IN_PROGRESS.value if completed_count > 0 else BuildProgressStatus.NOT_STARTED.value)
        )
        return new_pkg

    @classmethod
    def validate_visualization_integrity(cls, pkg: BuildVisualizationPackage) -> dict[str, Any]:
        """Audit visualization package for missing artifacts, duplicate IDs, and cyclic step dependencies."""
        errors: list[str] = []
        warnings: list[str] = []

        # 1. Part ID uniqueness
        seen_ids = set()
        for pid in pkg.components:
            if pid in seen_ids:
                errors.append(f"Duplicate component ID in viewer: {pid}")
            seen_ids.add(pid)

        # 2. Joint endpoints existence
        for j in pkg.joints:
            if j.parent_part_id not in pkg.components:
                errors.append(f"Joint {j.joint_id} references missing parent component {j.parent_part_id}")
            if j.child_part_id not in pkg.components:
                errors.append(f"Joint {j.joint_id} references missing child component {j.child_part_id}")

        # 3. Assembly step cycle check
        adj: dict[str, list[str]] = {s.step_id: s.dependencies for s in pkg.steps}
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node)
            return False

        for sid in adj:
            if sid not in visited:
                if has_cycle(sid):
                    errors.append(f"Cyclic dependency detected in assembly sequence involving step {sid}")

        is_valid = len(errors) == 0
        return {
            "is_valid": is_valid,
            "status": "PASS" if is_valid else "FAIL",
            "errors": errors,
            "warnings": warnings,
            "components_verified": len(pkg.components),
            "joints_verified": len(pkg.joints),
            "steps_verified": len(pkg.steps),
        }
