"""Scheduled privacy jobs (M12). Run hourly from cron / Task Scheduler:

    python tools/run_jobs.py

* purges accounts whose 14-day deletion window has ended
* ends lapsed web / dev access, sends trial-ending and renewal reminders
* runs the 24-month retention sweep (does nothing until
  ARCH_RETENTION_SWEEP_ENABLED=true)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services import privacy_service as P  # noqa: E402


def main():
    from app.services.billing_service import run_billing_jobs
    out = {"purged": P.purge_due(), "retention": P.retention_sweep(), "billing": run_billing_jobs()}
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
