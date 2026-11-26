# (Optional) Crypto Secret Rotation

This page describes how to rotate the crypto secret of an already-deployed Seqera Platform instance via the [cx-field-tools-installer](https://github.com/seqeralabs/cx-field-tools-installer) project.

**NOTE: _This activity is not required for first-time deployments._**

The crypto secret (`tower.crypto.secretKey`) encrypts the credentials and pipeline secrets that Platform stores in its database. Replacing it without running a rotation leaves every stored credential unreadable, and pipeline launches fail with `javax.crypto.BadPaddingException`. A rotation gives Platform both the previous and the new key. When the `cron` container starts, it decrypts each record with the previous key and re-encrypts it with the new one. The `backend` container can read records encrypted under either key while this runs.

Official Seqera documentation: [Secret key rotation](https://docs.seqera.io/platform-enterprise/enterprise/configuration/overview#secret-key-rotation).


## Steps
1. **Mandatory Before Anything Else**

    1. Read the official Seqera documentation about this feature (link above).
    1. Backup your existing database before implementing **any** change.
    1. Capture the existing crypto secret and keep it with your database backups. Credentials in any backup taken before the rotation can only be decrypted with this key, so keep it for as long as you keep those backups.
    1. Initiate an outage via `docker compose down`. Keep users off the instance until step 3 confirms the rotation has finished. A credential or pipeline secret that is created or edited after `backend` starts but before `cron` begins the rotation is stored in a state the rotation cannot read.

2. **Prepare Keys in SSM**

    1. In the omnibus file:
        1. In line with all the other keys, add an entry that holds the previous key value (_i.e. the value currently defined in the `TOWER_CRYPTO_SECRET` block_):
            ```json
            "TOWER_CRYPTO_PREVIOUS_SECRET": {
                "ssm_key": "/config/<YOUR_APP_NAME>/tower/secret-rotation/previous-key",
                "value": "<POPULATE_WITH_CURRENT_VALUE_OF_SSM_KEY: /config/<YOUR_APP_NAME>/tower/crypto/secretKey>"
            },
            ```
        1. In line with all the other keys, add an entry activating the key rotation:
            ```json
            "TOWER_CRYPTO_ROTATE_KEYS": {
                "ssm_key": "/config/<YOUR_APP_NAME>/tower/secret-rotation/enabled",
                "value": "true"
            },
            ```

        1. (Optional) In line with all the other keys, add an entry specifying how many records the rotation processes per batch (defaults to `50`):
            ```json
            "TOWER_CRYPTO_ROTATE_CHUNK_SIZE": {
                "ssm_key": "/config/<YOUR_APP_NAME>/tower/secret-rotation/chunk-size",
                "value": "50",
                "description": "The number of records to extract in chunks until all secrets and credentials are processed. Only applied if key rotation is enabled."
            },
            ```

        1. Double-check that you updated `<YOUR_APP_NAME>` to your own installation's name.
        1. Update `TOWER_CRYPTO_SECRET` entry's `value` to new desired key.

    2. Delete the standalone SSM crypto secret key:
        1. Delete `/config/<YOUR_APP_NAME>/tower/crypto/secretKey`

            This ensures the key will be recreated with the new value.

3. **Initiate Key Rotation**

    1. Start the Seqera Platform instance with `make apply`. This recreates the standalone SSM keys from the omnibus file and restarts the containers.

    1. Verify that the rotation started. On the EC2 instance, check the `cron` container log:
        ```bash
        cd /home/ec2-user
        docker compose logs cron | grep -i "rotation"
        ```

        A rotation that has started logs:
        ```
        Starting encryption key rotation process
        ```

        If the log shows `Pre-check of encryption key rotation process failed` instead, the rotation did not run. Check the message that follows it:

        | Message | Likely cause |
        | ------- | ------------ |
        | `Secret rotation is enabled, but the previous key was not provided` | The `previous-key` SSM parameter is missing, or its path doesn't match your app name. |
        | `Current encryption key and previous encryption key of secret cannot be the same` | `TOWER_CRYPTO_SECRET` still holds the old value, or the standalone `crypto/secretKey` parameter was not recreated (step 2.2). |
        | `Previous crypto key hash '...' does not match the current key hash` | `previous-key` is not the key the database is currently encrypted with. For example, an older key was used on a second rotation. |
        | `... does not match the promoting key hash` or `... does not match the retiring key hash` | A key was changed while a rotation was in progress. Restore the values used when it started. |
        | `The rotation process of secrets was disabled, but it didn't get to complete` | `enabled` was removed before the rotation finished. Set it back to `true`. |

    1. Wait for `cron` to complete all necessary rotation activities. A finished rotation logs:
        ```
        Finished encryption key rotation process
        ```

        Rotation normally takes seconds to a few minutes, depending on how many credentials and secrets are stored.

    1. Log in as a root user and open **Admin panel > Encryption**. Every credential and secret should be listed as rotated, with no errors. Then launch a pipeline that uses a stored credential to confirm it decrypts.

        If you have database access, the same results are in the `tw_rotation_log` table:
        ```sql
        SELECT type, COUNT(*) FROM tw_rotation_log GROUP BY type;   -- success / error / orphan
        ```

        `orphan` rows are encrypted records that aren't attached to a credential or pipeline secret, so the rotation skips them. For each `error` row, re-enter the affected credential's secret in Platform.

    1. End the outage.

4. **(Optional) Delete Rotation Keys**

    Only do this once the **Encryption** tab shows no errors. A record that failed to rotate is still encrypted with the previous key, and once the rotation keys are removed Platform can no longer read it.

    Leaving the rotation keys in place is harmless: on each later restart, `cron` logs `Encryption key rotation process completed. Please, consider disabling the process.` and does nothing else.

    1. Initiate an outage via `docker compose down`.

    1. In the omnibus file:
        1. Delete entry `TOWER_CRYPTO_PREVIOUS_SECRET`.
        1. Delete entry `TOWER_CRYPTO_ROTATE_KEYS`.
        1. Delete entry `TOWER_CRYPTO_ROTATE_CHUNK_SIZE` (if you added it).

    1. Delete standalone SSM keys:
        1. Delete SSM key `/config/<YOUR_APP_NAME>/tower/secret-rotation/previous-key`.
        1. Delete SSM key `/config/<YOUR_APP_NAME>/tower/secret-rotation/enabled`.
        1. Delete SSM key `/config/<YOUR_APP_NAME>/tower/secret-rotation/chunk-size` (if you added it).

5. **Restart Seqera Platform**

    1. Restart Seqera Platform via `docker compose up -d`.

        With the key-rotation keys no longer available, rotation activities are completely ceased.
