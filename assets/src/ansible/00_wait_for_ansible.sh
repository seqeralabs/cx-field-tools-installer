#!/bin/bash

end_time=$((SECONDS+120))

while [ ! -x "$(command -v ansible-playbook)" ]; do 
  if [ $SECONDS -ge $end_time ]; then
    echo "Timeout while waiting for ansible-playbook to become available"
    exit 1
  fi
  echo "ansible-playbook not yet available"
  sleep 5
done