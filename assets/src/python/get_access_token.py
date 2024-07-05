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


# Grab first TOWER_ROOT_USERS entry for login purposes
# Hardcoding path bad, but this is hardcoded lots of other places so ok for now.
with open('/home/ec2-user/tower.env', 'r') as file:
    '''Find the TOWER_ROOT_USER entry, split on comma if multiple value, and grab first entry'''
    lines = file.readlines()
    
    for line in lines:
        if line.startswith("TOWER_ROOT_USERS="):
            values = line.split('=')[1]
            try:
                EMAIL_ADDRESS = values.split(',')[0].strip()
                # EMAIL_ADRRESS = EMAIL_ADDRESS.strip().rstrip(os.linesep)
                break

            except Exception as e:
                raise Exception(f"Sorry, your `tower.env` has an unusable TOWER_ROOT_USERS value. Error: {e}")

    if EMAIL_ADDRESS == '':
        raise Exception("Sorry, your `tower.env` has an empty TOWER_ROOT_USERS value. Please populate and try again.")

APP_NAME = os.getenv('APP_NAME')
SSM_TOWER_DB_USER = f"/config/{APP_NAME}/datasources/default/username"
SSM_TOWER_DB_PASSWORD = f"/config/{APP_NAME}/datasources/default/password"

tower_db_user = subprocess.run(
        "aws ssm get-parameters --name " + SSM_TOWER_DB_USER + " --with-decryption --query 'Parameters[*].{Value:Value}' --output text",
        shell=True, text=True, capture_output=True)
tower_db_user = tower_db_user.stdout.replace('\n', '')

tower_db_password = subprocess.run(
        "aws ssm get-parameters --name " + SSM_TOWER_DB_PASSWORD + " --with-decryption --query 'Parameters[*].{Value:Value}' --output text",
        shell=True, text=True, capture_output=True)
tower_db_password = tower_db_password.stdout.replace('\n', '')


# Need to properly escape doublequotes for json payload. Strip \n off constant since that breaks curl.
login_payload =  {"email": EMAIL_ADDRESS}
login_payload = json.dumps(login_payload)
print(login_payload)

login_command = f"curl -Ss '{TOWER_API_ENDPOINT}/gate/access' -H 'Content-Type: application/json' -d '" + login_payload + "' -o /dev/null"
login = subprocess.run( login_command, shell=True, text=True, capture_output=False )
print(login)

# Get auth token from database
is_external_db_in_use = os.getenv("DB_POPULATE_EXTERNAL_INSTANCE")
if str(is_external_db_in_use) == "true":

    # Old call was too brittle -- assumed the first root user would be the first DB entry. Only true for first time greenfield deployments.
    # Modified SQL to search the db table for the same email that we grabbed above for initial login
    rds_query = f"""docker run --rm -t -e MYSQL_PWD={tower_db_password} mysql:8.0 mysql --host {os.getenv('DB_URL')} --port=3306 -u{tower_db_user} --silent --skip-column-names --execute 'select auth_token FROM tower.tw_user WHERE email="{EMAIL_ADDRESS}";' """
    auth_token = subprocess.run( [rds_query], shell=True, text=True, capture_output=True )

    # UID is not always guaranteed to be 1. Run extra query to get UID associated with the email address we are using.
    uid_query = f"""docker run --rm -t -e MYSQL_PWD={tower_db_password} mysql:8.0 mysql --host {os.getenv('DB_URL')} --port=3306 -u{tower_db_user} --silent --skip-column-names --execute 'select id FROM tower.tw_user WHERE email="{EMAIL_ADDRESS}";' """
    uid_value = subprocess.run(uid_query, shell=True, text=True, capture_output=True )
    uid_value = uid_value.stdout.replace('\n', '')

else:
    auth_token = subprocess.run(
        [f"""docker exec -i ec2-user-db-1 mysql -u{tower_db_user} -p{tower_db_password} --silent --skip-column-names --execute  'select auth_token FROM tower.tw_user WHERE email="{EMAIL_ADDRESS}";'"""], 
        shell=True, text=True, capture_output=True)
    
    # UID is not always guaranteed to be 1. Run extra query to get UID associated with the email address we are using.
    uid_query = f"""docker exec -i ec2-user-db-1 mysql -u{tower_db_user} -p{tower_db_password} --silent --skip-column-names --execute 'select id FROM tower.tw_user WHERE email="{EMAIL_ADDRESS}";' """
    uid_value = subprocess.run(uid_query, shell=True, text=True, capture_output=True )
    uid_value = uid_value.stdout.replace('\n', '')


auth_token = auth_token.stdout.replace('\n', '')
print("Auth token is: ", auth_token)

# Log in to Tower with auth code.
jwt_command = f"curl -Ss -d 'username={uid_value}' -d 'password={auth_token}' -c - '{TOWER_API_ENDPOINT}/login' | grep -w JWT | rev | cut -f 1 | rev"
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