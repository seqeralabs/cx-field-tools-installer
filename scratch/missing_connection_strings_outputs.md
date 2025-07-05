# Missing Connection Strings Outputs Tests

Based on comprehensive analysis of the connection strings module outputs and existing test coverage, the following test scenarios are missing:

## Module Analysis Summary

**Total outputs in module:** 16 (from outputs.tf)  
**Outputs with comprehensive tests:** 8/16 (50%)  
**Outputs with partial tests:** 3/16 (19%)  
**Outputs with no tests:** 5/16 (31%)  

## Current Test Coverage Status

### ✅ FULLY TESTED OUTPUTS (8/16)
1. **`tower_base_url`** - Basic URL construction tested
2. **`tower_server_url`** - Both secure and insecure modes tested  
3. **`tower_api_endpoint`** - Both secure and insecure modes tested
4. **`tower_db_root`** - New RDS and existing RDS scenarios tested
5. **`tower_db_url`** - New RDS and existing RDS scenarios tested
6. **`tower_connect_dns`** - ALB host-matching tested
7. **`tower_connect_wildcard_dns`** - Wildcard DNS construction tested
8. **`tower_connect_server_url`** - Both secure and insecure modes tested

### 🔶 PARTIALLY TESTED OUTPUTS (3/16)
9. **`swell_db_url`** - Only external DB; missing container DB scenarios
10. **`tower_redis_url`** - Only external Redis; missing container Redis scenarios
11. **`tower_connect_redis_url`** - Only external Redis; missing container Redis scenarios

### ❌ COMPLETELY UNTESTED OUTPUTS (5/16)
12. **`tower_wave_url`** - **CRITICAL**: No tests exist for Wave service URL selection
13. **`tower_wave_dns`** - **MEDIUM**: No tests exist for DNS extraction  
14. **`wave_lite_db_url`** - **HIGH**: No tests exist for Wave-Lite database URLs
15. **`wave_lite_redis_url`** - **HIGH**: No tests exist for Wave-Lite Redis URLs

## Critical Missing Test Scenarios

### 1. Wave Service URL Tests (COMPLETE GAP)
- **`tower_wave_url`** - **CRITICAL**: Conditional logic based on `flag_use_wave_lite`
  - ❌ Missing: `flag_use_wave_lite = true` (should use `wave_lite_server_url`)
  - ❌ Missing: `flag_use_wave_lite = false` (should use `wave_server_url`)
  - ❌ Missing: URL validation and format testing
- **`tower_wave_dns`** - **MEDIUM**: Strips "https://" prefix from `tower_wave_url`
  - ❌ Missing: DNS extraction testing for both Wave and Wave-Lite URLs
  - ❌ Missing: Protocol prefix removal validation

### 2. Wave-Lite Database Tests (COMPLETE GAP)
- **`wave_lite_db_url`** - **HIGH**: No tests exist
  - ❌ Missing: Container DB mode (`flag_use_container_db = true`)
  - ❌ Missing: External DB mode (`flag_create_external_db = true`)
  - ❌ Missing: Mock vs real resource testing
  - ❌ Missing: Database connection string format validation

### 3. Wave-Lite Redis Tests (COMPLETE GAP)
- **`wave_lite_redis_url`** - **HIGH**: No tests exist
  - ❌ Missing: Container Redis mode (`flag_use_container_redis = true`)
  - ❌ Missing: External Redis mode (`flag_create_external_redis = true`)
  - ❌ Missing: `rediss://` prefix validation (secure Redis)
  - ❌ Missing: Mock vs real resource testing

### 4. Container Database/Redis Scenarios (MAJOR GAP)
- **Missing container mode tests for:**
  - `swell_db_url` with container DB
  - `tower_redis_url` with container Redis
  - `tower_connect_redis_url` with container Redis
  - All Wave-Lite outputs with container resources

### 5. Flag Combination Coverage Gaps
- **Database flag combinations not tested:**
  - `flag_use_container_db = true` scenarios across all DB outputs
  - Wave-Lite with existing external DB (`flag_use_existing_external_db = true`)
- **Redis flag combinations not tested:**
  - `flag_use_container_redis = true` scenarios across all Redis outputs
  - Container Redis with various services (Tower, Connect, Wave-Lite)

## Test Priority Matrix

### HIGH Priority (Critical Missing Functionality)
1. **`tower_wave_url`** - Wave service flag switching logic
2. **`wave_lite_db_url`** - Wave-Lite database connection testing
3. **`wave_lite_redis_url`** - Wave-Lite Redis connection testing

### MEDIUM Priority (Important Missing Coverage)
4. **`tower_wave_dns`** - Wave DNS extraction logic
5. **Container DB scenarios** - All outputs with container database mode
6. **Container Redis scenarios** - All outputs with container Redis mode

### LOW Priority (Edge Cases)
7. **Mock vs Real Resource Testing** - Validation of `use_mocks` flag behavior
8. **URL Protocol Edge Cases** - Advanced protocol validation tests

## Recommended Test File Structure

### Create New Test File
- **`test_wave_urls.py`** - Dedicated Wave service URL testing
  - `tower_wave_url` tests for Wave-Lite vs Wave URL selection
  - `tower_wave_dns` tests for DNS extraction

### Expand Existing Test Files
- **`test_db_strings.py`** - Add Wave-Lite database tests
  - `wave_lite_db_url` tests for various database modes
  - Container DB scenarios for all database outputs
- **`test_redis_strings.py`** - Add Wave-Lite Redis tests
  - `wave_lite_redis_url` tests for various Redis modes  
  - Container Redis scenarios for all Redis outputs

## Summary of Required Test Additions

**New tests needed:** 15+ test functions  
**New test file needed:** 1 (`test_wave_urls.py`)  
**Existing files to expand:** 2 (`test_db_strings.py`, `test_redis_strings.py`)  
**Flag combinations to test:** 8+ additional scenarios  

## Implementation Priority Order
1. **Immediate**: Create `test_wave_urls.py` with Wave service URL tests
2. **Next**: Add Wave-Lite database tests to `test_db_strings.py`  
3. **Next**: Add Wave-Lite Redis tests to `test_redis_strings.py`
4. **Later**: Add comprehensive container DB/Redis scenario coverage to existing tests  