# Test Cases

[] - Custom Resource Naming vs default random pet
[] - Resource name vs AWS resource length limits and character acceptance

[] - DB connection strings:
    [x] - `flag_create_external_db = true`
        [x] - Check `tower_db_url`
        [x] - Check `swell_db_url`
        [x] - Check `wave_lite_db_url`
        [x] - Check `tower_db_root`
    [-] - `flag_use_existing_external_db = true`
        [x] - Check `tower_db_url`
        [x] - Check `swell_db_url`
        [-] - Check `wave_lite_db_url` (GAP)
        [x] - Check `tower_db_root`
    [] - `flag_use_container_db = true`
        [] - Check `tower_db_url`
        [] - Check `swell_db_url`
        [] - Check `wave_lite_db_url`
    - [] generated connection string?

[] - Redis strings
    [] - `flag_create_external_redis = true`
        [x] - Check `tower_redis_url`
        [x] - Check `wave_lite_redis_url`
        [x] - Check `tower_connect_redis_url`
    [] - `flag_use_container_redis = true`
        [] - Check `tower_redis_url`
        [] - Check `wave_lite_redis_url`
        [] - Check `tower_connect_redis_url`

[] - URLs
    - Secure
        - tower
        - connnect
    - Insecure
        - tower
        - connnect
    - DNS
        - domain
        - wildcard


- [] - VPC
    - Various regions and combinations of AZs
    - Existing ID?

? What to do about existing in-account values (eg. EBS KMS key, ALB cert?)
? Possible to parallelize code installation base / memoize calls to run tests in parallel?