#!/bin/bash

eval "$(ssh-agent -s)"
ssh-add /local/home/aplesner/.ssh/id_rsa

cd /var/www/cluster-usage-dashboard

./scripts/fetch_logs.sh
./scripts/import_logs.sh

kill $SSH_AGENT_PID
