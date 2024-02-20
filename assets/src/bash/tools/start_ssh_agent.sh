#!/bin/bash

# How to invoke: /bin/bash start_ssh_agent PRIVATE_IP_OF_BATCH_INSTANCE_FROM_get_batch_instance_id.sh

eval `ssh-agent`
ssh-add $(find ssh_key*)
ssh-add -l

echo 'Remember to use `kill $SSH_AGENT_PID` when done!'
ssh -AJ seqera ec2-user@$1