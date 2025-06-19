#!/bin/bash

eval "$(ssh-agent -s)"
ssh-add /local/home/aplesner/.ssh/id_rsa

cd /var/www/cluster-usage-dashboard

source scripts/variables.sh

# ssh into the server, cd to ~/bin, and run `./slurm-script.sh --last-hours 2`
ssh "$USER@$SERVER" << SCRIPT
    cd ~/bin
    ./slurm-script.sh --last-hours 2
SCRIPT

kill $SSH_AGENT_PID