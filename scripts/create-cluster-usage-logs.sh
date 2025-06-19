#!/bin/bash

# Source variables
source scripts/variables.sh

# ssh into the server, cd to ~/bin, and run `./slurm-script.sh --last-hours 2`
ssh "$USER@$SERVER" << EOF

cd ~/bin
./slurm-script.sh --last-hours 2
