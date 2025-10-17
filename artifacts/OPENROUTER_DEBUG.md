# OpenRouter API Debugging

## Issue Summary
- **Problem:** Getting 401 "User not found" from OpenRouter API
- **User Confirmation:** API key works when tested externally
- **Conclusion:** Our implementation is calling OpenRouter incorrectly

## Current Implementation

### Headers Being Sent
```python
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "Referer": "https://github.com/fba-bench/fba-bench-enterprise",  # Fixed from "HTTP-Referer"
    "X-Title": "FBA-Bench"
}
```

### Request Body Format
```python
payload = {
    "model": "x-ai/grok-4-fast:free",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.7
}
```

### URL
```
POST https://openrouter.ai/api/v1/chat/completions
```

## What We've Tried
1. ✅ Fixed "HTTP-Referer" → "Referer" (was incorrect CGI-style header)
2. ✅ Verified Authorization header format: "Bearer {key}"
3. ✅ Ensured Content-Type is application/json
4. ✅ Added attribution headers (Referer, X-Title)

## Simulation Status
✅ **Infrastructure Working:**
- Agent creation successful
- Decision loop functioning (~260+ decisions made)
- Simulation running full 365 ticks
- Event bus publishing events
- Services initialized correctly

❌ **LLM API Failing:**
- All OpenRouter calls return 401
- Agent receives empty responses `[]`
- Simulations complete but without real LLM decisions

## Possible Causes

### 1. API Key Format Issue
- OpenRouter expects: `sk-or-v1-{hash}`
- We're sending: `Bearer sk-or-v1-{hash}`
- **Hypothesis:** Maybe the Authorization header parsing is case-sensitive or requires specific format?

### 2. Missing Required Headers
According to OpenRouter docs, optional but recommended:
- `HTTP-Referer` (we have `Referer` now)
- `X-Title` (we have this)
- Maybe needs User-Agent?

### 3. Session/Context Issue
- aiohttp ClientSession might not be preserving headers correctly
- Session timeout or connection reuse issue?

### 4. URL or Endpoint Issue
- Using v1 API: `https://openrouter.ai/api/v1/chat/completions`
- Maybe needs different endpoint for free models?

## Next Steps to Debug

1. **Log Exact Request Being Sent:**
   ```python
   logger.info(f"OpenRouter Request - URL: {url}")
   logger.info(f"OpenRouter Request - Headers: {headers}")
   logger.info(f"OpenRouter Request - Body: {payload}")
   ```

2. **Test with Minimal curl:**
   ```bash
   curl https://openrouter.ai/api/v1/chat/completions \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     -d '{
       "model": "x-ai/grok-4-fast:free",
       "messages": [{"role": "user", "content": "test"}]
     }'
   ```

3. **Compare with Working Implementation:**
   - Ask user how they tested the key
   - Get exact curl/postman request that worked
   - Match our implementation to theirs

4. **Try Alternative Libraries:**
   - Use `requests` instead of `aiohttp`
   - Use official OpenRouter Python client if available

## Current Workaround
Simulations continue running with stub LLM responses (empty decisions). The infrastructure is proven to work - just need to fix the API call format.

## Files Involved
- [`infrastructure/openrouter_client.py`](infrastructure/openrouter_client.py) - Main client implementation
- [`llm_interface/openrouter_client.py`](llm_interface/openrouter_client.py) - Wrapper class
- [`baseline_bots/openrouter_bot.py`](baseline_bots/openrouter_bot.py) - Bot implementation