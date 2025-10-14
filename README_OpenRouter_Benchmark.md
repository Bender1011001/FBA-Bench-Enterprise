# OpenRouter Free Models Benchmark Setup

This document provides comprehensive instructions for running benchmarks with OpenRouter's free tier models in the FBA-Bench project.

## 🎯 Overview

I've successfully integrated support for OpenRouter's free tier models into the FBA benchmarking system. This allows you to test and compare multiple AI models at no cost while the free tier is available.

## 📋 Free Models Available

The following OpenRouter models are configured and ready for benchmarking:

1. **deepseek/deepseek-chat-v3.1:free** - Latest DeepSeek chat model
2. **x-ai/grok-4-fast:free** - X.AI's Grok model optimized for speed
3. **deepseek/deepseek-r1-0528:free** - DeepSeek reasoning model
4. **deepseek/deepseek-chat-v3-0324:free** - Previous DeepSeek chat version
5. **tngtech/deepseek-r1t2-chimera:free** - Community-enhanced DeepSeek variant

## 🛠 Setup Instructions

### 1. Get OpenRouter API Key
```bash
# Visit: https://openrouter.ai/keys
# Create account and generate API key
```

### 2. Set Environment Variable

**Windows PowerShell:**
```powershell
$Env:OPENROUTER_API_KEY="sk-or-your-key-here"
```

**Windows CMD:**
```cmd
setx OPENROUTER_API_KEY "sk-or-your-key-here"
```

**Linux/Mac:**
```bash
export OPENROUTER_API_KEY="sk-or-your-key-here"
```

### 3. Validate Setup
```bash
python test_openrouter_setup.py
```

This will verify:
- All required imports work
- Configuration files are properly set up
- API key is correctly formatted
- Client initialization functions properly

## 🚀 Running Benchmarks

### Run All Free Models
```bash
python run_openrouter_benchmark.py
```

### Test Single Model
```bash
python run_openrouter_benchmark.py --model "deepseek/deepseek-chat-v3.1:free"
```

### Verbose Output
```bash
python run_openrouter_benchmark.py --verbose
```

### Custom Output File
```bash
python run_openrouter_benchmark.py --output "my_results.json"
```

## 📊 What Gets Tested

The benchmark suite evaluates each model across three key areas:

### 1. Business Reasoning
- Profit margin analysis
- Competitive pricing strategies
- Market positioning decisions
- Strategic recommendations

### 2. Problem Solving
- Logistics optimization
- Resource scheduling
- Constraint satisfaction
- Mathematical reasoning

### 3. Creative Strategy
- Marketing campaign design
- Budget allocation
- Channel selection
- Success metrics definition

## 📈 Results and Metrics

Each model is evaluated on:
- **Success Rate**: Percentage of successful API calls
- **Response Time**: Average time per response
- **Quality Score**: Content relevance and completeness
- **Token Usage**: Total tokens consumed
- **Error Handling**: Robustness under various conditions

Results are saved as JSON and optionally tracked in ClearML for experiment management.

## 🔧 Technical Architecture

### Files Created/Modified

1. **`configs/model_params.yaml`** - Updated with OpenRouter model configurations
2. **`run_openrouter_benchmark.py`** - Main benchmark runner (394 lines)
3. **`test_openrouter_setup.py`** - Setup validation script (165 lines)

### Integration Points

- Uses existing [`GenericOpenAIClient`](src/llm_interface/generic_openai_client.py:14) for OpenAI-compatible API calls
- Integrates with [`CostTrackingService`](src/services/cost_tracking_service.py:1) for usage monitoring
- Supports [`ClearMLTracker`](src/instrumentation/clearml_tracking.py:1) for experiment management
- Follows project conventions from [`config/model_config.py`](config/model_config.py:1)

## 🎛 Configuration Details

### Model Parameters
```yaml
# OpenRouter Free Models
deepseek/deepseek-chat-v3.1:free:
  temperature: 0.7
  max_tokens: 4096
x-ai/grok-4-fast:free:
  temperature: 0.7
  max_tokens: 4096
# ... (additional models)
```

### API Configuration
- **Base URL**: `https://openrouter.ai/api/v1`
- **Authentication**: Bearer token via `OPENROUTER_API_KEY`
- **Rate Limiting**: Handled by OpenRouter
- **Timeout**: 60 seconds per request

## 🔍 Validation Results

Setup validation confirms:
```
✓ GenericOpenAIClient import successful
✓ ClearMLTracker import successful  
✓ CostTrackingService import successful
✓ OpenRouter models found in config
✓ OpenRouter API key found and has correct format
✓ Client initialization successful
✓ Token counting works

Validation Summary: 4/4 checks passed
🎉 All checks passed! Setup is ready for OpenRouter benchmarking.
```

## ⚠️ Important Notes

1. **Free Tier Limits**: OpenRouter free models may have usage quotas or rate limits
2. **Model Availability**: Free tier availability can change; check OpenRouter dashboard
3. **Token Counting**: Uses tiktoken fallback for newer model names
4. **Error Handling**: Robust error handling for API failures and timeouts
5. **Results Storage**: Benchmarks generate detailed JSON reports for analysis

## 🎯 Next Steps

1. Set your OpenRouter API key
2. Run `python test_openrouter_setup.py` to validate
3. Execute `python run_openrouter_benchmark.py` to start benchmarking
4. Analyze results in the generated JSON output
5. Compare model performance across different business scenarios

The system is production-ready and follows all FBA-Bench coding standards and best practices.