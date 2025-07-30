import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import sqlite3
import os
from flask import jsonify
from collections import defaultdict
from backend.config import GPU_MAX_HOURS
from backend.tasks.calendar_tasks import CALENDAR_LOGS_DIR

class JobState(Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PENDING = "PENDING"

@dataclass
class SlurmJob:
    job_id: int
    user: str
    partition: str
    cpus: int
    memory_mb: int
    gpus: int
    nodes: int
    node_list: str
    elapsed_time: str
    state: JobState
    command: str
    end_time: str  # New field for the end time column

@dataclass
class UserResourceUsage:
    user: str
    user_role: Optional[str]
    total_cpus: int
    total_memory_mb: int
    total_gpus: int
    running_jobs: int
    total_jobs: int
    hosts: Set[str]

def get_user_role(db_path: str, username: str) -> Optional[str]:
    """Get user role from database"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if Users table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='Users'
        """)
        if not cursor.fetchone():
            conn.close()
            return None
            
        cursor.execute("SELECT user_role FROM Users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"Error getting user role for {username}: {e}")
        return None

def parse_slurm_log(log_content: str) -> List[SlurmJob]:
    """Parse the content of a Slurm log file into a list of SlurmJob objects."""
    jobs = []
    # Skip header lines
    lines = [line for line in log_content.split('\n') if line and not line.startswith('#')]
    
    for line in lines:
        try:
            # Split by pipe character
            parts = line.strip().split('|')
            if len(parts) < 12:  # Now expect 12 fields
                continue
                
            job_id = int(parts[0])
            user = parts[1]
            partition = parts[2]
            cpus = int(parts[3])
            memory_mb = int(parts[4])
            gpus = int(parts[5])
            nodes = int(parts[6])
            node_list = parts[7]
            elapsed_time = parts[8]
            
            # Handle state field which might contain "CANCELLED by X"
            state_str = parts[9]
            if state_str.startswith("CANCELLED"):
                state = JobState.CANCELLED
            else:
                try:
                    state = JobState(state_str)
                except ValueError:
                    # If we can't parse the state, skip this job
                    continue
            
            command = parts[10]
            end_time = parts[11]  # New field
            
            job = SlurmJob(
                job_id=job_id,
                user=user,
                partition=partition,
                cpus=cpus,
                memory_mb=memory_mb,
                gpus=gpus,
                nodes=nodes,
                node_list=node_list,
                elapsed_time=elapsed_time,
                state=state,
                command=command,
                end_time=end_time,
            )
            jobs.append(job)
        except (ValueError, IndexError) as e:
            print(f"Error parsing line: {line}")
            continue
            
    return jobs

def filter_jobs(jobs: List[SlurmJob], 
                states: Optional[List[JobState]] = None,
                users: Optional[List[str]] = None,
                partitions: Optional[List[str]] = None) -> List[SlurmJob]:
    """Filter jobs based on various criteria."""
    filtered = jobs
    
    if states:
        filtered = [job for job in filtered if job.state in states]
    if users:
        filtered = [job for job in filtered if job.user in users]
    if partitions:
        filtered = [job for job in filtered if job.partition in partitions]
        
    return filtered

def calculate_user_resource_usage(jobs, db_path: str) -> Dict[str, UserResourceUsage]:
    """Calculate resource usage per user from a list of jobs, and also return per-host GPU counts."""
    usage_by_user: Dict[str, UserResourceUsage] = {}
    gpus_by_user_host = {}  # {user: {host: gpus}}

    for job in jobs:
        if job.user not in usage_by_user:
            user_role = get_user_role(db_path, job.user)
            usage_by_user[job.user] = UserResourceUsage(
                user=job.user,
                user_role=user_role,
                total_cpus=0,
                total_memory_mb=0,
                total_gpus=0,
                running_jobs=0,
                total_jobs=0,
                hosts=set()
            )
            gpus_by_user_host[job.user] = {}
        usage = usage_by_user[job.user]
        usage.total_cpus += job.cpus
        usage.total_memory_mb += job.memory_mb
        usage.total_gpus += job.gpus
        usage.total_jobs += 1
        if job.state == JobState.RUNNING:
            usage.running_jobs += 1
            if job.node_list and job.node_list != "None assigned":
                usage.hosts.add(job.node_list)
                # Track GPUs per host
                gpus_by_user_host[job.user][job.node_list] = gpus_by_user_host[job.user].get(job.node_list, 0) + job.gpus
    return usage_by_user, gpus_by_user_host

def extract_log_timestamp(log_file):
    """Extract the timestamp from the first line of the slurm log file."""
    with open(log_file, 'r') as f:
        first_line = f.readline()
    # Example: '# Slurm jobs from last 2 hours collected at 2025-07-17 14:10:03'
    import re
    match = re.search(r'collected at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', first_line)
    if match:
        return match.group(1)
    return None

# Modify get_current_usage_summary to use the database and reuse existing code
def get_current_usage_summary(db_path: str):
    """Get a summary of current resource usage suitable for display in a table, and the collection timestamp."""
    from backend.database.queries import get_running_jobs_with_timestamp
    
    # Get running jobs from database
    db_jobs, collection_timestamp = get_running_jobs_with_timestamp(db_path)
    
    # Convert database jobs to SlurmJob objects for reuse of existing code
    jobs = []
    for db_job in db_jobs:
        job = SlurmJob(
            job_id=db_job['job_id'],
            user=db_job['username'],
            partition='gpu',  # Default partition since not stored in DB
            cpus=db_job['cpus'],
            memory_mb=db_job['memory'],
            gpus=db_job['gpus'],
            nodes=1,  # Default to 1 since not stored in DB
            node_list=db_job['machine_name'],
            elapsed_time=db_job['runtime'],
            state=JobState(db_job['state']),
            command=db_job['command'],
            end_time=db_job['end_time']
        )
        jobs.append(job)
    
    # Reuse existing code to calculate usage
    usage_by_user, gpus_by_user_host = calculate_user_resource_usage(jobs, db_path)

    summary = []
    for user, usage in usage_by_user.items():
        hosts_list = []
        for host in sorted(list(usage.hosts)) if usage.hosts else ['None assigned']:
            gpus = gpus_by_user_host.get(user, {}).get(host, 0)
            hosts_list.append({'name': host, 'gpus': gpus})
        summary.append({
            'user': user,
            'user_role': usage.user_role,
            'total_cpus': usage.total_cpus,
            'total_memory_gb': round(usage.total_memory_mb / 1024, 2),  # Convert to GB
            'total_gpus': usage.total_gpus,
            'hosts': hosts_list
        })
    return sorted(summary, key=lambda x: x['total_gpus'], reverse=True), collection_timestamp

def store_slurm_jobs(jobs: List[SlurmJob], db_path: str, collection_timestamp: Optional[str] = None) -> bool:
    """Store Slurm jobs in the database"""
    print(f"Storing {len(jobs)} Slurm jobs in the database")
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Start a transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Use provided collection timestamp or current time
        if collection_timestamp:
            # Parse the collection timestamp
            try:
                created_at = datetime.strptime(collection_timestamp, '%Y-%m-%d %H:%M:%S')
                print(f"Collection timestamp: {collection_timestamp}")
            except ValueError as e:
                print(f"Error parsing collection timestamp '{collection_timestamp}': {e}")
                # Fallback to January 1st, 2000
                created_at = datetime(2000, 1, 1, 0, 0, 0)
        else:
            # Use current time as before
            from backend.utils.timezone_utils import get_current_time_cet
            created_at = get_current_time_cet()
        
        # Clear all existing jobs before inserting new ones
        cursor.execute("DELETE FROM Jobs")
        
        # Store each job
        for job in jobs:
            # Get or create user
            cursor.execute("SELECT user_id FROM Users WHERE username = ?", (job.user,))
            result = cursor.fetchone()
            if result:
                user_id = result[0]
            else:
                cursor.execute(
                    "INSERT INTO Users (username) VALUES (?)",
                    (job.user,)
                )
                user_id = cursor.lastrowid
            
            # Get or create machine
            cursor.execute(
                "SELECT machine_id FROM Machines WHERE machine_name = ? AND machine_type = 'gpu'",
                (job.node_list,)
            )
            result = cursor.fetchone()
            if result:
                machine_id = result[0]
            else:
                cursor.execute(
                    "INSERT INTO Machines (machine_name, machine_type) VALUES (?, 'gpu')",
                    (job.node_list,)
                )
                machine_id = cursor.lastrowid
            
            # Insert job (use REPLACE to handle duplicate job IDs)
            cursor.execute("""
                INSERT OR REPLACE INTO Jobs (
                    job_id, user_id, machine_id,
                    cpus, memory, gpus, runtime, state, command, end_time, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.job_id, user_id, machine_id,
                job.cpus, job.memory_mb, job.gpus,
                job.elapsed_time, job.state.value, job.command, job.end_time, created_at
            ))
        
        # Commit transaction
        conn.commit()

        return True
        
    except Exception as e:
        print(f"Error storing Slurm jobs: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close() 