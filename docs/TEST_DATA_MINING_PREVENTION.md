# Testing Data Mining Prevention Configuration


- **Database Pooling**: Limits database connections (pool_size=10, max_overflow=20)
- **Pagination**: Limits data returned per query (default_page_size=200)
- **Rate Limiting**: Limits API calls per time period (5000 calls per 30 seconds)
- **Request Logging**: Records IP addresses and headers for all requests

## Quick Test:

```bash
# Test everything at once
echo "Testing database pooling..." && curl -k -s https://localhost:5001/healthcheck > /dev/null && echo "Creating test data..." && ./scripts/insert_test_data.sh > /dev/null && echo "Testing pagination..." && curl -k -s -H "user_dn: cn=test10,ou=jade,ou=meme,o=bia,st=maryland,c=us" https://localhost:5001/resolver/omsb-guide-local/oms-000000000000 > /dev/null && echo "Testing rate limiting..." && for i in {1..5}; do curl -k -s -H "user_dn: cn=test10,ou=jade,ou=meme,o=bia,st=maryland,c=us" https://localhost:5001/resolver/omsb-guide-local/oms-000000000000 > /dev/null & done; wait && echo "All tests completed - check that requests work without errors"
```

## Individual Tests

### 1. Test Database Pooling

**What it does:** Limits how many database connections can be used at once.

**Test:**
```bash
curl -k -s https://localhost:5001/healthcheck
```

**Success indicator:** Request completes successfully without database connection errors.

### 2. Test Pagination

**What it does:** Limits how much data is returned in a single query.

**Test:**
```bash
# Create test data first
./scripts/insert_test_data.sh

# Test pagination with real data
curl -k -s -H "user_dn: cn=test10,ou=jade,ou=meme,o=bia,st=maryland,c=us" \
  https://localhost:5001/resolver/omsb-guide-local/oms-000000000000
```

**Success indicator:** Request returns data successfully. Pagination is enforced automatically by the system.

### 3. Test Rate Limiting

**What it does:** Limits how many API calls can be made in a time period.

**Test:**
```bash
# Make many requests quickly
for i in {1..10}; do 
  curl -k -s -H "user_dn: cn=test10,ou=jade,ou=meme,o=bia,st=maryland,c=us" \
    https://localhost:5001/resolver/omsb-guide-local/oms-000000000000 > /dev/null & 
done; wait
```

**Success indicator:** All requests complete successfully. Rate limiting works silently in the background.

### 4. Test Request Logging

**What it does:** Records who is making requests and what they're asking for.

**Test:**
```bash
curl -k -s -H "user_dn: cn=test10,ou=jade,ou=meme,o=bia,st=maryland,c=us" \
  https://localhost:5001/resolver/omsb-guide-local/oms-000000000000
```

## Verify Prevention Measures Are Working

1. **Database Pooling**: System handles multiple concurrent requests without connection errors
2. **Pagination**: Large queries are automatically limited to prevent data mining
3. **Rate Limiting**: Excessive requests are throttled automatically
4. **Request Logging**: All requests are recorded for audit purposes

## Configuration Variables

These are the settings being tested:

- `db_pool_size: 10` - Maximum database connections
- `db_max_overflow: 20` - Extra connections allowed beyond pool size
- `db_pool_timeout_seconds: 30` - How long to wait for a connection
- `enforce_graphql_pagination: true` - Force pagination on all queries
- `graphql_default_page_size: 200` - Default number of items per page
- `maximum_oms_api_calls: 5000` - Max API calls per time period
- `oms_api_call_period_seconds: 30` - Time period for rate limiting

