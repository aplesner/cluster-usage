#!/bin/bash
#
# Simple Slurm Running Jobs Logger
# Logs all jobs to text file without any aggregation
#
 
# Default configuration
LOG_DIR="./slurm-logs"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
DATE_STR=$(date '+%Y-%m-%d')
LAST_HOURS=""
VERBOSE=false
LOGS=true
 
# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --log-dir)
            LOG_DIR="$2"
            shift 2
            ;;
        --last-hours)
            LAST_HOURS="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift 1
            ;;
        *)
            echo "Usage: $0 [--log-dir DIR] [--last-hours N] [--verbose]"
            echo "  --last-hours N    Get jobs from last N hours instead of current running jobs"
            exit 1
            ;;
    esac
done
 
# Create log directory
mkdir -p "$LOG_DIR"
 
# Check if Slurm commands are available
if [[ -n "$LAST_HOURS" ]]; then
    if ! command -v sacct &> /dev/null; then
        echo "Error: sacct command not found in PATH (needed for historical data)"
        exit 1
    fi
    echo "Collecting jobs from last $LAST_HOURS hours at $TIMESTAMP"
else
    if ! command -v squeue &> /dev/null; then
        echo "Error: squeue command not found in PATH"
        exit 1
    fi
    echo "Collecting running jobs at $TIMESTAMP"
fi
 
# Create output file with header
if [[ -n "$LAST_HOURS" ]]; then
    output_file="$LOG_DIR/slurm.log"
    # output_file="$LOG_DIR/jobs_last_${LAST_HOURS}h.txt"
    echo "# Slurm jobs from last $LAST_HOURS hours collected at $TIMESTAMP" > "$output_file"
    echo "# Format: JobID|User|Partition|CPUs|Memory|GPUs|Nodes|NodeList|ElapsedTime|State|Command" >> "$output_file"
else
    output_file="$LOG_DIR/running_jobs.txt"
    echo "# Slurm running jobs collected at $TIMESTAMP" > "$output_file"
    echo "# Format: JobID|User|Partition|CPUs|Memory|GPUs|Nodes|NodeList|ElapsedTime|State|Command" >> "$output_file"
fi
 
# Get job data with appropriate command
if [[ -n "$LAST_HOURS" ]]; then
    # Use sacct for historical data
    start_time=$(date -d "$LAST_HOURS hours ago" '+%Y-%m-%dT%H:%M:%S')
    sacct --starttime="$start_time" --allusers --format="JobID,User,Partition,NCPUS,ReqMem,ReqTRES,NNodes,NodeList,Elapsed,State,JobName" --noheader --parsable2 > "$LOG_DIR/jobs_raw_last_${LAST_HOURS}h.txt"
    raw_file="$LOG_DIR/jobs_raw_last_${LAST_HOURS}h.txt"
else
    # Use squeue for current running jobs
    squeue --states=RUNNING --format="%A|%u|%P|%C|%m|%b|%D|%N|%M|%T|%o" --noheader > "$LOG_DIR/running_jobs_raw.txt"
    raw_file="$LOG_DIR/running_jobs_raw.txt"
fi
 
# Process and output each job individually
total_jobs=0
total_cpus=0
total_memory=0
total_gpus=0
total_nodes=0
 
while IFS='|' read -r job_id user partition cpus memory gres nodes nodelist elapsed state command; do
    if [[ -n "$job_id" ]]; then
        # Skip job steps (like .batch, .extern) - only process main jobs
        if [[ "$job_id" =~ \.(batch|extern)$ ]] || [[ -z "$user" ]]; then
            continue
        fi
        
        # Parse GPU count from GRES/TRES (handle both squeue and sacct formats)
        gpu_count=0
        if [[ "$gres" =~ gpu:([0-9]+) ]]; then
            gpu_count="${BASH_REMATCH[1]}"
        elif [[ "$gres" =~ gpu:[^:]+:([0-9]+) ]]; then
            gpu_count="${BASH_REMATCH[1]}"
        elif [[ "$gres" =~ gres/gpu=([0-9]+) ]]; then
            # Handle ReqTRES format: gres/gpu=2
            gpu_count="${BASH_REMATCH[1]}"
        elif [[ "$gres" =~ gres/gpu:[^=]+=([0-9]+) ]]; then
            # Handle ReqTRES format: gres/gpu:v100=2
            gpu_count="${BASH_REMATCH[1]}"
        fi
        
        # Parse memory to MB (handle both squeue and sacct formats)
        memory_mb=0
        if [[ "$memory" =~ ^([0-9]+)G$ ]] || [[ "$memory" =~ ^([0-9]+)Gc?$ ]]; then
            memory_mb=$((${BASH_REMATCH[1]} * 1024))
        elif [[ "$memory" =~ ^([0-9]+)M[cn]?$ ]] || [[ "$memory" =~ ^([0-9]+)$ ]]; then
            memory_mb=${BASH_REMATCH[1]}
        elif [[ "$memory" =~ ^([0-9]+)T$ ]]; then
            memory_mb=$((${BASH_REMATCH[1]} * 1024 * 1024))
        fi
        
        # Output job directly to file
        echo "$job_id|$user|$partition|$cpus|$memory_mb|$gpu_count|$nodes|$nodelist|$elapsed|$state|$command" >> "$output_file"
        
        # Update totals
        total_jobs=$((total_jobs + 1))
        total_cpus=$((total_cpus + cpus))
        total_memory=$((total_memory + memory_mb))
        total_gpus=$((total_gpus + gpu_count))
        total_nodes=$((total_nodes + nodes))
    fi
done < "$raw_file"

# If verbose printing is enabled, output detailed information
if [[ "$VERBOSE" == true ]]; then
    echo "Done! Generated files:"
    echo "  Jobs: $output_file"
    echo "  Raw data: $raw_file"
    echo ""
    if [[ -n "$LAST_HOURS" ]]; then
        echo "Summary (last $LAST_HOURS hours):"
    else
        echo "Summary (currently running):"
    fi
    echo "  Total jobs: $total_jobs"
    echo "  Total CPUs in use: $total_cpus"
    echo "  Total Memory in use: ${total_memory} MB"
    echo "  Total GPUs in use: $total_gpus"
    echo "  Total Nodes in use: $total_nodes"
fi

### EXECUTE WITH ./script.sh --last-hours 24 (and then set to like 4 hours)
