import machine

_wdt = None


def start(timeout_ms=8000):
    """Start the hardware watchdog (cannot be stopped until reboot)."""
    global _wdt
    _wdt = machine.WDT(timeout=timeout_ms)


def feed():
    if _wdt is not None:
        _wdt.feed()
