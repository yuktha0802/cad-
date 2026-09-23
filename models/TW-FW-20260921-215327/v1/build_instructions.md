# PROTOTYPE BUILD & ASSEMBLY INSTRUCTIONS
**Aircraft ID:** TW-FW-20260921-215327 | **Revision:** v1 | **Package Version:** 1.0.0
**Prototype Status:** READY

---

## 1. Material Schedule & Stock Requirements
* **Aeroply_3mm (3.0 mm)**: 14 parts across 1 sheet(s) [900 × 600 mm]
* **Balsa_3mm (3.0 mm)**: 33 parts across 1 sheet(s) [900 × 600 mm]
* **PETG_OR_PLA (0.0 mm)**: 1 parts across 0 sheet(s) [220 × 220 × 250 mm build volume]

---

## 2. Physical Subassembly Breakdown
### MainWing_Left (16 parts)
* Parts: `SPAR-L-MAIN`, `SPAR-L-REAR`, `RIB-L-000`, `RIB-L-001`, `RIB-L-002`, `RIB-L-003`, `RIB-L-004`, `RIB-L-005` and 8 more...
### MainWing_Right (16 parts)
* Parts: `SPAR-R-MAIN`, `SPAR-R-REAR`, `RIB-R-000`, `RIB-R-001`, `RIB-R-002`, `RIB-R-003`, `RIB-R-004`, `RIB-R-005` and 8 more...
### Fuselage (12 parts)
* Parts: `FMR-000`, `FMR-001`, `FMR-002`, `FMR-003`, `FMR-004`, `FMR-005`, `LONG-UPPER-L`, `LONG-UPPER-R` and 4 more...
### VerticalTail (4 parts)
* Parts: `VT-SPAR-001`, `VT-RIB-000`, `VT-RIB-001`, `VT-RIB-002`

---

## 3. Deterministic Assembly Sequence
### Step 01: Fuselage Primary Framework Assembly
**Subassembly:** Fuselage
Slot fuselage formers into upper and lower longerons and secure the forward propulsion firewall.
* **Components:** FMR-000, FMR-001, FMR-002, FMR-003, FMR-004, FMR-005, LONG-UPPER-L, LONG-UPPER-R, LONG-LOWER-L, LONG-LOWER-R, FIREWALL-001, WING-ATTACH-001
* **Joint Interfaces:** JNT_FMR_000_LONG-UPPER-L, JNT_FMR_000_LONG-UPPER-R, JNT_FMR_000_LONG-LOWER-L, JNT_FMR_000_LONG-LOWER-R, JNT_FMR_001_LONG-UPPER-L, JNT_FMR_001_LONG-UPPER-R, JNT_FMR_001_LONG-LOWER-L, JNT_FMR_001_LONG-LOWER-R, JNT_FMR_002_LONG-UPPER-L, JNT_FMR_002_LONG-UPPER-R, JNT_FMR_002_LONG-LOWER-L, JNT_FMR_002_LONG-LOWER-R, JNT_FMR_003_LONG-UPPER-L, JNT_FMR_003_LONG-UPPER-R, JNT_FMR_003_LONG-LOWER-L, JNT_FMR_003_LONG-LOWER-R, JNT_FMR_004_LONG-UPPER-L, JNT_FMR_004_LONG-UPPER-R, JNT_FMR_004_LONG-LOWER-L, JNT_FMR_004_LONG-LOWER-R
* **Output Assembly:** Fuselage_Subassembly

### Step 02: Left Wing Spar and Rib Assembly
**Subassembly:** MainWing_Left
Slot wing ribs (RIB-L-000 to RIB-L-009) onto the Main and Rear Wing Spars.
* **Components:** SPAR-L-MAIN, SPAR-L-REAR, RIB-L-000, RIB-L-001, RIB-L-002, RIB-L-003, RIB-L-004, RIB-L-005, RIB-L-006, RIB-L-007, RIB-L-008, RIB-L-009, HT-SPAR-L-001, HT-RIB-L-000, HT-RIB-L-001, HT-RIB-L-002
* **Joint Interfaces:** JNT_RIB_L_000_SPAR_MAIN, JNT_RIB_L_000_SPAR_REAR, JNT_RIB_L_001_SPAR_MAIN, JNT_RIB_L_001_SPAR_REAR, JNT_RIB_L_002_SPAR_MAIN, JNT_RIB_L_002_SPAR_REAR, JNT_RIB_L_003_SPAR_MAIN, JNT_RIB_L_003_SPAR_REAR, JNT_RIB_L_004_SPAR_MAIN, JNT_RIB_L_004_SPAR_REAR, JNT_RIB_L_005_SPAR_MAIN, JNT_RIB_L_005_SPAR_REAR, JNT_RIB_L_006_SPAR_MAIN, JNT_RIB_L_006_SPAR_REAR, JNT_RIB_L_007_SPAR_MAIN, JNT_RIB_L_007_SPAR_REAR, JNT_RIB_L_008_SPAR_MAIN, JNT_RIB_L_008_SPAR_REAR, JNT_RIB_L_009_SPAR_MAIN, JNT_RIB_L_009_SPAR_REAR, JNT_HT_RIB_L_000_SPAR, JNT_HT_RIB_L_001_SPAR, JNT_HT_RIB_L_002_SPAR
* **Output Assembly:** MainWing_Left_Subassembly

### Step 03: Right Wing Spar and Rib Assembly
**Subassembly:** MainWing_Right
Slot wing ribs (RIB-R-000 to RIB-R-009) onto the Main and Rear Wing Spars.
* **Components:** SPAR-R-MAIN, SPAR-R-REAR, RIB-R-000, RIB-R-001, RIB-R-002, RIB-R-003, RIB-R-004, RIB-R-005, RIB-R-006, RIB-R-007, RIB-R-008, RIB-R-009, HT-SPAR-R-001, HT-RIB-R-000, HT-RIB-R-001, HT-RIB-R-002
* **Joint Interfaces:** JNT_RIB_R_000_SPAR_MAIN, JNT_RIB_R_000_SPAR_REAR, JNT_RIB_R_001_SPAR_MAIN, JNT_RIB_R_001_SPAR_REAR, JNT_RIB_R_002_SPAR_MAIN, JNT_RIB_R_002_SPAR_REAR, JNT_RIB_R_003_SPAR_MAIN, JNT_RIB_R_003_SPAR_REAR, JNT_RIB_R_004_SPAR_MAIN, JNT_RIB_R_004_SPAR_REAR, JNT_RIB_R_005_SPAR_MAIN, JNT_RIB_R_005_SPAR_REAR, JNT_RIB_R_006_SPAR_MAIN, JNT_RIB_R_006_SPAR_REAR, JNT_RIB_R_007_SPAR_MAIN, JNT_RIB_R_007_SPAR_REAR, JNT_RIB_R_008_SPAR_MAIN, JNT_RIB_R_008_SPAR_REAR, JNT_RIB_R_009_SPAR_MAIN, JNT_RIB_R_009_SPAR_REAR, JNT_HT_RIB_R_000_SPAR, JNT_HT_RIB_R_001_SPAR, JNT_HT_RIB_R_002_SPAR
* **Output Assembly:** MainWing_Right_Subassembly

### Step 04: Tail Empennage Assembly
**Subassembly:** Tail
Assemble horizontal stabilizer spars/ribs and vertical stabilizer framework.
* **Components:** VT-SPAR-001, VT-RIB-000, VT-RIB-001, VT-RIB-002
* **Joint Interfaces:** JNT_VT_RIB_000_SPAR, JNT_VT_RIB_001_SPAR, JNT_VT_RIB_002_SPAR
* **Output Assembly:** Tail_Subassembly

### Step 05: Final Airframe Integration & Wing Attachment (Depends on Step 1, 2, 3, 4)
**Subassembly:** Airframe
Mount left and right wings to the fuselage using the 3D-printed attachment block and align tail empennage.
* **Components:** 
* **Output Assembly:** Complete_Prototype_Airframe

---

## 4. Build Integrity & Validation Summary
* **Engineering Review:** PASS
* **Manufacturing Validation:** PASS
* **Build Package Integrity:** READY
* **Total Physical Parts:** 48
* **Total Structural Joints:** 69