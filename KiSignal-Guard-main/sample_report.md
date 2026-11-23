# KiSignal-Guard Verification Report: Demo_HighSpeed_IoT_Controller.kicad_pcb

**Overall Signal Integrity Score:** `35.0%` (FAILED)  
**Execution Time:** `0.34 ms` | **Rules Executed:** `5`  

## Summary

| Metric | Count |
| :--- | :--- |
| Critical Errors | 4 |
| Warnings | 1 |
| Info Notes | 0 |
| **Total Violations** | **5** |

## Detailed Violations & Actionable Recommendations

### 1. 🔴 [EMC-001] Return Path Discontinuity & Split Plane Crossing
- **Net:** `CLK_100MHz`
- **Category:** Return Path & EMC
- **Severity:** `ERROR`
- **Location:** `X=40.00 mm, Y=25.00 mm`
- **Issue:** Track on net 'CLK_100MHz' crosses a copper void/split plane. 1/4 sample points lack reference ground.
- **Actionable Fix:** Reroute net 'CLK_100MHz' over a solid, unbroken ground plane or add a stitching capacitor / ground bridge across the plane split.

### 2. 🔴 [PDN-001] Decoupling Capacitor Proximity & Loop Inductance
- **Net:** `+3V3`
- **Category:** PDN & Decoupling
- **Severity:** `ERROR`
- **Location:** `X=20.00 mm, Y=10.00 mm`
- **Issue:** Decoupling cap C1 is 8.50 mm away from U1 pin 1 (Exceeds 6.0 mm limit). Estimated parasitic loop inductance: ~14.4 nH.
- **Actionable Fix:** Move capacitor C1 closer (< 3.5 mm) to U1 pin 1 to minimize PDN impedance.

### 3. 🔴 [SI-001] Crosstalk & 3W Rule Compliance
- **Net:** `SPI_MOSI <-> SPI_SCK`
- **Category:** Crosstalk & Isolation
- **Severity:** `ERROR`
- **Location:** `X=18.00 mm, Y=35.17 mm`
- **Issue:** Crosstalk hazard between nets 'SPI_MOSI' and 'SPI_SCK'. Parallel coupling run is 16.00 mm with spacing 0.10 mm (Violates 3W rule: required gap >= 0.50 mm).
- **Actionable Fix:** Increase spacing between 'SPI_MOSI' and 'SPI_SCK' to at least 0.50 mm or interpose an in-between ground shield trace.

### 4. 🔴 [SI-002] Differential Pair Skew & Length Matching
- **Net:** `USB_D_P/USB_D_N`
- **Category:** Differential Pair
- **Severity:** `ERROR`
- **Location:** `X=17.50 mm, Y=5.00 mm`
- **Issue:** Differential pair 'USB_D_P' / 'USB_D_N' has severe length mismatch: 25.00 mm vs 21.00 mm (Delta: 4.00 mm, Skew: ~24.8 ps).
- **Actionable Fix:** Add serpentine / meander length tuning to the shorter net to balance within 0.5 mm (< 3.1 ps).

### 5. 🟡 [TH-001] Power IC Thermal Via Stitching
- **Net:** `GND`
- **Category:** Thermal Dissipation
- **Severity:** `WARNING`
- **Location:** `X=80.00 mm, Y=15.00 mm`
- **Issue:** IC 'U2' thermal pad (Pad EP) has only 1 thermal vias within 2.5 mm (Minimum required: 4).
- **Actionable Fix:** Add a 4-via grid array (drill 0.3mm) connected to GND under 'U2' to ensure adequate heat sinking.
