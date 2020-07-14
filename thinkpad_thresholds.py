import os

"""
Shows the ThinkPad battery charge thresholds.

Configuration parameters:
    battery_id: id of the battery to be displayed
        (default 0)
    cache_timeout: a timeout to refresh the battery state
        (default 60)
    format: string that formats the output, see placeholders below
        (default "{start}% → {stop}%")

Format placeholders:
    {start} - the start battery percentage
    {stop} - the stop battery percentage

TODO: use composite output to allow setting them.
"""

class Py3status:
    battery_id       = 0
    cache_timeout    = 60
    format           = "{start}% → {stop}%"
    sys_battery_path = "/sys/class/power_supply/"

    def thinkpad_thresholds(self):
        start = self._read_prop("charge_start_threshold")
        stop  = self._read_prop("charge_stop_threshold")

        return {
            "full_text":    self.py3.safe_format(self.format, dict(
                start=start,
                stop=stop,
            )),
            "cached_until": self.py3.time_in(self.cache_timeout),
        }

    def _read_prop(self, name):
        with open(os.path.join(self.sys_battery_path, f"BAT{self.battery_id}", name)) as f:
            return f.read().splitlines()[0]

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    import py3status.module_test
    py3status.module_test.module_test(Py3status)
