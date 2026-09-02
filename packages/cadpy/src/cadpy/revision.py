"""Engineering design revision, change detection, dependency tracking, impact analysis, and selective regeneration."""

from __future__ import annotations

import copy
import datetime
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from cadpy.requirements import (
    AircraftSpecification,
    Requirement,
    parse_aircraft_specification,
)


class ChangeType(str, Enum):
    """Classification of requirement changes between two specification revisions."""
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    MODIFIED = "MODIFIED"
    STATUS_CHANGED = "STATUS_CHANGED"
    UNIT_ONLY = "UNIT_ONLY"
    CONFLICT_CHANGED = "CONFLICT_CHANGED"
    UNCHANGED = "UNCHANGED"


class ChangeSeverity(str, Enum):
    """Deterministic severity based on engineering dependency scope."""
    INFO = "INFO"        # Document metadata, non-geometric notes
    LOW = "LOW"          # Tolerances, minor non-load interfaces
    MEDIUM = "MEDIUM"    # Local component sizing, secondary surfaces
    HIGH = "HIGH"        # Major load-bearing geometry (wingspan, fuselage length)
    CRITICAL = "CRITICAL"# Configuration topology change (wing position, propulsion layout)


class ImpactCategory(str, Enum):
    """Impact classification for downstream CAD, structural, and manufacturing items."""
    DIRECTLY_AFFECTED = "DIRECTLY_AFFECTED"
    INDIRECTLY_AFFECTED = "INDIRECTLY_AFFECTED"
    UNAFFECTED = "UNAFFECTED"
    UNKNOWN = "UNKNOWN"


class ArtifactRevisionStatus(str, Enum):
    """Lifecycle status of artifacts relative to a revision."""
    VALID = "VALID"
    STALE = "STALE"
    INVALIDATED = "INVALIDATED"
    REGENERATED = "REGENERATED"
    PRESERVED = "PRESERVED"


@dataclass
class RequirementChange:
    """Structured representation of a single requirement delta between two specifications."""
    parameter: str
    category: str
    old_value: Any
    new_value: Any
    old_unit: str
    new_unit: str
    old_status: str
    new_status: str
    source_v1: str = ""
    source_v2: str = ""
    change_type: str = ChangeType.UNCHANGED.value
    severity: str = ChangeSeverity.INFO.value
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameter": self.parameter,
            "category": self.category,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "old_unit": self.old_unit,
            "new_unit": self.new_unit,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "source_v1": self.source_v1,
            "source_v2": self.source_v2,
            "change_type": self.change_type,
            "severity": self.severity,
            "description": self.description,
        }


@dataclass
class ImpactResult:
    """Comprehensive impact analysis result of requirement changes across downstream models."""
    changed_requirements: list[RequirementChange] = field(default_factory=list)
    affected_cad_components: dict[str, str] = field(default_factory=dict)
    affected_structural_components: dict[str, str] = field(default_factory=dict)
    affected_manufacturing_parts: dict[str, str] = field(default_factory=dict)
    affected_artifacts: dict[str, str] = field(default_factory=dict)
    unaffected_components: list[str] = field(default_factory=list)
    unaffected_artifacts: list[str] = field(default_factory=list)
    impact_level: str = ChangeSeverity.LOW.value
    can_selectively_regenerate: bool = False
    selective_scope: list[str] = field(default_factory=list)
    requires_user_confirmation: bool = False
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "changed_requirements_count": len(self.changed_requirements),
            "changed_requirements": [c.to_dict() for c in self.changed_requirements],
            "affected_cad_count": sum(1 for v in self.affected_cad_components.values() if v != ImpactCategory.UNAFFECTED.value),
            "affected_cad_components": self.affected_cad_components,
            "affected_structural_count": sum(1 for v in self.affected_structural_components.values() if v != ImpactCategory.UNAFFECTED.value),
            "affected_structural_components": self.affected_structural_components,
            "affected_manufacturing_count": sum(1 for v in self.affected_manufacturing_parts.values() if v != ImpactCategory.UNAFFECTED.value),
            "affected_manufacturing_parts": self.affected_manufacturing_parts,
            "unaffected_components_count": len(self.unaffected_components),
            "unaffected_components": self.unaffected_components,
            "affected_artifacts": self.affected_artifacts,
            "unaffected_artifacts": self.unaffected_artifacts,
            "impact_level": self.impact_level,
            "can_selectively_regenerate": self.can_selectively_regenerate,
            "selective_scope": self.selective_scope,
            "requires_user_confirmation": self.requires_user_confirmation,
            "summary": self.summary,
        }


@dataclass
class RevisionManifest:
    """Immutable manifest recording an engineering design revision."""
    aircraft_id: str
    version: str
    parent_version: str
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    changes: list[dict[str, Any]] = field(default_factory=list)
    impact_summary: dict[str, Any] = field(default_factory=dict)
    affected_components_count: int = 0
    unaffected_components_count: int = 0
    selective_regeneration_used: bool = False
    created_artifacts: list[str] = field(default_factory=list)
    preserved_artifacts: list[str] = field(default_factory=list)
    invalidated_artifacts: list[str] = field(default_factory=list)
    pipeline_status: str = "PASS"
    validation_status: str = "PASS"
    prototype_readiness: str = "READY"

    def to_dict(self) -> dict[str, Any]:
        return {
            "aircraft_id": self.aircraft_id,
            "version": self.version,
            "parent_version": self.parent_version,
            "created_at": self.created_at,
            "changes_count": len(self.changes),
            "changes": self.changes,
            "impact_summary": self.impact_summary,
            "affected_components_count": self.affected_components_count,
            "unaffected_components_count": self.unaffected_components_count,
            "selective_regeneration_used": self.selective_regeneration_used,
            "created_artifacts": self.created_artifacts,
            "preserved_artifacts": self.preserved_artifacts,
            "invalidated_artifacts": self.invalidated_artifacts,
            "pipeline_status": self.pipeline_status,
            "validation_status": self.validation_status,
            "prototype_readiness": self.prototype_readiness,
        }


class RequirementDiffEngine:
    """Compares two normalized Phase 3 aircraft specifications and computes structured diffs."""

    @classmethod
    def _extract_flattened_requirements(cls, spec: AircraftSpecification) -> dict[str, tuple[str, Requirement]]:
        """Flatten an AircraftSpecification into a dict of param_name -> (category, Requirement)."""
        res: dict[str, tuple[str, Requirement]] = {}
        for cat_name in [
            "identity",
            "mission",
            "configuration",
            "wing",
            "fuselage",
            "tail",
            "bays",
            "propulsion",
            "electronics",
            "payload",
            "mass",
            "performance",
        ]:
            cat_obj = getattr(spec, cat_name, None)
            if not cat_obj:
                continue
            for k, v in vars(cat_obj).items():
                if isinstance(v, Requirement):
                    full_key = f"{cat_name}.{k}"
                    res[full_key] = (cat_name, v)
        return res

    @classmethod
    def _normalize_value_for_comparison(cls, req: Requirement) -> tuple[Any, str]:
        """Convert a requirement value and unit into standard canonical numeric form where possible."""
        val = req.value
        unit = (req.unit or "").strip().lower()

        if val is None:
            return None, unit

        # Handle numeric equivalence with unit scaling
        if isinstance(val, (int, float)):
            num_val = float(val)
            if unit in ["m", "meter", "meters"]:
                return round(num_val * 1000.0, 4), "mm"
            if unit in ["cm", "centimeter", "centimeters"]:
                return round(num_val * 10.0, 4), "mm"
            if unit in ["mm", "millimeter", "millimeters"]:
                return round(num_val, 4), "mm"
            if unit in ["in", "inch", "inches"]:
                return round(num_val * 25.4, 4), "mm"
            if unit in ["g", "gram", "grams"]:
                return round(num_val / 1000.0, 4), "kg"
            if unit in ["kg", "kilogram", "kilograms"]:
                return round(num_val, 4), "kg"
            if unit in ["hr", "hour", "hours"]:
                return round(num_val * 60.0, 4), "minutes"
            if unit in ["min", "minute", "minutes"]:
                return round(num_val, 4), "minutes"
            return round(num_val, 4), unit

        if isinstance(val, str):
            clean_str = val.strip().lower()
            return clean_str, unit

        return val, unit

    @classmethod
    def compare_specifications(
        cls,
        spec_v1: AircraftSpecification,
        spec_v2: AircraftSpecification
    ) -> list[RequirementChange]:
        """Compare two specifications and return detailed list of changes."""
        flat_v1 = cls._extract_flattened_requirements(spec_v1)
        flat_v2 = cls._extract_flattened_requirements(spec_v2)

        all_keys = sorted(set(flat_v1.keys()) | set(flat_v2.keys()))
        changes: list[RequirementChange] = []

        for key in all_keys:
            cat_1, req_1 = flat_v1.get(key, ("", Requirement(None, "", "", "", "UNKNOWN")))
            cat_2, req_2 = flat_v2.get(key, ("", Requirement(None, "", "", "", "UNKNOWN")))
            cat = cat_2 or cat_1

            norm_val_1, norm_u_1 = cls._normalize_value_for_comparison(req_1)
            norm_val_2, norm_u_2 = cls._normalize_value_for_comparison(req_2)

            is_added = key not in flat_v1 or req_1.status == "UNKNOWN" and req_2.status != "UNKNOWN"
            is_removed = key not in flat_v2 or req_2.status == "UNKNOWN" and req_1.status != "UNKNOWN"

            # 1. Added
            if is_added and not is_removed and key not in flat_v1:
                changes.append(RequirementChange(
                    parameter=key,
                    category=cat,
                    old_value=None,
                    new_value=req_2.value,
                    old_unit="",
                    new_unit=req_2.unit,
                    old_status="UNKNOWN",
                    new_status=req_2.status,
                    source_v1="",
                    source_v2=req_2.source,
                    change_type=ChangeType.ADDED.value,
                    severity=cls._determine_severity(key, ChangeType.ADDED),
                    description=f"Requirement '{key}' added with value {req_2.value} {req_2.unit}"
                ))
                continue

            # 2. Removed
            if is_removed and not is_added and key not in flat_v2:
                changes.append(RequirementChange(
                    parameter=key,
                    category=cat,
                    old_value=req_1.value,
                    new_value=None,
                    old_unit=req_1.unit,
                    new_unit="",
                    old_status=req_1.status,
                    new_status="UNKNOWN",
                    source_v1=req_1.source,
                    source_v2="",
                    change_type=ChangeType.REMOVED.value,
                    severity=cls._determine_severity(key, ChangeType.REMOVED),
                    description=f"Requirement '{key}' removed (was {req_1.value} {req_1.unit})"
                ))
                continue

            # 3. Status Changed (e.g. UNKNOWN -> EXPLICIT, EXPLICIT -> DERIVED, EXPLICIT -> CONFLICT)
            status_changed = req_1.status != req_2.status
            conflict_changed = (req_1.status == "CONFLICT" or req_2.status == "CONFLICT") and status_changed

            # 4. Values Comparison
            val_changed = norm_val_1 != norm_val_2
            unit_changed = norm_u_1 != norm_u_2

            if conflict_changed:
                changes.append(RequirementChange(
                    parameter=key,
                    category=cat,
                    old_value=req_1.value,
                    new_value=req_2.value,
                    old_unit=req_1.unit,
                    new_unit=req_2.unit,
                    old_status=req_1.status,
                    new_status=req_2.status,
                    source_v1=req_1.source,
                    source_v2=req_2.source,
                    change_type=ChangeType.CONFLICT_CHANGED.value,
                    severity=ChangeSeverity.HIGH.value if req_2.status == "CONFLICT" else ChangeSeverity.MEDIUM.value,
                    description=f"Conflict status changed from {req_1.status} to {req_2.status}"
                ))
            elif val_changed:
                changes.append(RequirementChange(
                    parameter=key,
                    category=cat,
                    old_value=req_1.value,
                    new_value=req_2.value,
                    old_unit=req_1.unit,
                    new_unit=req_2.unit,
                    old_status=req_1.status,
                    new_status=req_2.status,
                    source_v1=req_1.source,
                    source_v2=req_2.source,
                    change_type=ChangeType.MODIFIED.value,
                    severity=cls._determine_severity(key, ChangeType.MODIFIED),
                    description=f"Value modified: {req_1.value} {req_1.unit} -> {req_2.value} {req_2.unit}"
                ))
            elif status_changed:
                changes.append(RequirementChange(
                    parameter=key,
                    category=cat,
                    old_value=req_1.value,
                    new_value=req_2.value,
                    old_unit=req_1.unit,
                    new_unit=req_2.unit,
                    old_status=req_1.status,
                    new_status=req_2.status,
                    source_v1=req_1.source,
                    source_v2=req_2.source,
                    change_type=ChangeType.STATUS_CHANGED.value,
                    severity=ChangeSeverity.LOW.value if cat == "identity" else ChangeSeverity.MEDIUM.value,
                    description=f"Provenance status changed: {req_1.status} -> {req_2.status}"
                ))
            elif unit_changed and req_1.value is not None:
                changes.append(RequirementChange(
                    parameter=key,
                    category=cat,
                    old_value=req_1.value,
                    new_value=req_2.value,
                    old_unit=req_1.unit,
                    new_unit=req_2.unit,
                    old_status=req_1.status,
                    new_status=req_2.status,
                    source_v1=req_1.source,
                    source_v2=req_2.source,
                    change_type=ChangeType.UNIT_ONLY.value,
                    severity=ChangeSeverity.INFO.value,
                    description=f"Unit formatting changed: {req_1.unit} -> {req_2.unit}"
                ))

        return changes

    @classmethod
    def compare_specification_texts(
        cls,
        text_v1: str,
        text_v2: str,
        source_name: str = "AIRCRAFT"
    ) -> list[RequirementChange]:
        """Parse two raw specification markdown texts and return their requirement diff."""
        spec_1 = parse_aircraft_specification(text_v1, source_name=f"{source_name}_v1")
        spec_2 = parse_aircraft_specification(text_v2, source_name=f"{source_name}_v2")
        return cls.compare_specifications(spec_1, spec_2)

    @classmethod
    def _determine_severity(cls, parameter: str, change_type: ChangeType) -> str:
        """Assign deterministic severity based on parameter engineering role."""
        param_lower = parameter.lower()
        if any(k in param_lower for k in ["configuration.wing_position", "configuration.propulsion_layout", "configuration.tail_configuration"]):
            return ChangeSeverity.CRITICAL.value
        if any(k in param_lower for k in ["wing.span", "fuselage.length", "tail.ht_span", "tail.vt_height", "propulsion.propeller_diameter"]):
            return ChangeSeverity.HIGH.value
        if any(k in param_lower for k in ["wing.root_chord", "wing.tip_chord", "fuselage.width", "fuselage.height", "wing.dihedral", "wing.sweep"]):
            return ChangeSeverity.MEDIUM.value
        if any(k in param_lower for k in ["mass.", "payload.", "battery.", "avionics.", "performance."]):
            return ChangeSeverity.MEDIUM.value
        if any(k in param_lower for k in ["identity.", "mission.category", "mission.title"]):
            return ChangeSeverity.INFO.value
        return ChangeSeverity.LOW.value

    @classmethod
    def format_human_readable_diff(cls, changes: list[RequirementChange]) -> str:
        """Format changes into human-readable engineering change report."""
        if not changes:
            return "ENGINEERING CHANGES\n  No changes detected between specifications."

        lines = ["ENGINEERING CHANGES"]
        by_category: dict[str, list[RequirementChange]] = {}
        for c in changes:
            by_category.setdefault(c.category.title(), []).append(c)

        for cat, cat_changes in by_category.items():
            lines.append(f"\n{cat}")
            for c in cat_changes:
                param_name = c.parameter.split(".")[-1].replace("_", " ").title()
                if c.change_type == ChangeType.MODIFIED.value:
                    lines.append(f"  {param_name}:")
                    lines.append(f"    {c.old_value} {c.old_unit} → {c.new_value} {c.new_unit} [{c.severity}]")
                elif c.change_type == ChangeType.STATUS_CHANGED.value:
                    lines.append(f"  {param_name} (Status):")
                    lines.append(f"    {c.old_status} → {c.new_status}")
                elif c.change_type == ChangeType.ADDED.value:
                    lines.append(f"  {param_name} [ADDED]:")
                    lines.append(f"    {c.new_value} {c.new_unit} ({c.new_status})")
                elif c.change_type == ChangeType.REMOVED.value:
                    lines.append(f"  {param_name} [REMOVED]:")
                    lines.append(f"    was {c.old_value} {c.old_unit}")
                elif c.change_type == ChangeType.CONFLICT_CHANGED.value:
                    lines.append(f"  {param_name} [CONFLICT]:")
                    lines.append(f"    {c.old_status} → {c.new_status} ({c.description})")
                else:
                    lines.append(f"  {param_name}: {c.change_type}")

        return "\n".join(lines)


class DependencyGraph:
    """Deterministic forward dependency mapping from Requirements to CAD, Structure, Manufacturing, and Artifacts."""

    # Explicit CAD Component Mapping
    CAD_DEPENDENCIES: dict[str, list[str]] = {
        "wing": ["MainWing", "MainWing_Left", "MainWing_Right"],
        "fuselage": ["Fuselage"],
        "tail.ht": ["HorizontalTail", "HT_Left", "HT_Right"],
        "tail.vt": ["VerticalTail"],
        "propulsion": ["Propulsion", "Motor", "Propeller"],
        "bays.payload": ["PayloadBay"],
        "bays.battery": ["BatteryBay"],
        "bays.avionics": ["AvionicsBay"],
    }

    # Explicit Structural Component Mapping
    STRUCTURAL_DEPENDENCIES: dict[str, list[str]] = {
        "wing": [
            "MainWing_Left_MainSpar", "MainWing_Left_RearSpar",
            "MainWing_Right_MainSpar", "MainWing_Right_RearSpar",
            "MainWing_Left_Rib_000", "MainWing_Left_Rib_001", "MainWing_Left_Rib_002", "MainWing_Left_Rib_003",
            "MainWing_Left_Rib_004", "MainWing_Left_Rib_005", "MainWing_Left_Rib_006", "MainWing_Left_Rib_007",
            "MainWing_Left_Rib_008", "MainWing_Left_Rib_009",
            "MainWing_Right_Rib_000", "MainWing_Right_Rib_001", "MainWing_Right_Rib_002", "MainWing_Right_Rib_003",
            "MainWing_Right_Rib_004", "MainWing_Right_Rib_005", "MainWing_Right_Rib_006", "MainWing_Right_Rib_007",
            "MainWing_Right_Rib_008", "MainWing_Right_Rib_009",
            "WingFuselage_Attachment"
        ],
        "fuselage": [
            "Fuselage_Firewall",
            "Fuselage_Former_001", "Fuselage_Former_002", "Fuselage_Former_003", "Fuselage_Former_004",
            "Fuselage_Former_005", "Fuselage_Former_006", "Fuselage_Former_007",
            "Fuselage_Longeron_UpperLeft", "Fuselage_Longeron_UpperRight",
            "Fuselage_Longeron_LowerLeft", "Fuselage_Longeron_LowerRight"
        ],
        "tail.ht": [
            "HT_Spar_Main", "HT_Spar_Rear",
            "HT_Left_Rib_000", "HT_Left_Rib_001", "HT_Left_Rib_002",
            "HT_Right_Rib_000", "HT_Right_Rib_001", "HT_Right_Rib_002"
        ],
        "tail.vt": [
            "VT_Spar_Main",
            "VT_Rib_000", "VT_Rib_001", "VT_Rib_002"
        ],
        "propulsion": [
            "Fuselage_Firewall"
        ],
    }

    # Explicit Manufacturing Part Mapping
    MANUFACTURING_PART_DEPENDENCIES: dict[str, list[str]] = {
        "wing": [
            "SPAR-L-MAIN", "SPAR-L-REAR", "SPAR-R-MAIN", "SPAR-R-REAR",
            "RIB-L-000", "RIB-L-001", "RIB-L-002", "RIB-L-003", "RIB-L-004",
            "RIB-L-005", "RIB-L-006", "RIB-L-007", "RIB-L-008", "RIB-L-009",
            "RIB-R-000", "RIB-R-001", "RIB-R-002", "RIB-R-003", "RIB-R-004",
            "RIB-R-005", "RIB-R-006", "RIB-R-007", "RIB-R-008", "RIB-R-009",
            "WING-ATTACH-001"
        ],
        "fuselage": [
            "FIREWALL-001",
            "FMR-001", "FMR-002", "FMR-003", "FMR-004", "FMR-005", "FMR-006", "FMR-007",
            "LONG-UPPER-L", "LONG-UPPER-R", "LONG-LOWER-L", "LONG-LOWER-R"
        ],
        "tail.ht": [
            "HT-SPAR-MAIN", "HT-SPAR-REAR",
            "HT-RIB-L-000", "HT-RIB-L-001", "HT-RIB-L-002",
            "HT-RIB-R-000", "HT-RIB-R-001", "HT-RIB-R-002"
        ],
        "tail.vt": [
            "VT-SPAR-MAIN",
            "VT-RIB-000", "VT-RIB-001", "VT-RIB-002"
        ],
        "propulsion": [
            "FIREWALL-001"
        ],
    }

    @classmethod
    def resolve_affected_cad_components(cls, param_key: str) -> list[str]:
        """Find CAD components affected by a parameter key."""
        cat = param_key.split(".")[0].lower()
        if cat == "wing":
            return cls.CAD_DEPENDENCIES["wing"]
        if cat == "fuselage":
            return cls.CAD_DEPENDENCIES["fuselage"]
        if cat == "tail":
            if "ht" in param_key.lower():
                return cls.CAD_DEPENDENCIES["tail.ht"]
            if "vt" in param_key.lower():
                return cls.CAD_DEPENDENCIES["tail.vt"]
            return cls.CAD_DEPENDENCIES["tail.ht"] + cls.CAD_DEPENDENCIES["tail.vt"]
        if cat == "propulsion":
            return cls.CAD_DEPENDENCIES["propulsion"]
        if cat == "payload":
            return cls.CAD_DEPENDENCIES["bays.payload"]
        if cat == "bays":
            return cls.CAD_DEPENDENCIES["bays.payload"] + cls.CAD_DEPENDENCIES["bays.battery"] + cls.CAD_DEPENDENCIES["bays.avionics"]
        if cat == "configuration":
            # Topology change impacts all major CAD components
            return ["MainWing", "Fuselage", "HorizontalTail", "VerticalTail", "Propulsion"]
        return []

    @classmethod
    def resolve_affected_structural_components(cls, param_key: str) -> list[str]:
        """Find structural components affected by a parameter key."""
        cat = param_key.split(".")[0].lower()
        if cat == "wing":
            return cls.STRUCTURAL_DEPENDENCIES["wing"]
        if cat == "fuselage":
            return cls.STRUCTURAL_DEPENDENCIES["fuselage"]
        if cat == "tail":
            if "ht" in param_key.lower():
                return cls.STRUCTURAL_DEPENDENCIES["tail.ht"]
            if "vt" in param_key.lower():
                return cls.STRUCTURAL_DEPENDENCIES["tail.vt"]
            return cls.STRUCTURAL_DEPENDENCIES["tail.ht"] + cls.STRUCTURAL_DEPENDENCIES["tail.vt"]
        if cat == "propulsion":
            return cls.STRUCTURAL_DEPENDENCIES["propulsion"]
        if cat == "payload" or cat == "bays":
            # Internal bay changes affect formers partitioning the bays
            return ["Fuselage_Former_003", "Fuselage_Former_004", "Fuselage_Former_005"]
        if cat == "configuration":
            all_struct: list[str] = []
            for group in cls.STRUCTURAL_DEPENDENCIES.values():
                all_struct.extend(group)
            return all_struct
        return []

    @classmethod
    def resolve_affected_manufacturing_parts(cls, param_key: str) -> list[str]:
        """Find manufacturing parts affected by a parameter key."""
        cat = param_key.split(".")[0].lower()
        if cat == "wing":
            return cls.MANUFACTURING_PART_DEPENDENCIES["wing"]
        if cat == "fuselage":
            return cls.MANUFACTURING_PART_DEPENDENCIES["fuselage"]
        if cat == "tail":
            if "ht" in param_key.lower():
                return cls.MANUFACTURING_PART_DEPENDENCIES["tail.ht"]
            if "vt" in param_key.lower():
                return cls.MANUFACTURING_PART_DEPENDENCIES["tail.vt"]
            return cls.MANUFACTURING_PART_DEPENDENCIES["tail.ht"] + cls.MANUFACTURING_PART_DEPENDENCIES["tail.vt"]
        if cat == "propulsion":
            return cls.MANUFACTURING_PART_DEPENDENCIES["propulsion"]
        if cat == "payload" or cat == "bays":
            return ["FMR-003", "FMR-004", "FMR-005"]
        if cat == "configuration":
            all_mfg: list[str] = []
            for group in cls.MANUFACTURING_PART_DEPENDENCIES.values():
                all_mfg.extend(group)
            return all_mfg
        return []


class ImpactAnalysisEngine:
    """Analyzes a list of RequirementChanges and determines exact downstream impact."""

    ALL_KNOWN_CAD_COMPONENTS = [
        "MainWing", "MainWing_Left", "MainWing_Right", "Fuselage",
        "HorizontalTail", "HT_Left", "HT_Right", "VerticalTail",
        "Propulsion", "Motor", "Propeller", "PayloadBay", "BatteryBay", "AvionicsBay"
    ]

    ALL_KNOWN_STRUCTURAL_COMPONENTS = (
        DependencyGraph.STRUCTURAL_DEPENDENCIES["wing"] +
        DependencyGraph.STRUCTURAL_DEPENDENCIES["fuselage"] +
        DependencyGraph.STRUCTURAL_DEPENDENCIES["tail.ht"] +
        DependencyGraph.STRUCTURAL_DEPENDENCIES["tail.vt"]
    )

    ALL_KNOWN_MANUFACTURING_PARTS = (
        DependencyGraph.MANUFACTURING_PART_DEPENDENCIES["wing"] +
        DependencyGraph.MANUFACTURING_PART_DEPENDENCIES["fuselage"] +
        DependencyGraph.MANUFACTURING_PART_DEPENDENCIES["tail.ht"] +
        DependencyGraph.MANUFACTURING_PART_DEPENDENCIES["tail.vt"]
    )

    @classmethod
    def analyze_impact(
        cls,
        changes: list[RequirementChange],
        is_manufacturing_profile_change: bool = False
    ) -> ImpactResult:
        """Compute full downstream impact matrix for a list of specification changes."""
        res = ImpactResult(changed_requirements=changes)

        # 1. If only manufacturing profile changed (no requirement diffs)
        if is_manufacturing_profile_change:
            res.impact_level = ChangeSeverity.LOW.value
            res.can_selectively_regenerate = True
            res.selective_scope = ["PHASE_6D_LASER", "PHASE_6E_PRINT", "PHASE_6F_VALIDATION"]
            # All CAD and structural components remain UNAFFECTED
            for c in cls.ALL_KNOWN_CAD_COMPONENTS:
                res.affected_cad_components[c] = ImpactCategory.UNAFFECTED.value
            for s in cls.ALL_KNOWN_STRUCTURAL_COMPONENTS:
                res.affected_structural_components[s] = ImpactCategory.UNAFFECTED.value
            for m in cls.ALL_KNOWN_MANUFACTURING_PARTS:
                res.affected_manufacturing_parts[m] = ImpactCategory.DIRECTLY_AFFECTED.value

            res.unaffected_components = cls.ALL_KNOWN_CAD_COMPONENTS + cls.ALL_KNOWN_STRUCTURAL_COMPONENTS
            res.summary = {
                "change_scope": "MANUFACTURING_PROFILE_ONLY",
                "cad_regenerated": False,
                "structure_regenerated": False,
                "manufacturing_regenerated": True,
            }
            return res

        # 2. If no requirement changes detected
        if not changes:
            res.impact_level = ChangeSeverity.INFO.value
            res.can_selectively_regenerate = False
            for c in cls.ALL_KNOWN_CAD_COMPONENTS:
                res.affected_cad_components[c] = ImpactCategory.UNAFFECTED.value
            for s in cls.ALL_KNOWN_STRUCTURAL_COMPONENTS:
                res.affected_structural_components[s] = ImpactCategory.UNAFFECTED.value
            for m in cls.ALL_KNOWN_MANUFACTURING_PARTS:
                res.affected_manufacturing_parts[m] = ImpactCategory.UNAFFECTED.value
            res.unaffected_components = cls.ALL_KNOWN_CAD_COMPONENTS + cls.ALL_KNOWN_STRUCTURAL_COMPONENTS + cls.ALL_KNOWN_MANUFACTURING_PARTS
            res.summary = {"change_scope": "NO_CHANGES"}
            return res

        # 3. Analyze each change through the dependency graph
        affected_cad_set: set[str] = set()
        affected_struct_set: set[str] = set()
        affected_mfg_set: set[str] = set()
        highest_severity = ChangeSeverity.INFO

        severity_rank = {
            ChangeSeverity.INFO.value: 1,
            ChangeSeverity.LOW.value: 2,
            ChangeSeverity.MEDIUM.value: 3,
            ChangeSeverity.HIGH.value: 4,
            ChangeSeverity.CRITICAL.value: 5,
        }

        for c in changes:
            if c.change_type in [ChangeType.UNCHANGED.value, ChangeType.UNIT_ONLY.value]:
                continue

            # Update highest severity
            if severity_rank.get(c.severity, 1) > severity_rank.get(highest_severity.value, 1):
                highest_severity = ChangeSeverity(c.severity)

            # Metadata only changes don't affect geometry
            if c.category in ["identity"] and c.change_type != ChangeType.CONFLICT_CHANGED.value:
                continue

            # Resolve downstream nodes
            c_cad = DependencyGraph.resolve_affected_cad_components(c.parameter)
            c_struct = DependencyGraph.resolve_affected_structural_components(c.parameter)
            c_mfg = DependencyGraph.resolve_affected_manufacturing_parts(c.parameter)

            affected_cad_set.update(c_cad)
            affected_struct_set.update(c_struct)
            affected_mfg_set.update(c_mfg)

        res.impact_level = highest_severity.value

        # Populate dictionaries
        for c in cls.ALL_KNOWN_CAD_COMPONENTS:
            if c in affected_cad_set:
                res.affected_cad_components[c] = ImpactCategory.DIRECTLY_AFFECTED.value
            else:
                res.affected_cad_components[c] = ImpactCategory.UNAFFECTED.value
                res.unaffected_components.append(c)

        for s in cls.ALL_KNOWN_STRUCTURAL_COMPONENTS:
            if s in affected_struct_set:
                res.affected_structural_components[s] = ImpactCategory.INDIRECTLY_AFFECTED.value
            else:
                res.affected_structural_components[s] = ImpactCategory.UNAFFECTED.value
                res.unaffected_components.append(s)

        for m in cls.ALL_KNOWN_MANUFACTURING_PARTS:
            if m in affected_mfg_set:
                res.affected_manufacturing_parts[m] = ImpactCategory.INDIRECTLY_AFFECTED.value
            else:
                res.affected_manufacturing_parts[m] = ImpactCategory.UNAFFECTED.value
                res.unaffected_components.append(m)

        # Determine selective regeneration feasibility
        # Safe when changes are isolated to a single component subtree (e.g. wing only, or metadata only)
        is_metadata_only = not affected_cad_set and not affected_struct_set and not affected_mfg_set
        is_wing_only = affected_cad_set and all("Wing" in c for c in affected_cad_set)
        
        if is_metadata_only:
            res.can_selectively_regenerate = True
            res.selective_scope = ["PHASE_3_REQUIREMENTS"]
        elif is_wing_only:
            res.can_selectively_regenerate = True
            res.selective_scope = ["PHASE_4_CAD", "PHASE_5_STRUCTURE", "PHASE_6D_LASER", "PHASE_6E_PRINT", "PHASE_6F_VALIDATION"]
        else:
            # Fallback to full pipeline orchestration for multi-component or topology changes
            res.can_selectively_regenerate = False
            res.selective_scope = []

        res.requires_user_confirmation = highest_severity in [ChangeSeverity.HIGH, ChangeSeverity.CRITICAL]

        res.summary = {
            "total_requirements_changed": len(changes),
            "highest_severity": res.impact_level,
            "total_cad_affected": len(affected_cad_set),
            "total_structural_affected": len(affected_struct_set),
            "total_manufacturing_affected": len(affected_mfg_set),
            "total_unaffected_items": len(res.unaffected_components),
            "requires_user_confirmation": res.requires_user_confirmation,
        }

        return res
