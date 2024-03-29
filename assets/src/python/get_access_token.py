#!/usr/bin/env python3


import datetime
import json
import os
import subprocess

SEQERAKIT_USE_HOSTS_FILE = os.getenv('SEQERAKIT_USE_HOSTS_FILE')
if SEQERAKIT_USE_HOSTS_FILE == "true":
    TOWER_API_ENDPOINT = f"http:/localhost:8000/api"
else:
    TOWER_API_ENDPOINT = os.getenv('TOWER_API_ENDPOINT')


SEQERAKIT_TEST_TOKEN = f"SEQERAKIT_TEST_TOKEN_{datetime.datetime.now().timestamp()}"
EMAIL_ADDRESS = ''
UID = 1


# Grab first TOWER_ROOT_USERS entry for login purposes
key = "TOWER_ROOT_USERS="
#  Hardcoding path bad, but this is hardcoded lots of other places so ok for now.
with open('/home/ec2-user/tower.env', 'r') as file:
    '''Find the TOWER_ROOT_USER entry, split on comma if multiple value, and grab first entry'''
    lines = file.readlines()
    
    for line in lines:
        if line.startswith(key):
            values = line.split('=')[1]
            try:
                EMAIL_ADDRESS = values.split(',')[0]
            except Exception as e:
                EMAIL_ADDRESS = values

    if EMAIL_ADDRESS == '':
        raise Exception("Sorry, your `tower.env` does not have a usable TOWER_ROOT_USERS value. Please fix and try again.")


# Need to properly escape doublequotes for json payload. Strip \n off constant since that breaks curl.
login_payload =  {"email": EMAIL_ADDRESS.strip()}
login_payload = json.dumps(login_payload)
print(login_payload)

login_command = f"curl -Ss '{TOWER_API_ENDPOINT}/gate/access' -H 'Content-Type: application/json' -d '" + login_payload + "' -o /dev/null"
login = subprocess.run( login_command, shell=True, text=True, capture_output=False )
print(login_payload)

# Get auth token from database
is_external_db_in_use = os.getenv("DB_POPULATE_EXTERNAL_INSTANCE")
if str(is_external_db_in_use) == "true":

    app_name = os.getenv('APP_NAME')
    ssm_tower_db_user = f"/config/{app_name}/datasources/default/username"
    ssm_tower_db_password = f"/config/{app_name}/datasources/default/password"

    tower_db_user = subprocess.run(
        "aws ssm get-parameters --name " + ssm_tower_db_user + " --with-decryption --query 'Parameters[*].{Value:Value}' --output text",
        shell=True, text=True, capture_output=True
    )
    tower_db_user = tower_db_user.stdout.replace('\n', '')

    tower_db_password = subprocess.run(
        "aws ssm get-parameters --name " + ssm_tower_db_password + " --with-decryption --query 'Parameters[*].{Value:Value}' --output text",
        shell=True, text=True, capture_output=True
    )
    tower_db_password = tower_db_password.stdout.replace('\n', '')

    mysql_connection = f"mysql --host {os.getenv('DB_URL')} --port=3306 --user={tower_db_user} --password={tower_db_password}" 
    auth_token = subprocess.run(
        # Old call was too brittle -- assumed the first root user would be the first DB entry. Only true for first time greenfield deployments.
        # Modified SQL to search the db table for the same email that we grabbed above for initial login

        # [f"mysql --host {os.getenv('DB_URL')} --port=3306 --user={tower_db_user} --password={tower_db_password} <<< 'use tower; select auth_token FROM tw_user WHERE id=1;' | sed -n '2p'"], 
        # shell=True, text=True, capture_output=True
        [f"{mysql_connection} <<< \"use tower; select auth_token FROM tw_user WHERE email='{EMAIL_ADDRESS}';\" | sed -n '2p'"],
        shell=True, text=True, capture_output=True
    )

else:
    auth_token = subprocess.run(
        ["docker exec -i ec2-user-db-1 mysql -utower -ptower <<< 'use tower; select auth_token FROM tw_user WHERE id=1;' | sed -n '2p'"], 
        shell=True, text=True, capture_output=True
    )

auth_token = auth_token.stdout.replace('\n', '')
print("Auth token is: ", auth_token)


# Log in to Tower with auth code.
jwt_command = f"curl -Ss -d 'username={UID}' -d 'password={auth_token}' -c - '{TOWER_API_ENDPOINT}/login' | grep -w JWT | rev | cut -f 1 | rev"
jwt_token = subprocess.run( jwt_command, shell=True, text=True, capture_output=True )
print('jwt_stdout is: ', jwt_token.stdout)


# Generate PAT
pat_payload = { "name": SEQERAKIT_TEST_TOKEN.strip() }
pat_payload = json.dumps(pat_payload)

pat_command = f"curl -Ss '{TOWER_API_ENDPOINT}/tokens' -H 'Content-Type: application/json' -H 'Authorization: Bearer {jwt_token.stdout.strip()}' -d '{pat_payload}' | jq -r '.accessKey'",
pat_token = subprocess.run( pat_command, shell=True, text=True, capture_output=True )
print("Token Value is: ", pat_token.stdout)


# Write Token to bashrc
subprocess.run( ["echo 'export TOWER_ACCESS_TOKEN=" + pat_token.stdout + "' >> /home/ec2-user/.bashrc"], shell=True )