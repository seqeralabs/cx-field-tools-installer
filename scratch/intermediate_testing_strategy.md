# Intermediate testing strategy

## Desire
1. Test DB connection values against local MySQL and Postgres containers so we don't need to spin up a stack in AWS.


## Considerations
`terraform apply -target=null_resource.regenerate_config_files_from_data` is a guaranteed way to get configured `assets/target` files but it generates too much intermediate infrastructure.

Testing container connections locally means I dont need to worry about instantiating an EC2 or managing an SSH connection. However, e2e testing is still going to require me to spin up a full stack. Is intermediate worth the effort? Maybe I just do local and remote? 

My connection_strings module has mocking mode. Can I use that to avoid needing to generate assets?


## Implementation Options
O3 suggests using Pytest & testcontainers. TBD if this is viable or useful.

```python
# tests/test_populate_rds.py
import os, subprocess, textwrap, mysql.connector
from testcontainers.mysql import MySqlContainer

def test_populate_external_db(tmp_path):
    sql = "CREATE DATABASE foo; USE foo; CREATE TABLE bar(id INT);"
    (tmp_path/"tower.sql").write_text(sql)

    with MySqlContainer("mysql:8.0") as mysql:
        # env vars consumed by the Ansible snippet
        env = {
            **os.environ,
            "DB_POPULATE_EXTERNAL_INSTANCE": "true",
            "DB_URL": mysql.get_connection_url().split("@")[1].split("/")[0],  # host:port
            "app_name": "test",
            # bypass SSM by hard-coding creds
            "db_master_user": mysql.MYSQL_USER,
            "db_master_password": mysql.MYSQL_PASSWORD,
        }

        # run just that task file via ansible-playbook
        play = textwrap.dedent(f"""
        - hosts: localhost
          connection: local
          tasks:
            - include_tasks: assets/src/ansible/02_update_file_configurations.yml.tpl
        """)
        playfile = tmp_path / "play.yml"
        playfile.write_text(play)

        subprocess.run(
            ["ansible-playbook", str(playfile)],
            check=True,
            env=env,
            cwd=tmp_path,
        )

        # assert SQL really executed
        conn = mysql.get_connection_driver()
        cur = conn.cursor()
        cur.execute("SHOW DATABASES LIKE 'foo'")
        assert cur.fetchone()
```

GW Musings (July 6/25):
- Forgo local containers and bring up minimal infra in AWS (e.g. SSM entries & small EC2 in public subnet with SSH access) -- should be fast(ish) to deploy and not need all the extra bells and whistles that take time to procure (EICE, external instances).
- Need to break up `010_prepare_config_files.tf` into small chained chunks. Split dependent-on-values-from-procured-infra from can-be-configured-solely-based-on-tfvars files.
- Use YAML tool to extract database and redis containers only -- no point downloading beefier containers like Seqera images when they arent needed at this point.
- setup for test will involve:
    - Creating testing secrets (SSM)
    - copying config files to machine

## Questions
1. Is this worthh it? Redeploying containers to EC2 is pretty fast, is it worth the complication of local containers?

2. How do I mock the wave_lite_secrets terraform resource using by SALT?