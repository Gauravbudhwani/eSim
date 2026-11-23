"""
wxPython User Interface for KiSignal-Guard.
Displays interactive inspection controls, diagnostic results grid, and export utilities.
Compatible with KiCad 9 wxPython environment.
"""

import os
from typing import Optional, List
from kisignal_guard.core.models import BoardSnapshot, InspectionResult, Severity, Violation
from kisignal_guard.core.engine import InspectionEngine
from kisignal_guard.core.reporter import ReportGenerator


def get_wx():
    """Dynamically imports wx to allow headless execution when wx is missing."""
    try:
        import wx
        return wx
    except ImportError:
        return None


class KiSignalGuardDialog:
    """
    Dialog wrapper for KiSignal-Guard.
    If wx is installed, it instantiates wx.Dialog; otherwise provides mock fallback.
    """

    def __init__(self, parent=None, board_snapshot: Optional[BoardSnapshot] = None):
        self.wx = get_wx()
        if not self.wx:
            raise RuntimeError("wxPython is required for GUI mode. Use CLI mode for headless environments.")

        self.board_snapshot = board_snapshot
        self.engine = InspectionEngine()
        self.current_result: Optional[InspectionResult] = None

        # Create wx Dialog
        self.frame = self.wx.Dialog(
            parent,
            title="KiSignal-Guard — High-Speed SI & EMC Analyzer for KiCad 9",
            size=(880, 650),
            style=self.wx.DEFAULT_DIALOG_STYLE | self.wx.RESIZE_BORDER
        )
        self._init_ui()

    def _init_ui(self):
        wx = self.wx
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header Banner
        header_panel = wx.Panel(self.frame)
        header_panel.SetBackgroundColour(wx.Colour(24, 32, 47))
        h_sizer = wx.BoxSizer(wx.VERTICAL)

        title_lbl = wx.StaticText(header_panel, label="KiSignal-Guard: SI, EMC & PDN Verification")
        title_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title_lbl.SetFont(title_font)
        title_lbl.SetForegroundColour(wx.Colour(255, 255, 255))
        h_sizer.Add(title_lbl, 0, wx.ALL, 8)

        sub_lbl = wx.StaticText(header_panel, label="Semantic electrical rule checker: return paths, crosstalk, decoupling, differential skew & thermal vias.")
        sub_lbl.SetForegroundColour(wx.Colour(180, 195, 215))
        h_sizer.Add(sub_lbl, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        header_panel.SetSizer(h_sizer)
        main_sizer.Add(header_panel, 0, wx.EXPAND)

        # Rule Selection Controls
        rules_box = wx.StaticBox(self.frame, label="Active Verification Rules")
        rules_sizer = wx.StaticBoxSizer(rules_box, wx.HORIZONTAL)

        self.chk_rules = {}
        for rule_id, rule in self.engine.rules.items():
            chk = wx.CheckBox(self.frame, label=rule.name[:28] + "...")
            chk.SetValue(rule.enabled)
            chk.Bind(wx.EVT_CHECKBOX, self._on_rule_toggled)
            self.chk_rules[rule_id] = chk
            rules_sizer.Add(chk, 1, wx.ALL | wx.EXPAND, 5)

        main_sizer.Add(rules_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Action Buttons & Status Score Bar
        action_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_run = wx.Button(self.frame, label="▶ Run SI/EMC Inspection", size=(200, 34))
        self.btn_run.SetBackgroundColour(wx.Colour(16, 149, 193))
        self.btn_run.SetForegroundColour(wx.Colour(255, 255, 255))
        self.btn_run.Bind(wx.EVT_BUTTON, self._on_run_analysis)
        action_sizer.Add(self.btn_run, 0, wx.RIGHT, 15)

        self.lbl_score = wx.StaticText(self.frame, label="Ready to analyze PCB layout.")
        score_font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.lbl_score.SetFont(score_font)
        action_sizer.Add(self.lbl_score, 1, wx.ALIGN_CENTER_VERTICAL)

        main_sizer.Add(action_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # Violations Table (ListCtrl)
        self.list_ctrl = wx.ListCtrl(self.frame, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.list_ctrl.InsertColumn(0, "Severity", width=80)
        self.list_ctrl.InsertColumn(1, "Rule ID", width=75)
        self.list_ctrl.InsertColumn(2, "Net Name", width=120)
        self.list_ctrl.InsertColumn(3, "Location (X, Y mm)", width=120)
        self.list_ctrl.InsertColumn(4, "Diagnostic Issue", width=300)
        self.list_ctrl.InsertColumn(5, "Actionable Remediation", width=320)
        main_sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        # Footer with Export and Close buttons
        footer_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_export_html = wx.Button(self.frame, label="Export HTML Report")
        self.btn_export_html.Bind(wx.EVT_BUTTON, self._on_export_html)
        footer_sizer.Add(self.btn_export_html, 0, wx.RIGHT, 10)

        self.btn_export_md = wx.Button(self.frame, label="Export Markdown")
        self.btn_export_md.Bind(wx.EVT_BUTTON, self._on_export_md)
        footer_sizer.Add(self.btn_export_md, 0, wx.RIGHT, 10)

        footer_sizer.AddStretchSpacer()
        self.btn_close = wx.Button(self.frame, label="Close")
        self.btn_close.Bind(wx.EVT_BUTTON, lambda evt: self.frame.EndModal(wx.ID_OK))
        footer_sizer.Add(self.btn_close, 0)

        main_sizer.Add(footer_sizer, 0, wx.EXPAND | wx.ALL, 10)
        self.frame.SetSizer(main_sizer)

    def _on_rule_toggled(self, event):
        for rule_id, chk in self.chk_rules.items():
            self.engine.set_rule_enabled(rule_id, chk.GetValue())

    def _on_run_analysis(self, event):
        if not self.board_snapshot:
            # Try to fetch from live KiCad pcbnew
            from kisignal_guard.core.adapter import PcbnewAdapter
            if PcbnewAdapter.is_kicad_available():
                self.board_snapshot = PcbnewAdapter.load_from_pcbnew()
            else:
                self.wx.MessageBox(
                    "No board snapshot loaded and pcbnew is not active.",
                    "KiSignal-Guard",
                    self.wx.OK | self.wx.ICON_WARNING
                )
                return

        self.current_result = self.engine.run(self.board_snapshot)
        self._populate_results()

    def _populate_results(self):
        if not self.current_result:
            return

        self.list_ctrl.DeleteAllItems()
        res = self.current_result
        score = res.signal_integrity_score

        score_text = f"SI Score: {score:.1f}% ({res.error_count} Errors, {res.warning_count} Warnings in {res.execution_time_ms:.1f}ms)"
        self.lbl_score.SetLabel(score_text)

        for idx, v in enumerate(res.violations):
            row = self.list_ctrl.InsertItem(idx, v.severity.value)
            self.list_ctrl.SetItem(row, 1, v.rule_id)
            self.list_ctrl.SetItem(row, 2, v.net_name)
            self.list_ctrl.SetItem(row, 3, f"({v.location.x:.2f}, {v.location.y:.2f})")
            self.list_ctrl.SetItem(row, 4, v.message)
            self.list_ctrl.SetItem(row, 5, v.recommendation)

    def _on_export_html(self, event):
        if not self.current_result:
            return
        html = ReportGenerator.to_html(self.current_result)
        out_path = os.path.join(os.getcwd(), "kisignal_guard_report.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        self.wx.MessageBox(f"Saved HTML report to: {out_path}", "Export Successful", self.wx.OK | self.wx.ICON_INFORMATION)

    def _on_export_md(self, event):
        if not self.current_result:
            return
        md = ReportGenerator.to_markdown(self.current_result)
        out_path = os.path.join(os.getcwd(), "kisignal_guard_report.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md)
        self.wx.MessageBox(f"Saved Markdown report to: {out_path}", "Export Successful", self.wx.OK | self.wx.ICON_INFORMATION)

    def ShowModal(self):
        return self.frame.ShowModal()
