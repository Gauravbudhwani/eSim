# KiSignal-Guard: Presentation & Video Demo Guide (5–10 Minutes)
**FOSSEE eSim Semester Long Internship 2026 — Task 6**

This guide provides a slide-by-slide structure, talking points, and a live demonstration script for your presentation video.

---

## 📽️ Slide-by-Slide Presentation Structure

### Slide 1: Title & Introduction (0:00 - 0:45)
- **Title:** KiSignal-Guard: Intelligent Signal Integrity, EMC & PDN Analyzer for KiCad 9
- **Subtitle:** FOSSEE eSim Semester Long Internship 2026 — Task 6 Submission
- **Presenter:** [Your Name], [Your University / Department]
- **Key Talking Points:**
  - Introduce yourself and the objective of Task 6: proposing and implementing a modular, extensible KiCad 9 plugin that unites Computer Science and Electronics.
  - State the project title: **KiSignal-Guard**.

---

### Slide 2: Motivation & The Engineering Gap (0:45 - 2:00)
- **Title:** Why Standard KiCad DRC Is Not Enough
- **Key Talking Points:**
  - Standard Design Rule Checks (DRC) in KiCad 9 test only physical clearances (e.g., copper clearance $\ge 0.2\text{ mm}$, minimum drill size).
  - High-speed digital and mixed-signal PCBs fail not from physical shorts, but from **semantic electromagnetic and signal integrity flaws**:
    1. *Return Path Discontinuities:* High-speed clock/SPI lines crossing split ground planes, creating severe EMI radiation and ground bounce.
    2. *PDN Decoupling Inductance:* Decoupling capacitors placed too far from IC power pins, adding parasitic trace inductance ($\approx 0.85\text{ nH/mm}$) that destabilizes power rails.
    3. *Crosstalk (3W Rule):* Parallel signal traces coupling noise into adjacent nets.
    4. *Differential Pair Skew:* Length mismatches causing phase skew.
    5. *Thermal Bottlenecks:* Power ICs lacking thermal via arrays.

---

### Slide 3: The Solution — KiSignal-Guard (2:00 - 3:15)
- **Title:** Blending Computer Science and Electrical Engineering
- **Key Talking Points:**
  - **Electronics Foundations:**
    - High-frequency return current path analysis ($Z = R + j\omega L$).
    - Parasitic loop inductance calculation ($V = L \cdot \frac{di}{dt}$).
    - Empirical 3W crosstalk rule ($S \ge 2W$).
    - Differential propagation delay and phase skew ($\tau_{prop} \approx 6.2\text{ ps/mm}$ in FR4).
  - **Computer Science Foundations:**
    - Computational geometry algorithms: 2D Ray-Casting (Jordan curve theorem) for copper plane enclosure, segment-segment distance, vector projection for parallel overlap.
    - Software Architecture: Ports-and-Adapters (Hexagonal) pattern, Strategy/Visitor pattern for extensible rules.
    - Dual execution modes: Interactive wxPython GUI inside KiCad 9 and a headless CLI runner for automated CI/CD pipelines.

---

### Slide 4: System Architecture (3:15 - 4:30)
- **Title:** Modular & Extensible Software Architecture
- **Key Talking Points:**
  - Refer to the architectural diagram from the Design Document:
    - *Presentation Layer:* `ActionPlugin` toolbar hook and wxPython dialog (`ui/main_dialog.py`).
    - *Adapter Layer:* `PcbnewAdapter` converts KiCad 9 nanometer coordinates ($10^6\text{ nm} = 1\text{ mm}$) to clean Python domain models (`BoardSnapshot`).
    - *Core Engine:* `InspectionEngine` runs enabled rules independently and calculates a normalized 0–100% Signal Integrity Score.
    - *Reporting Layer:* Outputs interactive HTML, Markdown, and JSON reports.

---

### Slide 5: Live Demonstration (4:30 - 7:30)
*(Screen recording of the CLI or KiCad GUI)*
- **Demo Step 1: Unit Test Suite**
  - Run `python -m unittest discover -s tests -v` in the terminal.
  - Highlight that 13 unit tests pass in 0.005 seconds, demonstrating robust code quality and independent testability.
- **Demo Step 2: Running the Inspection Audit**
  - Run `python -m kisignal_guard.cli --demo --output-html report.html --output-md report.md --output-json report.json`.
  - Show the terminal output diagnosing the 5 benchmark flaws:
    - Clock line crossing the split ground plane.
    - Bypass capacitor placed 8.5 mm away from microcontroller pin.
    - SPI traces violating the 3W rule.
    - USB differential pair with 4.0 mm length mismatch.
    - IC thermal pad with only 1 via.
- **Demo Step 3: Interactive HTML Report**
  - Open `report.html` in a web browser.
  - Show the score badge (35.0%), severity cards, diagnostic descriptions, and engineering remediation advice.

---

### Slide 6: Roadmap for Internship Period & Conclusion (7:30 - 8:30)
- **Title:** Internship Expansion Roadmap
- **Key Talking Points:**
  - Automated layout healing: Automatic thermal via array generation and ground return via stitching.
  - 2D FEM / Boundary Element impedance solver for arbitrary polygon plane return currents.
  - Direct cross-probing between FOSSEE eSim schematics and KiCad layouts.
  - Thank the FOSSEE team and express enthusiasm for contributing to eSim during the internship.

---

## 🎙️ Recording Tips
1. **Screen Resolution:** Record at 1920x1080 (1080p) for crisp text in terminal and browser.
2. **Audio:** Use a clear headset or dedicated microphone; keep background noise minimal.
3. **Pacing:** Speak steadily and highlight how each feature solves a real-world electronics problem using computer science principles.
