# (Optional) Crypto Secret Rotation

This page describes how to rotate the crypto secret of an already-deployed Seqera Platform instance via the [cx-field-tools-installer](https://github.com/seqeralabs/cx-field-tools-installer) project.

**NOTE: _This activity is not required for first-time deployments._**


## Steps
1. **Mandatory Before Anything Else**

    1. Go read the official Seqera documentation about this feature (TODO: Add link)
    1. Backup your existing database before implementing **any** change.
    1. If you have pre-existing database backups, capture the existing crypto secret and ensure you have a way to associate it with the relevant backups. 
    1. Initiate an outage via `docker compose down`.

2. **Prepare Keys in SSM**

    1. In the omnibus file:
        1. In line with all the other keys, add an entry that holds the previous key value (_i.e. the value currently defined in the `TOWER_CRYPTO_SECRET` block_):
            ```json
            "TOWER_CRYPTO_PREVIOUS_SECRET": {
		        "ssm_key": "/config/<YOUR_APP_NAME>/tower/secret-rotation/secretKey",
		        "value": "POPULATE_WITH_CURRENT_VALUE_OF_SSM_KEY: /config/tower-template/tower/crypto/secretKey"
	        },
            ```
        1. In line with all the other keys, add an entry activating the key rotation:
            ```json
            "TOWER_CRYPTO_ROTATE_KEYS": {
		        "ssm_key": "/config/<YOUR_APP_NAME>/tower/secret-rotation/enabled",
		        "value": "true"
	        },
            ```

        1. Update `TOWER_CRYPTO_SECRET` entry's `value` to new desired key.

    2. Delete the standalone crypto secret key:
        1. Delete `/config/<YOUR_APP_NAME>/tower/crypto/secretKey`

            This ensures the key will be recreated with the new value.

3. **Initiate Key Rotation**

    1. Start the Seqera Platform instance.
    1. Verify key rotation activity.
        TODO: Figure out how to determine this.
    1. Wait for `cron` container to complete all necessary rotation activities. 
        TODO: Figure out how to determine this.

4. **(Optional) Delete Rotation Keys**

    1. Key rotation 
        Initiate an outage via `docker compose down`.

    1. In the omnibus file:
        1. Delete entry `TOWER_CRYPTO_PREVIOUS_SECRET`.
        1. Delete entry `TOWER_CRYPTO_ROTATE_KEYS`.

    1. Delete standalone SSM keys:
        1. Delete SSM key `/config/<YOUR_APP_NAME>/tower/secret-rotation/secretKey`.
        1. Delete SSM key `/config/<YOUR_APP_NAME>/tower/secret-rotation/enabled`.

5. **Restart Seqera Platform**

    1. Restart Seqera Platform via `docker compose up -d`.

        With the key-rotation keys no longer available, rotation activities are completely ceased.
