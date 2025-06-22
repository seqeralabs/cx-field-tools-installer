# Test Cases

[] - Custom Resource Naming vs default random pet
[] - Resource name vs AWS resource length limits and character acceptance

[] - DB connection strings:
    [] - `flag_create_external_db = true`
        [x] - Check `tower_db_url`
        [x] - Check `swell_db_url`
        [x] - Check `wave_lite_db_url`
    [] - `flag_use_existing_external_db = true`
        [x] - Check `tower_db_url`
        [x] - Check `swell_db_url`
        [] - Check `wave_lite_db_url` (GAP)
    [] - `flag_use_container_db = true`

- [] - VPC
    - Various regions and combinations of AZs
    - Existing ID?

? What to do about existing in-account values (eg. EBS KMS key, ALB cert?)
? Possible to parallelize code installation base / memoize calls to run tests in parallel?