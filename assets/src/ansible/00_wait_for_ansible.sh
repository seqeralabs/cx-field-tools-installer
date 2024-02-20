#!/bin/bash

while [ ! -x "$(command -v ansible-playbook)" ]; do echo "ansible-playbook not yet available"; sleep 5; done