"""Scheduled jobs inside the API process (QA rounds 5 and 6).

Before this, the purge after the deletion grace period (79/80), the retention
sweep, billing reminders (trial ending, renewals) and the Google Play
acknowledgement retry only ran from /v1/dev/run-jobs, which production
refuses. Every ARCH_JOBS_INTERVAL_MINUTES (60 by default on production and
staging, off in dev) one thread runs them all. Assumes one uvicorn worker per
port, as the run scripts start it.
"""
import logging
import threading

from app import config

log = logging.getLogger("arch.jobs")
_stop = threading.Event()
_thread = None


def run_all() -> dict:
    from app.services import billing_service as B
    from app.services import privacy_service as P
    out = {}
    for name, job in (("purged", P.purge_due), ("retention", P.retention_sweep),
                      ("billing", B.run_billing_jobs), ("google_ack", B.retry_google_acknowledgements)):
        try:
            out[name] = job()
        except Exception as exc:          # one failing job never stops the others
            log.exception("job %s failed", name)
            out[name] = {"error": str(exc)}
    return out


def _loop(interval_s: float):
    while not _stop.wait(interval_s):
        log.info("scheduled jobs: %s", run_all())


def start():
    global _thread
    if config.JOBS_INTERVAL_MINUTES <= 0 or (_thread and _thread.is_alive()):
        return False
    _stop.clear()
    _thread = threading.Thread(target=_loop, args=(config.JOBS_INTERVAL_MINUTES * 60,),
                               name="arch-jobs", daemon=True)
    _thread.start()
    log.info("scheduled jobs every %s minutes", config.JOBS_INTERVAL_MINUTES)
    return True


def stop():
    _stop.set()
