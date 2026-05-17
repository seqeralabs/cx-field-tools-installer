# Test Framework Simplification Options

**Context**: The current test framework is complex and difficult to debug, particularly when `terraform console` subprocess calls fail. This document outlines simplification strategies that preserve speed and flexibility while improving maintainability.

**Key Requirements**:
1. **Speed is critical** - Test suite must remain fast (current: 3-6s cached, 6m+ uncached)
2. **Terraform console breaks most often** - Difficult to debug with no clear stack trace
3. **Stable core with extensible assertions** - Need to add assertions to existing files
4. **Open to experimental features** - But NOT resource creation (too slow, costs money)
5. **Open to dramatic refactoring** - If speed and flexibility retained

---

## Option B: Surgical Improvements (Keep Architecture, Fix Pain Points)

### Core Philosophy
Keep the fast caching + `terraform console` approach, but make it **debuggable and maintainable**.

### Key Changes

#### B1. Add Debug Mode with Full Pipeline Visibility
**Problem**: When `terraform console` fails, you can't see what was sent to it.
**Solution**: See `debug_implementation_example.md`


#### B2. Split `local.py` into Focused Modules
**Current**: 707 lines, 26 functions, mixed concerns

**Proposed Structure**:
```
tests/utils/
├── terraform/
│   ├── executor.py         # Run plan/apply/console (100 lines)
│   ├── template_engine.py  # Template interpolation (200 lines)
│   └── parser.py           # Parse JSON plans (100 lines)
├── cache/
│   ├── plan_cache.py       # Plan caching logic (100 lines)
│   └── template_cache.py   # Template caching logic (80 lines)
├── assertions/
│   ├── validator.py        # Core assertion logic (150 lines)
│   └── file_handlers.py    # Type-specific validation (100 lines)
├── config.py               # Configuration only (200 lines)
└── debug.py                # Debug utilities (50 lines)
```

**Benefit**: When debugging, you know which module to look in. Stack traces are clearer.


#### B3. Validate Each Pipeline Stage
**Add validation after each transformation**:

```python
def sub_templatefile_inputs(input_str, namespaces):
    original = input_str

    # Track what we're replacing
    replacements = {
        'module.connection_strings': [],
        'tower_secrets': [],
        'groundswell_secrets': [],
        # ...
    }

    # Do replacements and track
    result = replace_vars_in_templatefile(input_str, outputs, "module.connection_strings")
    replacements['module.connection_strings'] = find_replaced_keys(original, result)

    # VALIDATE: Did we replace everything we should have?
    remaining_placeholders = find_unreplaced_patterns(result)
    if remaining_placeholders:
        raise TemplateSubstitutionError(
            f"Failed to replace: {remaining_placeholders}\n"
            f"Available keys: {outputs.keys()}\n"
            f"Check if module output is missing from plan"
        )

    return result
```

**Benefit**: Fail early with actionable error message instead of cascading to cryptic terraform console error.

#### B4. Better Error Context for Terraform Console Failures
**Current**: Just "exit code 1"

**Proposed**:
```python
def write_populated_templatefile(outfile, payload):
    try:
        result = subprocess.run(
            ["terraform", "console"],
            input=str(payload),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        # Parse terraform's error message for common issues
        error_context = parse_terraform_error(e.stderr)

        raise TerraformConsoleError(
            f"Terraform console failed for {outfile}\n"
            f"Error: {error_context['message']}\n"
            f"Line: {error_context.get('line', 'unknown')}\n"
            f"Hint: {error_context['hint']}\n"
            f"Payload saved to: {save_failed_payload(payload)}\n"
            f"Reproduce with: terraform console < {saved_file}"
        ) from e
```

**Common error patterns to detect**:
- Missing comma → "Expected comma or closing brace"
- Unclosed quote → "Unterminated string"
- Invalid variable reference → "Unknown variable"

#### B5. Smart Cache Invalidation
**Problem**: Cache doesn't know when `.tf` files change

**Solution**: Include `.tf` file hashes in cache key:
```python
def hash_cache_key(tf_modifiers: str, qualifier: str = "") -> str:
    tfvars_content = read_file(TFVARS_BASE).strip()
    tfvars_override_content = read_file(TFVARS_BASE_OVERRIDE_DST).strip()

    # NEW: Hash all .tf files
    tf_files_hash = hash_terraform_files([
        "009_define_file_templates.tf",
        "variables.tf",
        "modules/connection_strings/**/*.tf"
    ])

    combined_content = f"{tfvars_content}\n{tfvars_override_content}\n{tf_modifiers}\n{qualifier}\n{tf_files_hash}\n"
    return hashlib.sha256(combined_content.encode("utf-8")).hexdigest()[:16]
```

**Benefit**: Cache automatically invalidates when templates change. No more manual cache deletion.

#### B6. Structured Exception Hierarchy
**Create custom exceptions** for each failure mode:

```python
# tests/utils/exceptions.py
class TestFrameworkError(Exception):
    """Base exception for test framework"""
    pass

class TerraformConsoleError(TestFrameworkError):
    """Terraform console subprocess failed"""
    pass

class TemplateSubstitutionError(TestFrameworkError):
    """Failed to replace template variables"""
    pass

class CacheCorruptionError(TestFrameworkError):
    """Cache file is invalid"""
    pass

class AssertionValidationError(TestFrameworkError):
    """Assertion failed with context"""
    def __init__(self, file_type, key, expected, actual):
        self.file_type = file_type
        self.key = key
        self.expected = expected
        self.actual = actual
        super().__init__(self._format_message())

    def _format_message(self):
        return f"""
        Assertion failed for {self.file_type}
        Key: {self.key}
        Expected: {self.expected}
        Actual: {self.actual}

        Possible causes:
        - Template substitution error
        - Stale cache (check .templatefile_cache)
        - Expected result out of sync with template
        """
```

#### B7. Add Pre-flight Checks
**Before running tests**, validate environment:

```python
# tests/conftest.py
def pytest_configure(config):
    """Run before any tests"""
    # Check terraform is initialized
    if not Path(".terraform").exists():
        raise EnvironmentError("Terraform not initialized. Run: terraform init")

    # Check required files exist
    required_files = [
        "009_define_file_templates.tf",
        "tests/datafiles/terraform.tfvars",
    ]
    for f in required_files:
        if not Path(f).exists():
            raise EnvironmentError(f"Required file missing: {f}")

    # Validate terraform config (catches syntax errors early)
    result = subprocess.run(["terraform", "validate"], capture_output=True)
    if result.returncode != 0:
        raise EnvironmentError(f"Terraform validation failed:\n{result.stderr.decode()}")
```

#### B8. Improve Assertion Error Messages
**Current**: Assertion shows diff but not context

**Proposed**:
```python
def assert_present_and_omitted(tc_files, assertions):
    for file_type, assertion in assertions.items():
        content = tc_files[file_type]["content"]

        # Check present keys
        for key, expected_value in assertion["present"].items():
            try:
                actual_value = get_value_by_path(content, key, file_type)
            except KeyError:
                raise AssertionValidationError(
                    file_type=file_type,
                    key=key,
                    expected=f"Key exists with value: {expected_value}",
                    actual="Key not found in generated file",
                    context={
                        "generated_file": tc_files[file_type]["filepath"],
                        "available_keys": list_available_keys(content, file_type),
                        "hint": "Check if templatefile substitution completed"
                    }
                )

            if actual_value != expected_value:
                raise AssertionValidationError(
                    file_type=file_type,
                    key=key,
                    expected=expected_value,
                    actual=actual_value,
                    context={
                        "generated_file": tc_files[file_type]["filepath"],
                        "template_source": "009_define_file_templates.tf:XXX",
                        "hint": f"Expected '{expected_value}' but terraform generated '{actual_value}'"
                    }
                )
```

### Option B Summary
- **Estimated Effort**: 2-3 days
- **Speed Impact**: None (might be slightly faster with better caching)
- **Debugging Improvement**: 80-90% reduction in diagnosis time

---

## Option C: Modern Tooling (Without Resource Creation)

### Core Philosophy
Replace subprocess + regex magic with proper tools, but keep local-only execution.

### Key Approach: Terraform CDK for Testing (CDKTF)

**What it is**: HashiCorp's Cloud Development Kit for Terraform - write infrastructure in Python/TypeScript, generates Terraform JSON.

**Key insight**: You can use CDKTF's Python API to:
1. Load your Terraform configuration
2. Synthesize to JSON
3. Access all values (including module outputs) programmatically
4. Render templates **without needing terraform console**

### Architecture

#### C1. Use CDKTF for Template Rendering
```python
# tests/utils/terraform/cdktf_renderer.py
from cdktf import App, TerraformStack, TerraformOutput
from cdktf_cdktf_provider_aws import provider

class TestStack(TerraformStack):
    def __init__(self, scope, id, tfvars):
        super().__init__(scope, id)

        # Load your existing .tf files
        self.load_terraform_config(".")

        # Apply tfvars overrides
        self.apply_overrides(tfvars)

        # Synthesize (doesn't create resources, just generates plan)
        self.synth()

def render_template(template_path, tfvars_overrides):
    """Render template using CDKTF (no subprocess, no regex)"""
    app = App()
    stack = TestStack(app, "test", tfvars_overrides)

    # CDKTF gives you access to ALL values including module outputs
    template_vars = {
        'tower_db_url': stack.connection_strings.tower_db_url,
        'tower_redis_url': stack.connection_strings.tower_redis_url,
        # All values available programmatically!
    }

    # Use Jinja2 for template rendering (more robust than terraform console)
    from jinja2 import Environment, FileSystemLoader
    env = Environment(loader=FileSystemLoader('assets/src'))
    template = env.get_template(template_path)
    return template.render(template_vars)
```

**Benefits**:
- No subprocess calls
- No regex substitutions
- Type-safe access to values
- Native Python error messages
- Can use proper template engine (Jinja2)

**Drawbacks**:
- Requires converting templates from HCL to Jinja2 (one-time cost)
- Adds dependency on CDKTF

#### C2. Use Terraform-JSON Library (Alternative to CDKTF)
**Alternative approach**: Use `python-terraform` + `terraform-json` libraries

```python
# tests/utils/terraform/json_renderer.py
from python_terraform import Terraform
import json

def render_template_via_plan(template_path, tfvars_overrides):
    """Use terraform plan output directly (no console needed)"""
    tf = Terraform(working_dir='.')

    # Run plan with overrides
    return_code, stdout, stderr = tf.plan(
        var=tfvars_overrides,
        out='test.tfplan',
        capture_output=True
    )

    # Convert binary plan to JSON
    tf.show(json=True, plan_file='test.tfplan')
    plan_json = json.loads(stdout)

    # Extract ALL values (including module outputs from planned_values)
    values = extract_all_values(plan_json)

    # Render template using Jinja2
    return render_jinja2_template(template_path, values)

def extract_all_values(plan_json):
    """Extract all variables, locals, and outputs from plan"""
    values = {}

    # Variables
    values.update(plan_json['variables'])

    # Outputs (including from modules!)
    # This is the key - terraform plan JSON includes module outputs
    for output_name, output_data in plan_json['planned_values']['outputs'].items():
        values[output_name] = output_data['value']

    return values
```

**Benefits**:
- Uses terraform's native plan JSON output
- Module outputs ARE available in plan JSON (just not in console!)
- No regex substitutions
- Proper template engine (Jinja2)

**Key Discovery**: `terraform show -json tfplan` includes module outputs! You don't need terraform console at all!

#### C3. Convert Templates to Jinja2
**One-time conversion** of your templates from HCL templatefile to Jinja2:

**Before** (HCL in 009_define_file_templates.tf):
```hcl
templatefile("assets/src/tower/tower.env.tpl", {
  docker_version = var.tower_container_version,
  tower_db_url = module.connection_strings.tower_db_url,
})
```

**After** (Jinja2 template):
```jinja2
{# assets/src/tower/tower.env.j2 #}
TOWER_CONTAINER_VERSION={{ docker_version }}
TOWER_DB_URL={{ tower_db_url }}
```

**Benefits**:
- More robust than HCL templates (better error messages)
- Standard template language
- Easier to debug (can test templates in isolation)

#### C4. Simplified Test Flow
```python
# tests/unit/config_files/test_config_file_content.py
from tests.utils.terraform.json_renderer import TerraformRenderer

@pytest.mark.local
def test_baseline_alb_all_enabled(session_setup):
    """Conduct baseline assertions when all SP services turned on."""

    tf_overrides = {}  # No overrides for baseline

    # NEW: Simple API, no nested function calls
    renderer = TerraformRenderer(tfvars_overrides=tf_overrides)

    # Generate files (uses cached plan if available)
    config_files = renderer.render_all([
        'tower_env',
        'docker_compose',
        'seqerakit_yml',
    ])

    # Assertions (same as before)
    assertions = generate_assertions_all_active(config_files)
    verify_all_assertions(config_files, assertions)
```

**Benefits**:
- Shallow call stack
- Clear what's happening
- Easy to debug (renderer.debug_mode = True)

#### C5. Better Error Messages Naturally
```python
class TerraformRenderer:
    def render_template(self, template_name):
        try:
            values = self.get_all_values()
            template = self.jinja_env.get_template(f"{template_name}.j2")
            return template.render(values)
        except jinja2.UndefinedError as e:
            # Jinja2 gives clear error messages
            raise TemplateRenderError(
                f"Template '{template_name}' references undefined variable: {e}\n"
                f"Available variables: {list(values.keys())}\n"
                f"Check if terraform plan includes this output"
            )
        except Exception as e:
            raise TemplateRenderError(
                f"Failed to render {template_name}: {e}\n"
                f"Enable debug mode: renderer.debug_mode = True"
            )
```

### Option C Summary
- **Estimated Effort**: 4-5 days (includes template conversion)
- **Speed Impact**: Should be similar or faster (fewer subprocess calls)
- **Debugging Improvement**: 90-95% reduction in diagnosis time
- **Long-term Maintainability**: Much better

---

## Recommendation: Hybrid Approach (B + C Lite)

Start with **Option B's debugging improvements** (1-2 days) to make your current system debuggable, THEN evaluate whether to do full Option C conversion.

### Phase 1 (Immediate - 2 days)
**Goal**: Make debugging tractable NOW

- **B1**: Add debug mode with pipeline visibility
- **B4**: Better error context for terraform console failures
- **B6**: Custom exception hierarchy
- **B7**: Pre-flight checks

**Impact**: Can immediately diagnose terraform console failures

### Phase 2 (Short-term - 1 week)
**Goal**: Improve maintainability

- **B2**: Split local.py into focused modules
- **B3**: Pipeline validation at each stage
- **B5**: Smart cache invalidation

**Impact**: Easier to maintain and extend

### Phase 3 (Future - Evaluate after Phase 1-2)
**Goal**: Eliminate the "Rube Goldberg"

- **C2**: Try using `terraform show -json` instead of terraform console
- If successful, gradually convert templates to Jinja2

**Impact**: Simpler architecture, better error messages

### Rationale
1. **Phase 1** addresses immediate pain (can't debug terraform console failures)
2. **Phase 2** improves long-term maintainability
3. **Phase 3** is optional - only if you want to eliminate subprocess complexity

---

## Next Steps

1. Review this document and decide on approach
2. If proceeding with Phase 1, prioritize:
   - B1 (debug mode) - highest ROI for debugging
   - B4 (error context) - makes failures actionable
   - B6 (exceptions) - better error propagation
3. Validate Phase 1 effectiveness before committing to Phase 2
4. Consider Phase 3 as separate project after measuring Phase 1-2 impact

---

## Key Insight: terraform show -json

The biggest discovery is that **`terraform show -json tfplan` includes module outputs**, which means you could potentially eliminate the terraform console subprocess entirely and use direct JSON parsing. This would remove the most fragile part of your current pipeline.

Worth prototyping in isolation to validate before full migration.
