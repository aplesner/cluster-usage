from backend.parsers.slurm_parser import parse_slurm_log, store_slurm_jobs
from backend.tasks.calendar_tasks import CALENDAR_LOGS_DIR
from config import DB_PATH, SLURM_DIRECTORY
import os
import logging



logger = logging.getLogger(__name__)

def parse_and_store_slurm_log():
    """Scheduled task to parse the Slurm log and store jobs in the database."""
    slurm_log_file = SLURM_DIRECTORY
    if not os.path.exists(slurm_log_file):
        logger.warning(f"Slurm log file not found: {slurm_log_file}")
        return {"status": "skipped", "reason": "Slurm log file not found"}
    
    # Extract the collection timestamp from the log file header
    from backend.parsers.slurm_parser import extract_log_timestamp
    collection_timestamp = extract_log_timestamp(slurm_log_file)
    
    with open(slurm_log_file, 'r') as f:
        log_content = f.read()
    jobs = parse_slurm_log(log_content)
    result = store_slurm_jobs(jobs, DB_PATH, collection_timestamp)
    return {"status": "success" if result else "error", "jobs_count": len(jobs), "jobs[:10]": jobs[:10], "collection_timestamp": collection_timestamp, "filename": slurm_log_file} 