from backend.parsers.slurm_parser import parse_slurm_log, store_slurm_jobs
from backend.tasks.calendar_tasks import CALENDAR_LOGS_DIR
from config import DB_PATH
import os
import logging

logger = logging.getLogger(__name__)

def parse_and_store_slurm_log():
    """Scheduled task to parse the Slurm log and store jobs in the database."""
    slurm_log_file = os.path.join(CALENDAR_LOGS_DIR, 'slurm', 'slurm.log')
    if not os.path.exists(slurm_log_file):
        logger.warning(f"Slurm log file not found: {slurm_log_file}")
        return {"status": "skipped", "reason": "Slurm log file not found"}
    with open(slurm_log_file, 'r') as f:
        log_content = f.read()
    jobs = parse_slurm_log(log_content)
    result = store_slurm_jobs(jobs, DB_PATH)
    return {"status": "success" if result else "error", "jobs_count": len(jobs)} 