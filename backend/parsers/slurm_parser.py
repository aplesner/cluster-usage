import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import sqlite3
import os
from flask import jsonify

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
            if len(parts) < 11:  # We need exactly 11 fields
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

def calculate_user_resource_usage(jobs: List[SlurmJob], db_path: str) -> Dict[str, UserResourceUsage]:
    """Calculate resource usage per user from a list of jobs."""
    usage_by_user: Dict[str, UserResourceUsage] = {}
    
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
            
        usage = usage_by_user[job.user]
        usage.total_cpus += job.cpus
        usage.total_memory_mb += job.memory_mb
        usage.total_gpus += job.gpus
        usage.total_jobs += 1
        
        if job.state == JobState.RUNNING:
            usage.running_jobs += 1
            if job.node_list and job.node_list != "None assigned":
                usage.hosts.add(job.node_list)
            
    return usage_by_user

def get_current_usage_summary(jobs: List[SlurmJob], db_path: str) -> List[Dict]:
    """Get a summary of current resource usage suitable for display in a table."""
    running_jobs = filter_jobs(jobs, states=[JobState.RUNNING])
    usage_by_user = calculate_user_resource_usage(running_jobs, db_path)
    
    # Convert to list of dicts for easy JSON serialization
    summary = []
    for user, usage in usage_by_user.items():
        summary.append({
            'user': user,
            'user_role': usage.user_role,
            'total_cpus': usage.total_cpus,
            'total_memory_gb': round(usage.total_memory_mb / 1024, 2),  # Convert to GB
            'total_gpus': usage.total_gpus,
            'hosts': sorted(list(usage.hosts)) if usage.hosts else ['None assigned']
        })
        
    return sorted(summary, key=lambda x: x['total_gpus'], reverse=True)  # Sort by GPU usage

def store_slurm_jobs(jobs: List[SlurmJob], db_path: str) -> bool:
    """Store Slurm jobs in the database"""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Start a transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Get or create the latest log entry
        current_time = datetime.now()
        unix_timestamp = int(current_time.timestamp())
        timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute(
            "INSERT INTO LogEntries (timestamp, unix_timestamp) VALUES (?, ?)",
            (timestamp, unix_timestamp)
        )
        log_id = cursor.lastrowid
        
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
                    job_id, log_id, user_id, machine_id,
                    cpus, memory, gpus, runtime, state, command
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.job_id, log_id, user_id, machine_id,
                job.cpus, job.memory_mb, job.gpus,
                job.elapsed_time, job.state.value, job.command
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