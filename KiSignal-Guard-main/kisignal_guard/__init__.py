"""
KiSignal-Guard: High-Speed Signal Integrity & EMC Plugin for KiCad 9.
"""

from kisignal_guard.plugin import KiSignalGuardAction

# Instantiate and register with KiCad pcbnew
action = KiSignalGuardAction()
action.register()
