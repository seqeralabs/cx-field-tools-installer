#!/usr/bin/env sh

# Having a subshell in the .tpl file was causing the Terraform function to throw a fit.
# Move Bash logic to a separate file which does not need to go through the template file, and reference via a 'source' command in the Ansible script.
source $HOME/target/bash/remote/codecommit_set_workspace_id.sh

echo "-***** EXECUTING CUSTOM CURL***"
export WORKSPACEID=$(tw --output json workspaces list -o $CC_ORG_NAME | jq --arg cc_workspace_name $CC_WORKSPACE_NAME '.workspaces[] | select(.workspaceName==$cc_workspace_name) | .workspaceId')

payload=$(jq --arg user "$SEQERAKIT_CODECOMMIT_USER" --arg password "$SEQERAKIT_CODECOMMIT_PASSWORD" --arg region "$SEQERAKIT_CODECOMMIT_REGION" '.credentials.baseUrl=$region | .credentials.keys.username=$user | .credentials.keys.password=$password' $HOME/target/seqerakit/credentials/codecommit.json)
echo "Payload is:"
echo $payload > /tmp/payload.txt
curl -H "Authorization: Bearer $TOWER_ACCESS_TOKEN" -H "Accept: application/json" -H "Content-Type: application/json" -X POST "$TOWER_API_ENDPOINT/credentials?workspaceId=$WORKSPACEID" -d "$payload" --verbose