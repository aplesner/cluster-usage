#!/bin/bash

source scripts/variables.sh

# Push slurm-script.sh to the server at `~/bin/slurm-script.sh`
rsync -avz --progress scripts/slurm-script.sh "$USER@$SERVER:~/bin/slurm-script.sh"

