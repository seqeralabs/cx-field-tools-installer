# Missing Connection Strings Outputs Tests

Based on comprehensive analysis of the connection strings module outputs and existing test coverage after recent test additions, the following test scenarios are missing:

## Module Analysis Summary (UPDATED)

**Total outputs in module:** 16 (from outputs.tf)  
**Outputs with comprehensive tests:** 13/16 (81%)  
**Outputs with partial tests:** 1/16 (6%)  
**Outputs with no tests:** 2/16 (13%)  

## Current Test Coverage Status (UPDATED)

### ✅ FULLY TESTED OUTPUTS (13/16) 
1. **`tower_base_url`** - Basic URL construction tested
2. **`tower_server_url`** - Both secure and insecure modes tested  
3. **`tower_api_endpoint`** - Both secure and insecure modes tested
4. **`tower_db_root`** - New RDS, existing RDS, and container scenarios tested
5. **`tower_db_url`** - New RDS, existing RDS, and container scenarios tested
6. **`tower_connect_dns`** - ALB host-matching tested
7. **`tower_connect_wildcard_dns`** - Wildcard DNS construction tested
8. **`tower_connect_server_url`** - Both secure and insecure modes tested
9. **`swell_db_url`** - External and container DB scenarios tested ✅ **FIXED**
10. **`tower_redis_url`** - External and container Redis scenarios tested ✅ **FIXED**
11. **`tower_connect_redis_url`** - External and container Redis scenarios tested ✅ **FIXED**
12. **`wave_lite_db_url`** - New RDS and container DB scenarios tested ✅ **FIXED**
13. **`wave_lite_redis_url`** - External and container Redis scenarios tested ✅ **FIXED**

### 🔶 PARTIALLY TESTED OUTPUTS (1/16)
14. **`tower_wave_url`** - **CRITICAL**: Only tested in other contexts; missing dedicated flag switching tests

### ❌ COMPLETELY UNTESTED OUTPUTS (2/16)
15. **`tower_wave_url`** - **CRITICAL**: No dedicated tests for Wave service URL selection logic
16. **`tower_wave_dns`** - **MEDIUM**: No tests exist for DNS extraction

## Remaining Critical Missing Test Scenarios

### 1. Wave Service URL Tests (ONLY REMAINING MAJOR GAP)
- **`tower_wave_url`** - **CRITICAL**: Conditional logic based on `flag_use_wave_lite`
  - ❌ Missing: `flag_use_wave_lite = true` (should use `wave_lite_server_url`)
  - ❌ Missing: `flag_use_wave_lite = false` (should use `wave_server_url`)
  - ❌ Missing: URL validation and format testing
- **`tower_wave_dns`** - **MEDIUM**: Strips "https://" prefix from `tower_wave_url`
  - ❌ Missing: DNS extraction testing for both Wave and Wave-Lite URLs
  - ❌ Missing: Protocol prefix removal validation

### 2. Wave-Lite Database Tests ✅ **COMPLETED**
- **`wave_lite_db_url`** - ✅ **FULLY TESTED**
  - ✅ Container DB mode tested
  - ✅ External DB mode tested
  - ✅ Mock resource testing validated

### 3. Wave-Lite Redis Tests ✅ **COMPLETED**
- **`wave_lite_redis_url`** - ✅ **FULLY TESTED**
  - ✅ Container Redis mode tested
  - ✅ External Redis mode tested
  - ✅ `rediss://` prefix validation tested

### 4. Container Database/Redis Scenarios ✅ **COMPLETED**
- ✅ **All container mode tests now exist:**
  - ✅ `swell_db_url` with container DB
  - ✅ `tower_redis_url` with container Redis
  - ✅ `tower_connect_redis_url` with container Redis
  - ✅ All Wave-Lite outputs with container resources

### 5. Flag Combination Coverage ✅ **MOSTLY COMPLETED**
- ✅ **Database flag combinations now tested:**
  - ✅ `flag_use_container_db = true` scenarios across all DB outputs
  - ❌ Still missing: Wave-Lite with existing external DB (`flag_use_existing_external_db = true`)
- ✅ **Redis flag combinations now tested:**
  - ✅ `flag_use_container_redis = true` scenarios across all Redis outputs
  - ✅ Container Redis with various services (Tower, Connect, Wave-Lite)

## Updated Test Priority Matrix

### HIGH Priority (Only Critical Missing Functionality)
1. **`tower_wave_url`** - Wave service flag switching logic
2. **`tower_wave_dns`** - Wave DNS extraction logic

### MEDIUM Priority (Minor Missing Coverage)
3. **Wave-Lite with existing external DB** - Edge case scenario

### LOW Priority (Edge Cases)
4. **Mock vs Real Resource Testing** - Additional validation scenarios
5. **URL Protocol Edge Cases** - Advanced protocol validation tests

## Recommended Test File Structure (UPDATED)

### Create New Test File (ONLY REMAINING MAJOR TASK)
- **`test_wave_urls.py`** - Dedicated Wave service URL testing
  - `tower_wave_url` tests for Wave-Lite vs Wave URL selection
  - `tower_wave_dns` tests for DNS extraction

### Minor Additions to Existing Files
- **`test_db_strings.py`** - Add Wave-Lite with existing external DB test (edge case)

## Summary of Required Test Additions (UPDATED)

**New tests needed:** 3-4 test functions (down from 15+)  
**New test file needed:** 1 (`test_wave_urls.py`)  
**Existing files to expand:** 1 (minor addition to `test_db_strings.py`)  
**Flag combinations to test:** 2-3 additional scenarios (down from 8+)  

## Implementation Priority Order (UPDATED)
1. **Immediate**: Create `test_wave_urls.py` with Wave service URL tests
2. **Optional**: Add Wave-Lite with existing external DB edge case test  