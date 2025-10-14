# Reproducibility Module

This module provides tools and utilities for ensuring reproducible results across simulations, experiments, and analyses.

## Overview

Reproducibility is a critical aspect of scientific computing and simulation. This module offers:

- **Cache Management**: Efficient caching of computational results with configurable policies
- **Seed Management**: Tools for controlling random number generation to ensure reproducible randomness
- **Result Tracking**: Mechanisms for tracking and comparing experimental results
- **Environment Capture**: Tools for capturing and reproducing execution environments

## Components

### Cache Manager

The `CacheManager` class provides a centralized caching system with the following features:

- Multiple backends (in-memory and disk-based)
- Configurable time-to-live (TTL) for cache entries
- Size-based eviction policies
- Thread-safe operations
- Statistics tracking

#### Usage Example

```python
from reproducibility.cache.cache_manager import CacheManager

# Initialize cache manager
cache = CacheManager(
    cache_dir="./cache",
    max_size_mb=1024,  # 1GB
    default_ttl_seconds=86400,  # 24 hours
    enable_disk_cache=True,
    enable_memory_cache=True
)

# Use as a decorator
@cache.cache_decorator(ttl_seconds=3600)  # 1 hour
def expensive_computation(param1, param2):
    # Your expensive computation here
    return result

# Or use directly
key = "computation_key"
result = cache.get(key)
if result is None:
    result = compute_expensive_function()
    cache.set(key, result, ttl_seconds=3600)

# Get cache statistics
stats = cache.get_stats()
print(f"Cache hit rate: {stats['hit_rate']:.2%}")
```

### Seed Management

The seed management tools help ensure reproducible random number generation:

```python
from reproducibility.seed_manager import SeedManager

# Initialize with a fixed seed
seed_manager = SeedManager(seed=42)

# Get seeded random generators
random_gen = seed_manager.get_random_generator()
numpy_gen = seed_manager.get_numpy_generator()

# All random operations will be reproducible
value = random_gen.random()
```

### Result Tracking

Track and compare experimental results:

```python
from reproducibility.result_tracker import ResultTracker

# Initialize tracker
tracker = ResultTracker(experiment_name="my_experiment")

# Record results
tracker.record_result(
    parameters={"learning_rate": 0.01, "batch_size": 32},
    metrics={"accuracy": 0.95, "loss": 0.05},
    metadata={"model_version": "1.0", "timestamp": "2023-01-01"}
)

# Compare results
comparison = tracker.compare_runs(run_id1, run_id2)
```

## Configuration

The reproducibility module can be configured through environment variables or configuration files:

### Environment Variables

- `REPRODUCIBILITY_CACHE_DIR`: Directory for cache storage (default: `.cache`)
- `REPRODUCIBILITY_CACHE_SIZE_MB`: Maximum cache size in MB (default: 1024)
- `REPRODUCIBILITY_DEFAULT_TTL_SECONDS`: Default TTL for cache entries (default: 86400)
- `REPRODUCIBILITY_SEED`: Default seed for random number generation (default: None)

### Configuration File

Create a `reproducibility_config.yaml` file:

```yaml
cache:
  directory: "./cache"
  max_size_mb: 2048
  default_ttl_seconds: 86400
  enable_disk_cache: true
  enable_memory_cache: true

seed:
  default_seed: 42
  auto_seed: false

tracking:
  storage_dir: "./results"
  auto_save: true
```

## Best Practices

1. **Use Descriptive Keys**: When using the cache directly, use descriptive keys that include relevant parameters.

2. **Set Appropriate TTL**: Choose TTL values based on how often your data changes.

3. **Monitor Cache Performance**: Regularly check cache statistics to optimize hit rates.

4. **Version Your Experiments**: Use the result tracker to maintain version history of your experiments.

5. **Document Randomness**: Always document when and how randomness is used in your experiments.

## API Reference

### CacheManager

#### Constructor

```python
CacheManager(
    cache_dir: Union[str, Path] = ".cache",
    max_size_mb: int = 1024,
    default_ttl_seconds: int = 86400,
    enable_disk_cache: bool = True,
    enable_memory_cache: bool = True
)
```

#### Methods

- `get(key: str) -> Optional[Any]`: Retrieve a value from the cache
- `set(key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool`: Store a value in the cache
- `delete(key: str) -> bool`: Delete a value from the cache
- `clear() -> bool`: Clear all entries from the cache
- `get_stats() -> Dict[str, Any]`: Get cache statistics
- `cache_decorator(ttl_seconds: Optional[int] = None)`: Decorator for caching function results

## Contributing

When contributing to this module, please ensure:

1. All new features include appropriate tests
2. Documentation is updated for any API changes
3. Configuration options are properly documented
4. Performance implications are considered and documented

## License

This module is part of the FBA project and is subject to the project's license terms.
