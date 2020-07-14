import datetime
import dateutil
import icalendar

"""
Shows the next iCalendar event. Recurring or whole-day events are not supported.

Configuration parameters:
    ics_url: URL to download the iCalendar feed from
        (required)
    cache_timeout: how often to refresh the current event in seconds (warning: this is currently somewhat inefficient, especially for larger calendars)
        (default 60)
    cache_ics_timeout: how often to refresh the calendar feed in seconds
        (default 900)
    format: string that formats the output, see placeholders below
        (default "{title} @ {time}")
    format_none: format for when there aren't any events
        (default "")
    urgent_time: minutes before event start to mark it as urgent
        (default 15)

Format placeholders:
    {title} - the event title
    {time} - the event start time

TODO: add buttons to switch events.
"""

class Py3status:
    ics_url           = ""
    cache_timeout     = 60
    cache_ics_timeout = 900
    format            = "{title} @ {time}"
    format_none       = ""
    urgent_time       = 15

    _configured_ts = None

    def post_config_hook(self):
        if not self.ics_url:
            raise Exception("missing ics_url")
        self._configured_ts = datetime.datetime.utcnow().timestamp()

    def _ckey(self):
        return (self.ics_url, self.ics_url + "@@mtime")

    def _ical(self):
        ts = datetime.datetime.utcnow().timestamp()
        ckt, ckd = self._ckey()

        st = self.py3.storage_get(ckt)
        sd = self.py3.storage_get(ckd)

        if st and sd and isinstance(st, str) and isinstance(sd, int) and sd > self._configured_ts and abs(ts - sd) < self.cache_ics_timeout:
            return st

        st = str(self.py3.request(self.ics_url, timeout=3).text)
        sd = ts

        self.py3.storage_set(ckt, st)
        self.py3.storage_set(ckd, sd)

        return st

    def icalendar_event(self):
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        cal = icalendar.Calendar.from_ical(self._ical())

        l_title = None
        l_time  = None

        for evt in cal.walk("vevent"):
            e_title = str(evt.get("summary", ""))
            e_time = evt.get("dtstart").dt
            if not isinstance(e_time, datetime.datetime):
                continue # it's probably a whole-day event
            e_time = e_time.astimezone()

            if e_time > now:
                if l_time and e_time > l_time:
                    continue
                l_title = e_title
                l_time = e_time
        
        if not l_time:
            return {
                "full_text": self.py3.safe_format(self.format_none),
                "cached_until": self.py3.time_in(self.cache_timeout),
            }

        delta = l_time - now
        
        args = dict(
            title=str(l_title).replace("&", "_"), # py3status doesn't like & signs for some reason
            time=datetime.datetime.strftime(l_time, "%a %d %b %Y %H:%M %Z"),
            urgent=bool(delta < datetime.timedelta(minutes=self.urgent_time)),
        )

        return {
            "full_text": self.py3.safe_format(self.format, args),
            "cached_until": self.py3.time_in(self.cache_timeout),
            "urgent": args["urgent"],
        }

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    import sys
    import py3status.module_test
    py3status.module_test.module_test(Py3status, config=dict(
        ics_url=sys.argv[1]
    ))
