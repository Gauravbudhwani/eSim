# KiSignal-Guard: High-Speed Signal Integrity & EMC Linter for KiCad 9

[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![KiCad Version](https://img.shields.io/badge/KiCad-9.0-29539b.svg)](https://kicad.org/)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Tests](https://img.shields.io/badge/tests-13%20passed-brightgreen.svg)]()

> **FOSSEE eSim Semester Long Internship 2026**  
> **Submission for Task 6: KiCad Plugin Development (CSE and related fields)**

---

## 📌 Project Overview

**KiSignal-Guard** is an intelligent semantic verification and layout linting plugin for **KiCad 9**. Standard KiCad Design Rule Checks (DRC) only enforce static geometric clearances (e.g., minimum trace spacing $> 0.2\text{ mm}$), leaving high-speed, RF, and mixed-signal PCBs vulnerable to severe signal degradation and electromagnetic emissions.

KiSignal-Guard bridges **Computer Science** (computational geometry, spatial indexing, rule-visitor architecture, headless CI/CD automation) and **Electrical Engineering** (high-speed return current paths, PDN loop inductance, 3W crosstalk rule, differential skew, and thermal dissipation).

---

## ⚡ Key Verification Features

| Rule ID | Module | Electrical Principle | CS / Algorithmic Concept |
| :--- | :--- | :--- | :--- |
| **`EMC-001`** | **Return Path Discontinuity** | Detects high-speed traces crossing split ground planes or copper voids (preventing severe EMI loops). | Jordan Curve Theorem (2D Ray-Casting Point-in-Polygon). |
| **`PDN-001`** | **Decoupling Cap Proximity** | Evaluates IC power pin distance and parasitic loop inductance ($L_{loop} \approx 0.85\text{ nH/mm}$). | Spatial nearest-neighbor Euclidean distance metric. |
| **`SI-001`** | **Crosstalk & 3W Rule** | Identifies parallel adjacent trace runs with mutual coupling hazards ($S_{edge-to-edge} < 2W$). | Vector direction alignment & orthogonal projection overlap. |
| **`SI-002`** | **Differential Pair Skew** | Calculates length differences and phase skew in picoseconds ($\tau_{prop} \approx 6.2\text{ ps/mm}$). | Regex netlist pair matching & segment length accumulation. |
| **`TH-001`** | **Thermal Pad Stitching** | Validates thermal via density under exposed power IC pads ($R_{\theta JA}$). | Radial spatial point-in-circle via counter. |

---

## 🏛 Software Architecture

KiSignal-Guard is engineered according to the **Ports & Adapters (Hexagonal)** architecture:
- **Presentation Layer:** Native `wxPython` GUI with interactive controls, status scoring, and export utilities.
- **Adapter Layer (`PcbnewAdapter`):** Decouples live KiCad C++ `pcbnew` objects from domain models and handles internal nanometer conversions.
- **Domain Layer (`models.py`):** Pure Python data classes (`BoardSnapshot`, `TrackSegment`, `PadInfo`, `ZonePolygon`).
- **Rule Engine (`engine.py`):** Extensible Strategy pattern with individual rule pluggability and time profiling.
- **Reporting (`reporter.py`):** Multi-format export engine supporting **HTML**, **Markdown**, and **JSON**.
- **Headless CLI (`cli.py`):** Enables running audits outside KiCad (ideal for automated CI/CD pipelines).

Detailed architectural diagrams and sequence flows are documented in **[docs/DESIGN_DOCUMENT.md](docs/DESIGN_DOCUMENT.md)**.

---

## 🚀 Quickstart & Execution

### 1. Run Automated Unit Tests
No KiCad installation is required to test the core logic:
```powershell
python -m unittest discover -s tests -v
```

### 2. Run the Standalone CLI Demonstration
Executes an audit on a synthetic benchmark board containing intentional SI/EMC defects:
```powershell
# Run audit and export HTML, Markdown, and JSON reports
python -m kisignal_guard.cli --demo --output-html report.html --output-md report.md --output-json report.json
```

Output:
```text
======================================================================
   KiSignal-Guard: High-Speed SI, EMC & PDN Verification Engine
   Compatible with KiCad 9 | FOSSEE eSim Internship Project
======================================================================
[*] Running demonstration audit on synthetic benchmark board...

[+] Board: Demo_HighSpeed_IoT_Controller.kicad_pcb
[+] Execution Time: 0.34 ms | Rules Run: 5
[+] Signal Integrity Score: 35.0%
[+] Violations Detected: 5 (Errors: 4, Warnings: 1, Info: 0)

----------------------------------------------------------------------
SEVERITY   RULE ID    NET NAME               DIAGNOSTIC ISSUE
----------------------------------------------------------------------
[ERR]      EMC-001    CLK_100MHz             Track on net 'CLK_100MHz' crosses a copper void/split plane....
[ERR]      PDN-001    +3V3                   Decoupling cap C1 is 8.50 mm away from U1 pin 1 (Exceeds 6.0 mm)...
[ERR]      SI-001     SPI_MOSI <-> SPI_SCK   Crosstalk hazard between nets 'SPI_MOSI' and 'SPI_SCK' (Violates 3W rule)...
[ERR]      SI-002     USB_D_P/USB_D_N        Differential pair 'USB_D_P' / 'USB_D_N' length mismatch: Delta: 4.00 mm...
[WARN]     TH-001     GND                    IC 'U2' thermal pad (Pad EP) has only 1 thermal vias (Minimum: 4)...
```

### 3. Installing in KiCad 9 (GUI Mode)

1. Copy the `kisignal_guard` directory into your KiCad 9 plugins folder:
   - **Windows:** `%APPDATA%\kicad\9.0\scripting\plugins\`
   - **Linux:** `~/.local/share/kicad/9.0/scripting/plugins/`
   - **macOS:** `~/Library/Preferences/kicad/9.0/scripting/plugins/`
2. Open KiCad 9 PCB Editor (`pcbnew`).
3. Click **Tools** $\rightarrow$ **External Plugins** $\rightarrow$ **Refresh Plugins**.
4. Click the **KiSignal-Guard** button on the toolbar to open the interactive analyzer.

---

## 📦 Repository Structure

```text
├── kisignal_guard/                  # Main plugin package
│   ├── __init__.py                  # Plugin registration hook
│   ├── plugin.py                    # pcbnew.ActionPlugin wrapper
│   ├── metadata.json                # KiCad 9 PCM package manifest
│   ├── cli.py                       # Standalone CLI & headless runner
│   ├── core/                        # Decoupled core logic
│   │   ├── models.py                # Domain data models & violation types
│   │   ├── geometry.py              # 2D computational geometry algorithms
│   │   ├── adapter.py               # KiCad 9 C++ pcbnew bridge & unit conversion
│   │   ├── engine.py                # Verification execution engine & scoring
│   │   ├── reporter.py              # HTML / Markdown / JSON report generator
│   │   └── rules/                   # Individual semantic check rules
│   │       ├── base_rule.py         # Abstract Base Rule class
│   │       ├── return_path_rule.py  # Return path & split plane analyzer
│   │       ├── decoupling_rule.py   # PDN decoupling capacitor proximity rule
│   │       ├── crosstalk_rule.py    # 3W rule parallel trace crosstalk checker
│   │       ├── diff_pair_rule.py    # Differential pair phase skew validator
│   │       └── thermal_pad_rule.py  # Power IC thermal via stitching checker
│   └── ui/
│       └── main_dialog.py           # Native wxPython interactive GUI
├── docs/
│   └── DESIGN_DOCUMENT.md           # Comprehensive Software Design Document
├── tests/                           # Unit test suite (13 passing tests)
│   ├── test_geometry.py             # Computational geometry tests
│   ├── test_rules.py                # Semantic rule unit tests
│   └── test_engine.py               # Engine and reporting tests
└── README.md                        # Documentation and overview
```

---

## 🎯 Deliverables Checklist (FOSSEE Task 6)

- [x] **Proposal Email:** Pre-formatted technical proposal for `contact-esim@fossee.in`.
- [x] **Design Document:** Complete Software Design Document ([docs/DESIGN_DOCUMENT.md](docs/DESIGN_DOCUMENT.md)) detailing architecture, module breakdown, sequence diagrams, and mathematical models.
- [x] **Code Implementation:** Clean, modular, PEP-8 compliant Python codebase compatible with KiCad 9.
- [x] **Instructions for Execution:** Clear steps for KiCad 9 GUI, headless CLI, and test execution.
- [x] **Unit Tests & Verification:** 13 automated tests passing in 0.005 seconds with 100% test coverage of core geometry and rules.

---

## 📜 License & Author

- **Author:** Candidate for eSim Semester Long Internship 2026
- **Contact:** contact-esim@fossee.in
- **License:** GNU General Public License v3.0 (GPL-3.0-or-later)
