#!/bin/bash

SRC=assets/src
TARGET=assets/target

rm -rf $TARGET/* && sleep 5
mkdir -p $TARGET

# Delete EC2 key
rm ssh_key_for_* || true

# Copy some source folders to target
cp -R $SRC/ansible $TARGET
cp -R $SRC/customcerts $TARGET
cp -R $SRC/python $TARGET
cp -R $SRC/seqerakit $TARGET
cp -R $SRC/docker_compose $TARGET

# Create necessary folders which weren't copied over (because templated data will be put here)
mkdir -p $TARGET/bash/remote
mkdir -p $TARGET/tower_config
mkdir -p $TARGET/groundswell_config
mkdir -p $TARGET/docker_logging

# Purge template files from target
find $TARGET -name '*.tpl' -delete

# Purge unnecessary folders from target
rm -rf $TARGET/seqerakit/compute-envs   || true

# Copy over static Bash script
cp -R $SRC/bash/remote/codecommit_create_credential.sh $TARGET/bash/remote/