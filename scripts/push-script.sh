#!/bin/bash

source scripts/variables.sh

eval "$(ssh-agent -s)"
ssh-add /local/home/aplesner/.ssh/id_rsa

# Push slurm-script.sh to the server at `~/bin/slurm-script.sh`
rsync -avz --progress scripts/slurm-script.sh "$USER@$SERVER:~/bin/slurm-script.sh"

# ssh into the server and make the script executable
ssh "$USER@$SERVER" << SCRIPT
    cd ~/bin
    chmod +x slurm-script.sh
SCRIPT

kill $SSH_AGENT_PID
