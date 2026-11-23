"""
KiCad 9 ActionPlugin entrypoint for KiSignal-Guard.
Inherits from pcbnew.ActionPlugin and registers with KiCad's Plugin and Content Manager (PCM).
"""

import os
import sys

# Ensure plugin root is in sys.path
plugin_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(plugin_dir)
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


class KiSignalGuardAction(object):
    """
    Action plugin class that safely handles both KiCad pcbnew environment
    and mock/test environments.
    """

    def __init__(self):
        try:
            import pcbnew
            # Dynamically inherit from pcbnew.ActionPlugin if inside KiCad
            class _KiCadPlugin(pcbnew.ActionPlugin):
                def defaults(self_inner):
                    self_inner.name = "KiSignal-Guard"
                    self_inner.category = "Signal Integrity & DRC"
                    self_inner.description = "Semantic High-Speed Signal Integrity, EMC & PDN Analyzer"
                    self_inner.show_on_toolbar = True
                    icon_path = os.path.join(plugin_dir, "icon.png")
                    if os.path.exists(icon_path):
                        self_inner.icon_file_name = icon_path

                def Run(self_inner):
                    from kisignal_guard.core.adapter import PcbnewAdapter
                    from kisignal_guard.ui.main_dialog import KiSignalGuardDialog
                    try:
                        board_snapshot = PcbnewAdapter.load_from_pcbnew()
                        dlg = KiSignalGuardDialog(board_snapshot=board_snapshot)
                        dlg.ShowModal()
                    except Exception as err:
                        import wx
                        wx.MessageBox(f"KiSignal-Guard error: {err}", "Error", wx.OK | wx.ICON_ERROR)

            self.impl = _KiCadPlugin()
        except ImportError:
            self.impl = None

    def register(self):
        """Registers the action plugin with pcbnew if available."""
        if self.impl is not None:
            self.impl.register()
