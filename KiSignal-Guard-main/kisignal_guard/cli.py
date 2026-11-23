"""
Standalone CLI Interface for KiSignal-Guard.
Enables headless PCB Signal Integrity & EMC audits in continuous integration (CI/CD) pipelines
or local terminal environments without requiring the graphical KiCad PCB editor.
"""

import argparse
import sys
import os
from kisignal_guard.core.models import (
    BoardSnapshot,
    TrackSegment,
    PadInfo,
    ViaInfo,
    ZonePolygon,
    Point2D,
    Severity
)
from kisignal_guard.core.engine import InspectionEngine
from kisignal_guard.core.reporter import ReportGenerator


def create_demo_board() -> BoardSnapshot:
    """
    Constructs a realistic high-speed mixed-signal PCB snapshot
    containing intentional design flaws to demonstrate each rule detector:
    1. Return path crossing a split ground plane void.
    2. Decoupling capacitor placed too far from microcontroller VDD pin.
    3. Crosstalk violation: Two parallel high-speed SPI traces with tight gap.
    4. Differential pair length mismatch (skew).
    5. High-power regulator without sufficient thermal vias.
    """
    board = BoardSnapshot(title="Demo_HighSpeed_IoT_Controller.kicad_pcb")

    # 1. Ground Reference Plane with a split/void between x=40 and x=60
    # Left Ground Zone (x: 0 to 40, y: 0 to 50)
    board.zones.append(
        ZonePolygon(
            net_name="GND",
            layer="In1.Cu",
            vertices=[Point2D(0, 0), Point2D(40, 0), Point2D(40, 50), Point2D(0, 50)],
            is_ground=True
        )
    )
    # Right Ground Zone (x: 60 to 100, y: 0 to 50) - leaving a 20mm gap between 40 and 60
    board.zones.append(
        ZonePolygon(
            net_name="GND",
            layer="In1.Cu",
            vertices=[Point2D(60, 0), Point2D(100, 0), Point2D(100, 50), Point2D(60, 50)],
            is_ground=True
        )
    )

    # 2. Critical Clock trace crossing directly over the split plane void!
    board.tracks.append(
        TrackSegment(
            start=Point2D(20, 25),
            end=Point2D(80, 25),
            width_mm=0.2,
            layer="F.Cu",
            net_name="CLK_100MHz"
        )
    )

    # 3. Microcontroller U1 power pin and distant Decoupling Cap C1 (8.5mm away -> Error!)
    board.pads.append(
        PadInfo(
            footprint_ref="U1",
            pad_number="1",
            net_name="+3V3",
            position=Point2D(20.0, 10.0),
            layer="F.Cu",
            is_power=True
        )
    )
    board.pads.append(
        PadInfo(
            footprint_ref="C1",
            pad_number="1",
            net_name="+3V3",
            position=Point2D(28.5, 10.0),  # 8.5 mm away
            layer="F.Cu",
            is_power=True
        )
    )

    # 4. Crosstalk Hazard: Parallel SPI traces running 15mm alongside each other with 0.2mm gap (3W violation)
    board.tracks.append(
        TrackSegment(
            start=Point2D(10, 35),
            end=Point2D(26, 35),
            width_mm=0.25,
            layer="F.Cu",
            net_name="SPI_MOSI"
        )
    )
    board.tracks.append(
        TrackSegment(
            start=Point2D(10, 35.35),  # 0.35 mm center-to-center -> edge-to-edge = 0.1 mm (< 2 * 0.25 = 0.5 mm)
            end=Point2D(26, 35.35),
            width_mm=0.25,
            layer="F.Cu",
            net_name="SPI_SCK"
        )
    )

    # 5. Differential Pair with severe skew (USB_DP = 25 mm, USB_DN = 21 mm -> Delta: 4.0 mm)
    board.tracks.append(
        TrackSegment(
            start=Point2D(5, 5),
            end=Point2D(30, 5),
            width_mm=0.2,
            layer="F.Cu",
            net_name="USB_D_P"
        )
    )
    board.tracks.append(
        TrackSegment(
            start=Point2D(5, 6),
            end=Point2D(26, 6),
            width_mm=0.2,
            layer="F.Cu",
            net_name="USB_D_N"
        )
    )

    # 6. Power Regulator U2 with thermal exposed pad but only 1 thermal via (Needs >= 4)
    board.pads.append(
        PadInfo(
            footprint_ref="U2",
            pad_number="EP",
            net_name="GND",
            position=Point2D(80.0, 15.0),
            layer="F.Cu",
            is_ground=True
        )
    )
    board.vias.append(
        ViaInfo(
            position=Point2D(80.5, 15.2),
            drill_mm=0.3,
            pad_diameter_mm=0.6,
            net_name="GND",
            is_ground=True
        )
    )

    return board


def main():
    parser = argparse.ArgumentParser(
        prog="kisignal-guard",
        description="KiSignal-Guard: Automated PCB Signal Integrity & EMC Linter for KiCad 9"
    )
    parser.add_argument("--demo", action="store_true", help="Run audit on synthetic benchmark board with intentional SI/EMC defects")
    parser.add_argument("--kicad-pcb", type=str, help="Path to .kicad_pcb board file")
    parser.add_argument("--output-json", type=str, help="Export diagnostic results to JSON file")
    parser.add_argument("--output-html", type=str, help="Export diagnostic results to interactive HTML report")
    parser.add_argument("--output-md", type=str, help="Export diagnostic results to Markdown report")
    parser.add_argument("--min-score", type=float, default=70.0, help="Minimum acceptable SI score for CI exit code (default: 70.0)")

    args = parser.parse_args()

    print("=" * 70)
    print("   KiSignal-Guard: High-Speed SI, EMC & PDN Verification Engine")
    print("   Compatible with KiCad 9 | FOSSEE eSim Internship Project")
    print("=" * 70)

    if args.demo:
        print("[*] Running demonstration audit on synthetic benchmark board...")
        board = create_demo_board()
    elif args.kicad_pcb:
        from kisignal_guard.core.adapter import PcbnewAdapter
        if not PcbnewAdapter.is_kicad_available():
            print("[!] Error: pcbnew module is not installed in this Python environment.")
            print("[!] Please run inside KiCad 9's Python or use '--demo' mode.")
            sys.exit(1)
        import pcbnew
        loaded_board = pcbnew.LoadBoard(args.kicad_pcb)
        board = PcbnewAdapter.load_from_pcbnew(loaded_board)
    else:
        print("[*] No input specified. Running in demo mode by default...")
        board = create_demo_board()

    # Execute Engine
    engine = InspectionEngine()
    result = engine.run(board)

    # Print Terminal Report
    print(f"\n[+] Board: {result.board_title}")
    print(f"[+] Execution Time: {result.execution_time_ms:.2f} ms | Rules Run: {result.rules_executed}")
    print(f"[+] Signal Integrity Score: {result.signal_integrity_score:.1f}%")
    print(f"[+] Violations Detected: {len(result.violations)} (Errors: {result.error_count}, Warnings: {result.warning_count}, Info: {result.info_count})\n")

    print("-" * 70)
    print(f"{'SEVERITY':<10} {'RULE ID':<10} {'NET NAME':<22} {'DIAGNOSTIC ISSUE'}")
    print("-" * 70)
    for v in result.violations:
        color_tag = "[ERR]" if v.severity == Severity.ERROR else ("[WARN]" if v.severity == Severity.WARNING else "[INFO]")
        print(f"{color_tag:<10} {v.rule_id:<10} {v.net_name[:20]:<22} {v.message[:60]}...")
        print(f"  └─> Fix: {v.recommendation}\n")

    # Exports
    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            f.write(ReportGenerator.to_json(result))
        print(f"[✓] Saved JSON report to: {args.output_json}")

    if args.output_html:
        with open(args.output_html, "w", encoding="utf-8") as f:
            f.write(ReportGenerator.to_html(result))
        print(f"[✓] Saved HTML report to: {args.output_html}")

    if args.output_md:
        with open(args.output_md, "w", encoding="utf-8") as f:
            f.write(ReportGenerator.to_markdown(result))
        print(f"[✓] Saved Markdown report to: {args.output_md}")

    print("=" * 70)
    if result.signal_integrity_score < args.min_score:
        print(f"[!] FAILED: SI Score ({result.signal_integrity_score:.1f}%) is below minimum threshold ({args.min_score:.1f}%).")
        sys.exit(1)
    else:
        print(f"[✓] PASSED: SI Score ({result.signal_integrity_score:.1f}%) meets threshold.")
        sys.exit(0)


if __name__ == "__main__":
    main()
