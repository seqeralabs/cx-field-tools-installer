# Test Case Architecture Documentation

## Overview

These tests exist to validate that the resources (_configuration & AWS resources_) produced by Terraform align to expected behaviours, in two ways:


## Architecture Components -- Unit Testing

### 1. Test Cases (`tests/unit/`)

Assets are produced via Terraform commands: `terraform plan` and `terraform console -target=...`. Resulting files & outputs are evaluated through several methods:

- **Terraform outputs** are extracted from the JSONified plan and compared against hardcoded values.
- **Seqera Platform configuration files** are produced and compared against baseline and test-specific assertions.
- **Testcontainers** are used to run a subset of SP configuration files (e.g. `.sql` files) to validate successful execution. 


### 2. Test Case Inputs
#### Tfvars
Testcase inputs are merged from a variety of sources:

1. **Base terraform.tfvars**: This is copied directly from `templates/TEMPLATE_terraform.tfvars` to ensure testcase start from the same file that we tell implementations to use.
2. **Base terraform.tfvars overrides**: This file is generated fresh for each testrun via `tests/datafiles/generate_core_data.sh`. It produces the file `tests/datafiles/base-overrides.auto.tfvars`, which contains a subset of terraform values which must be populated with real values in order for subsequent terraform commands to succeed.
3. **Testcase-level tfvars overrides**: These are set in each testcase, superceding base values in other to implement an edgecase.

The three sources work together as follows:

1. At the start of the testing session, the pytest fixture `session_setup` executes:

    1. The root-level `terraform.tfvars` (_used by Seqera resources for real deployments_) is backed up and moved out of the project root.

    2. The `tests/datafiles/generate_core_data.sh` executes, creating a fresh copy of `tests/datafiles/terraform.tfvars` and `tests/datafiles/base-overrides.auto.tfvars`. Both files contain testing-appropriate data.

    3. The newly-generated files are copied into the project root.

2. At the beginning of each testcase, the provided `tf_modifiers` values is feed to the `prepare_plan` helper function:

    1. The `tf_modifiers` content is written to file `override.auto.tfvars` in the project root.

    2. `terraform plan` is executed.

    3. `terraform plan` results are converted to JSON and cached.

The tfvars file naming is designed to leverage Terraform's [Variable Definition Precedence](https://developer.hashicorp.com/terraform/language/values/variables#variable-definition-precedence):

- The testcase-specific overrides are lexically-named to supercede base overrides.
- The base overrides are lexically-named to supercede the cloned-from-template tfvars.
- The result is a single fused layer of terraform inputs which minimizes the amount of entries requiring explicit definition in the individual testcases.

To speed up `n+1` testing, a caching mechanism is used (_fulsome details in the Performance section_).


#### Secrets
The `tests/datafiles/generate_core_data.sh` also generates secrets via `tests/datafiles/generate_testing_secrets.sh`. Results are written to `tests/datafiles/secrets/*.json`files.

The scripts have the ability to push secrets to the appropriate SSM location, but this has been disabled to speed up unit testing (_more on this below in the performance section_). If / when secrets are needed for local tests, the SSM sourcing can be emulated by simply reading the appropriate key from the appropriate secrets file. 


### 2. Expected Results (`tests/datafiles/expected_results/`)
Establishes a baseline for expected end state against which the tests can be compared. This is done in two ways:

1. **Pre-generated end state files** (e.g `tests/datafiles/expected_results/expected_sql/*.sql`)

    These are fully rendered reference files used for page-to-page comparison. 
    
    Given the dynamic permutations possible within this solution and required upkeep of file accuracy, I prefer targeted line-by-line assertions and over full-page comparisons. However, some configuration files (_`.sql` files in particular_) are much easier to validate via full page comparions.

    Testcases that use this methodology share the same starting logic but differ within the assertion phase (_loading reference document content rather than granular key-value assertions_). 

2. **Per configuration file key-value expectations** (`tests/datafiles/expected_results/expected_results.py`)

    This implementation is more complicated than the standard key-value assertion, but meant to be modular and extensible. Here's how it works:

    - Each configuration file has two associated functions: 
        - One covers expected content when all Seqera Platform services are active; 
        - The other covers expected content when the services are inactive (_i.e. only the core SP is active_).

    - Each function contains a dictionary with 2 sub-keys, containing baseline expectations:
        ```python
        # EXAMPLE: tower.env for an implementation with active features.
        def generate_tower_env_entries_all_active(overrides={}):
            baseline: {
                "present": {
                    # These define the keys and values expected to be found within a generated tower_env file.
                    "KEY_A": "VALUE_A",
                },
                "omitted": {
                    # These define the keys and values NOT expected to be found within a generated tower_env file.
                    "KEY_B": "VALUE_B",
                }
            }
        ```

    - A set of **overrides** can be passed during the function call. These come from the invoking testcase and define expected baseline deltas (_resulting from the different **terraform variables** used for that testcase_). Any assertion passed in the override object is removed from the baseline and replaced with the override value. Essentially, the two layers are fused into a single testcase-appropriate assertion set.

    - The nature of the keys can differ depending on the file being assessed:
        - Keys tied to `.env` files are treated as plain key-value split by a `=`.
        - Keys tied to `.yml` files are treated as YAMLpaths.

    - To simplify content management, a **master assertion dictionary** is returned (_either active or disabled flavour_). Its top-level keys are named the same as the generated files, and its values are the fused assertion layer for that file.

        ```python
        # Example: Function that generates the master assertion dictionary (_active features_)
        def generate_assertions_all_active(template_files, overrides):
            entries = {
                "tower_env"             : generate_tower_env_entries_all_active(overrides["tower_env"]),
                "tower_yml"             : generate_tower_yml_entries_all_active(overrides["tower_yml"]),
                ...
        ```


### Implementation
In order for tests to provide continual ongoing value, the following criteria must be met:

- Have a minimal code line footprint.
- Be easy to update
- Be easy to extend
- Be fast to run

To achieve these goals and maintain a simple-ish outward interface, a moderately complex implementation was required. This section covers those details.

#### 1. Common Testcase Boilerplate
Each testcase function is responsible for:

1. Defining tfvars overrides (_if necessary_).
2. Generating a JSONified `terraform plan`.
3. Defining a minimal set of impacted Seqera Plaform configuration files.
4. Defining necessary assertions for the generated set of files.
5. Executing the assertion set (_the phase varies depending if it's granular kv comparison, full-page comparison, or testcontainer verification_).


#### 2. Configuration (`tests/utils/config.py`)
This is a centralized source for making filepaths and core structures as DRY as possible. 

- Defines file paths for test data, cache directories, secrets, etc.
- Defines core data structures used to store testcase file content and assertions.
- Sets flags that control test behavior (_which are themselves controleld via environment variables (e.g., KITCHEN_SINK mode)_).

Two settings in particular require call out:

1. **`all_template_files`**: is a top-level dictionary from which other structures are derived:

    - Its keys identify a discrete Seqera Platform configuration file.
    - Its values identify:
        - The expected file extension.
        - The utility helper function to use to read the content of the generated file (e.g. plain text, YAML, JSON).
        - The content of the source file (_this key likely to be phased out now that there is a `filepath` key_).
        - The location of the cached file on the filesystem.
        - The validation technique that should be used to execution assertions (e.g. granular kv, full-page comparison, YAMLPath). 

    ```python
    all_template_files = {
        "tower_env": {
            "extension"         : ".env", 
            "read_type"         : parse_key_value_file,
            "content"           : "",
            "filepath"          : "",
            "validation_type"   : "kv",
        },
        ...
    ```

2. **`KITCHEN_SINK`**: is an environment variables modifier that will generate every configuration file for every testcase.

    Although the current solution (`terraform plan / terraform console`) is much faster than its original implementation (`terraform apply / terraform destroy`), and caching makes `n+1` execution extremely fast, there IS a cost for first-time generation (_up to several minutes_). As a result, most testcases are scoped to produce only those files required for test-specific validations (_e.g. why produce a full set of files if the test targets a password in a single `.sql` file?_).

    The downside of targeting testing is that it won't catch bugs in files that are not included in the minimal set. As a result, at least one testing run should force all testcases to produce a full set of configurations and run the entire test suite. This is what `KITCHEN_SINK` does.

    ```bash
    # Tests a limited set of assertions tied to Wave-specific configurations.
    pytest tests/unit/config_files/test_config_file_content.py::test_seqera_hosted_wave_active

    # Generates a full set of configuration files using the testcase-specific tfvars overrides, and runs a full set of assertions
    # including the specific Wave assertion modifiers identified in this testcase.
    KITCHEN_SINK=true pytest tests/unit/config_files/test_config_file_content.py::test_seqera_hosted_wave_active
    ``` 




### 3. Utility Functions (`tests/utils/local.py`)
- `prepare_plan()`: Executes Terraform plan with caching to speed up repeated tests
- `generate_tc_files()`: Creates interpolated configuration files from Terraform templates
- `verify_all_assertions()`: Validates generated files against expected assertions



## Function Call Flow

```
test_baseline_alb_all_enabled()
    │
    ├─> prepare_plan(tf_modifiers)
    │     ├─> get_cache_key()                    # Generate hash for caching
    │     ├─> check_aws_sso_token()              # Verify AWS credentials
    │     ├─> run_terraform_plan()               # Execute terraform plan
    │     └─> read_json(tfplan.json)             # Load plan output
    │
    ├─> assertion_modifiers_template()           # Initialize empty modifiers
    │
    ├─> generate_tc_files(plan, desired_files)
    │     ├─> generate_namespaced_dictionaries() # Convert plan to namespaces
    │     │     ├─> read secrets from JSON files
    │     │     └─> create SimpleNamespace objects
    │     │
    │     └─> generate_interpolated_templatefiles()
    │           ├─> prepare_templatefile_payload()
    │           │     ├─> read_json(009_define_file_templates.json)
    │           │     └─> sub_templatefile_inputs()
    │           │           └─> replace_vars_in_templatefile()
    │           │
    │           └─> write_populated_templatefile()
    │                 └─> terraform console execution
    │
    ├─> generate_assertions_all_active(tc_files, assertion_modifiers)
    │     ├─> generate_tower_env_entries_all_active()
    │     ├─> generate_wave_lite_yml_entries_all_active()
    │     └─> ... (other file-specific generators)
    │
    └─> verify_all_assertions(tc_files, tc_assertions)
          └─> assert_present_and_omitted()
                ├─> assert_kv_key_present()      # For .env files
                ├─> assert_yaml_key_present()    # For YAML files
                └─> assert_sql_key_present()      # For SQL files
```

## Architecture Components -- Remote Testing
Current as of August 2025, verification on actual infrastructure is done via manual deployment & verification. This is not efficient or scaleable.

Intended future state solution plans to leverage `terraform` and `GitHub Actions`. Implementation TBD.


## Key Concepts

### Terraform Variable Overrides
Test cases use multi-line strings to define Terraform variable overrides that configure the infrastructure scenario:
```python
tf_modifiers = """
    flag_create_external_db         = true
    flag_use_existing_external_db   = false
    flag_use_container_db           = false
"""
```

### Assertion Modifiers
Each test case can customize the baseline assertions by providing overrides:
```python
assertion_modifiers["tower_env"] = {
    "present": {
        "TOWER_DB_URL": "jdbc:mysql://mock.tower-db.com:3306/tower"
    },
    "omitted": {}
}
```

### Caching Strategy
- **Plan Cache**: Terraform plans are cached based on a hash of variable overrides
- **Template Cache**: Generated configuration files are cached by content hash
- Cache directories: `tests/.plan_cache/` and `tests/.templatefile_cache/`

### File Validation Types
Different file formats require different validation approaches:
- **Key-Value (.env)**: Direct dictionary comparison
- **YAML**: YAMLPath library for nested key validation
- **SQL**: Full file content comparison

## Adding a New Test Case

### Step 1: Define the Test Case
Add to `tests/unit/config_files/test_config_file_content.py`:

```python
@pytest.mark.local
@pytest.mark.custom_scenario
def test_external_smtp_with_studios(session_setup):
    """
    Scenario:
        - External SMTP configuration
        - Data Studios enabled with custom templates
    """
    
    tf_modifiers = """
        flag_use_aws_ses_iam_integration = false
        flag_use_existing_smtp           = true
        smtp_host                        = "smtp.example.com"
        smtp_port                        = "587"
        flag_enable_data_studio          = true
        data_studio_custom_templates     = true
    """
    plan = prepare_plan(tf_modifiers)
    
    desired_files = ["tower_env", "data_studios_env"]
    assertion_modifiers = assertion_modifiers_template()
    tc_files = generate_tc_files(plan, desired_files, sys._getframe().f_code.co_name)
    
    # Define custom assertions
    assertion_modifiers["tower_env"] = {
        "present": {
            "TOWER_SMTP_HOST": "smtp.example.com",
            "TOWER_SMTP_PORT": "587",
            "TOWER_ENABLE_AWS_SES": "false"
        },
        "omitted": {}
    }
    
    assertion_modifiers["data_studios_env"] = {
        "present": {
            "CUSTOM_TEMPLATES_ENABLED": "true"
        },
        "omitted": {}
    }
    
    tc_assertions = generate_assertions_all_active(tc_files, assertion_modifiers)
    verify_all_assertions(tc_files, tc_assertions)
```

### Step 2: Extend Expected Results (if needed)
If the scenario requires new baseline assertions, add to `tests/datafiles/expected_results/expected_results.py`:

```python
def generate_tower_env_entries_external_smtp(overrides={}):
    """Generate assertions for external SMTP configuration."""
    baseline = {
        "present": {
            "TOWER_ENABLE_AWS_SES": "false",
            "TOWER_SMTP_HOST": "smtp.example.com",
            "TOWER_SMTP_PORT": "587",
            "TOWER_SMTP_AUTH": "true",
            "TOWER_SMTP_STARTTLS_ENABLE": "true"
        },
        "omitted": {
            "AWS_SES_CONFIGURATION": ""
        }
    }
    baseline = purge_baseline_of_specified_overrides(baseline, overrides)
    return {**baseline, **overrides}

# Add new generator to the main assertion function
def generate_assertions_external_smtp(template_files, overrides):
    entries = {
        "tower_env": generate_tower_env_entries_external_smtp(overrides["tower_env"]),
        # ... other file generators
    }
    return entries
```

### Step 3: Run the Test
```bash
# Run specific test
pytest tests/unit/config_files/test_config_file_content.py::test_external_smtp_with_studios -v

# Run with custom marker
pytest -m "custom_scenario" -v
```

## Performance Considerations

### Caching Benefits
- First test run: ~30 seconds (full Terraform plan)
- Subsequent runs: ~4 seconds (cached plan reuse)
- Cache invalidation: Based on tfvars content hash

### Optimization Strategies
1. Use `desired_files` to generate only necessary configuration files
2. Leverage pytest markers to run specific test subsets
3. Set `KITCHEN_SINK=false` to minimize file generation

## Troubleshooting

### Common Issues

1. **Cache Inconsistency**
   ```bash
   rm -rf tests/.plan_cache tests/.templatefile_cache
   ```

2. **AWS SSO Token Expiration**
   The framework automatically detects and prompts for re-authentication

3. **Assertion Failures**
   Check the specific validation type (kv/yaml/sql) and ensure proper formatting

### Debug Output
Enable verbose pytest output:
```bash
pytest -v -s --tb=short
```

## Best Practices

1. **Test Organization**
   - Group related scenarios using pytest markers
   - Use descriptive test function names
   - Document scenario assumptions in docstrings

2. **Assertion Management**
   - Start with baseline assertions (all_active/all_disabled)
   - Apply minimal overrides for clarity
   - Separate "present" vs "omitted" assertions clearly

3. **Performance**
   - Use plan caching for iterative development
   - Generate only necessary files per test
   - Clear cache when switching branches

## Extending the Framework

### Adding New File Types
1. Define the file in `tests/utils/config.py` configuration lists
2. Create generator function in `expected_results.py`
3. Add appropriate assertion function in `local.py`
4. Update `verify_all_assertions()` to handle the new validation type

### Custom Validation Logic
Extend `assert_present_and_omitted()` in `tests/utils/local.py`:
```python
elif type == "custom_format":
    assert_custom_format_present(entries["present"], file)
    assert_custom_format_omitted(entries["omitted"], file)
```

## Summary

The testing framework provides a structured approach to validate Terraform-generated configuration files. While the internal mechanics are complex (involving Terraform plan parsing, template interpolation, and multi-format validation), the test case interface remains relatively simple: define Terraform overrides, specify assertion modifiers, and verify results.

For non-technical users, focus on:
1. Copying existing test patterns
2. Modifying Terraform variable overrides
3. Adjusting assertion modifiers for expected values
4. Running tests with appropriate pytest markers

The framework handles the complex transformation pipeline automatically, allowing test authors to concentrate on defining scenarios and expected outcomes.
