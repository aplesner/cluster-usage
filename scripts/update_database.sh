#!/bin/bash

eval "$(ssh-agent -s)"
ssh-add /local/home/aplesner/.ssh/id_rsa

cd /local/home/aplesner/cluster-usage

./scripts/fetch_logs.sh
./scripts/import_logs.sh

kill $SSH_AGENT_PID
