"""
Report Generation Module for KiSignal-Guard.
Exports inspection results to Markdown, JSON, and rich HTML formats.
"""

import json
from typing import Dict, Any
from kisignal_guard.core.models import InspectionResult, Severity


class ReportGenerator:
    """Generates structured documentation and export artifacts."""

    @staticmethod
    def to_json(result: InspectionResult, indent: int = 2) -> str:
        data = {
            "board_title": result.board_title,
            "signal_integrity_score": result.signal_integrity_score,
            "rules_executed": result.rules_executed,
            "execution_time_ms": result.execution_time_ms,
            "summary": {
                "errors": result.error_count,
                "warnings": result.warning_count,
                "info": result.info_count,
                "total_violations": len(result.violations)
            },
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "rule_name": v.rule_name,
                    "category": v.category.value,
                    "severity": v.severity.value,
                    "net_name": v.net_name,
                    "location_mm": {"x": round(v.location.x, 3), "y": round(v.location.y, 3)},
                    "message": v.message,
                    "recommendation": v.recommendation,
                    "metrics": v.metrics
                }
                for v in result.violations
            ]
        }
        return json.dumps(data, indent=indent)

    @staticmethod
    def to_markdown(result: InspectionResult) -> str:
        score = result.signal_integrity_score
        status = "PASSED" if score >= 85 else ("WARNING" if score >= 60 else "FAILED")

        lines = [
            f"# KiSignal-Guard Verification Report: {result.board_title}",
            "",
            f"**Overall Signal Integrity Score:** `{score:.1f}%` ({status})  ",
            f"**Execution Time:** `{result.execution_time_ms:.2f} ms` | **Rules Executed:** `{result.rules_executed}`  ",
            "",
            "## Summary",
            "",
            f"| Metric | Count |",
            f"| :--- | :--- |",
            f"| Critical Errors | {result.error_count} |",
            f"| Warnings | {result.warning_count} |",
            f"| Info Notes | {result.info_count} |",
            f"| **Total Violations** | **{len(result.violations)}** |",
            "",
            "## Detailed Violations & Actionable Recommendations",
            ""
        ]

        if not result.violations:
            lines.append("No signal integrity or EMC violations detected. The layout passes all checks!")
        else:
            for idx, v in enumerate(result.violations, 1):
                icon = "🔴" if v.severity == Severity.ERROR else ("🟡" if v.severity == Severity.WARNING else "🔵")
                lines.extend([
                    f"### {idx}. {icon} [{v.rule_id}] {v.rule_name}",
                    f"- **Net:** `{v.net_name}`",
                    f"- **Category:** {v.category.value}",
                    f"- **Severity:** `{v.severity.value}`",
                    f"- **Location:** `X={v.location.x:.2f} mm, Y={v.location.y:.2f} mm`",
                    f"- **Issue:** {v.message}",
                    f"- **Actionable Fix:** {v.recommendation}",
                    ""
                ])

        return "\n".join(lines)

    @staticmethod
    def to_html(result: InspectionResult) -> str:
        score = result.signal_integrity_score
        score_color = "#10b981" if score >= 85 else ("#f59e0b" if score >= 60 else "#ef4444")

        rows = []
        for v in result.violations:
            badge_class = "badge-error" if v.severity == Severity.ERROR else ("badge-warning" if v.severity == Severity.WARNING else "badge-info")
            rows.append(f"""
            <tr>
                <td><span class="badge {badge_class}">{v.severity.value}</span></td>
                <td><code>{v.rule_id}</code></td>
                <td>{v.category.value}</td>
                <td><strong>{v.net_name}</strong></td>
                <td>({v.location.x:.2f}, {v.location.y:.2f})</td>
                <td>{v.message}</td>
                <td class="rec">{v.recommendation}</td>
            </tr>
            """)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>KiSignal-Guard Report - {result.board_title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 30px; background: #f8fafc; color: #1e293b; }}
        .header {{ background: #ffffff; padding: 24px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 24px; }}
        .score-circle {{ font-size: 36px; font-weight: bold; color: {score_color}; }}
        .stats {{ display: flex; gap: 20px; margin-top: 15px; }}
        .stat-box {{ background: #f1f5f9; padding: 12px 20px; border-radius: 6px; }}
        table {{ width: 100%; border-collapse: collapse; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid #e2e8f0; font-size: 14px; }}
        th {{ background: #0f172a; color: #ffffff; font-weight: 600; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 11px; }}
        .badge-error {{ background: #fee2e2; color: #b91c1c; }}
        .badge-warning {{ background: #fef3c7; color: #b45309; }}
        .badge-info {{ background: #e0f2fe; color: #0369a1; }}
        .rec {{ color: #047857; font-weight: 500; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>KiSignal-Guard SI & EMC Audit</h1>
        <p><strong>Board:</strong> {result.board_title} | <strong>Execution Time:</strong> {result.execution_time_ms:.1f} ms</p>
        <div class="score-circle">{score:.1f}% Signal Integrity Score</div>
        <div class="stats">
            <div class="stat-box"><strong>Errors:</strong> {result.error_count}</div>
            <div class="stat-box"><strong>Warnings:</strong> {result.warning_count}</div>
            <div class="stat-box"><strong>Info:</strong> {result.info_count}</div>
            <div class="stat-box"><strong>Rules Run:</strong> {result.rules_executed}</div>
        </div>
    </div>
    <table>
        <thead>
            <tr>
                <th>Severity</th>
                <th>Rule</th>
                <th>Category</th>
                <th>Net</th>
                <th>Location (mm)</th>
                <th>Diagnostic</th>
                <th>Actionable Remediation</th>
            </tr>
        </thead>
        <tbody>
            {"".join(rows) if rows else "<tr><td colspan='7'>All design rules passed! Excellent layout quality.</td></tr>"}
        </tbody>
    </table>
</body>
</html>
"""
        return html
