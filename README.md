# Cache Simulator - Computer Architecture Assignment

A two-level cache hierarchy simulator implementing L1, L2, and main memory with configurable parameters and industry-standard cache policies.

## Quick Start

```bash
python cache_sim.py def.txt input.txt output.txt
```

## Test Results

✅ **All 102 test cases passing (100%)**

The implementation has been thoroughly tested with a comprehensive test suite covering:
- All cache configurations (direct-mapped, 2-way, 4-way)
- All line sizes (2, 4, 8, 16, 32 bytes)
- LRU replacement in all scenarios
- Inclusive and non-inclusive cache modes
- Write policies (no-write-allocate)
- Stress tests and edge cases

See [docs/TODO.md](docs/TODO.md) for detailed test coverage and enhancement ideas.

## Features

- ✅ **Two-level cache hierarchy** (L1 and L2)
- ✅ **LRU replacement policy** (Least Recently Used)
- ✅ **Write-through policy** with no-write-allocate
- ✅ **Inclusive cache support** (L1 ⊆ L2)
- ✅ **Fully configurable** (line size, associativity, cache size)
- ✅ **Python 3.10+** with standard library only

## Repository Structure

```
.
├── cache_sim.py          # Main simulator implementation
├── docs/                 # Comprehensive documentation
│   ├── index.md          # Documentation overview
│   ├── architecture.md   # Class structure and design
│   ├── address_parsing.md # Address breakdown explained
│   ├── lru_policy.md     # LRU algorithm details
│   ├── cache_policies.md # Write and inclusion policies
│   ├── usage_guide.md    # How to run and test
│   └── example_walkthrough.md # Step-by-step example
├── def.txt              # Test config 1
├── input.txt            # Test trace 1
├── output.txt           # Expected output 1
├── def2.txt             # Test config 2
├── input2.txt           # Test trace 2
└── output2.txt          # Expected output 2
```

## Documentation

📚 **Full documentation available in the [`docs/`](docs/) folder**

Start with [docs/index.md](docs/index.md) for a complete guide covering:
- Architecture and class design
- Address parsing and bit fields
- LRU replacement algorithm
- Cache policies (write-through, no-write-allocate, inclusive)
- Usage examples and testing

## Usage

### Basic Command

```bash
python cache_sim.py <config_file> <trace_file> <output_file>
```

### Configuration File Format

```
CACHE_LINE_SIZE, CACHE_INCLUSIVE, L1_NUM_WAYS, L1_DATA_SIZE, L2_NUM_WAYS, L2_DATA_SIZE
```

Example:
```
4, TRUE, 1, 16, 2, 64
```

### Trace File Format

```
<HEX_ADDRESS> , R/W
```

Example:
```
00000000 , R
00000004 , W
```

### Output Format

```
L1HIT    # Found in L1 cache
L2HIT    # Found in L2 cache (not in L1)
MEMACC   # Not in any cache (main memory access)
```

## Running Tests

```bash
# Test 1
python cache_sim.py def.txt input.txt test1_out.txt
diff test1_out.txt output.txt

# Test 2
python cache_sim.py def2.txt input2.txt test2_out.txt
diff test2_out.txt output2.txt
```

If both tests produce no diff output, the implementation is correct! ✅

## Implementation Highlights

### Class Hierarchy

```
CacheLine       → Individual cache line (tag, valid bit, LRU counter)
    ↓
CacheSet        → Set of cache lines (implements LRU)
    ↓
Cache           → Complete cache level (L1 or L2)
    ↓
CacheSimulator  → Manages both cache levels and policies
```

### Cache Policies

| Policy | Description |
|--------|-------------|
| **LRU** | Evicts the least recently used cache line |
| **Write-Through** | Writes propagate immediately to lower levels |
| **No-Write-Allocate** | Write misses don't allocate in cache |
| **Inclusive** | L1 is a subset of L2 (optional) |

### Example Configuration

```
Line size: 4 bytes
Inclusive: TRUE
L1: Direct-mapped (1-way), 16 bytes → 4 lines, 4 sets
L2: 2-way set-associative, 64 bytes → 16 lines, 8 sets
```

## Requirements

- **Python**: 3.10 or higher
- **Dependencies**: Standard library only
- **Platform**: Linux, macOS, Windows

## Assignment Details

- **Course**: Computer Architecture (מבנה מחשבים)
- **Institution**: Technion - Israel Institute of Technology
- **Semester**: Spring 2026
- **Assignment**: Homework 1 - Cache Simulator (33 points)

## Learn More

For detailed explanations of the implementation:

1. **[Architecture Overview](docs/architecture.md)** - Understand the class structure
2. **[Address Parsing](docs/address_parsing.md)** - Learn how addresses are decoded
3. **[LRU Policy](docs/lru_policy.md)** - Deep dive into LRU replacement
4. **[Cache Policies](docs/cache_policies.md)** - Explore write and inclusion policies
5. **[Usage Guide](docs/usage_guide.md)** - Complete usage instructions
6. **[Example Walkthrough](docs/example_walkthrough.md)** - Step-by-step trace analysis

## License

Academic assignment - for educational purposes only.

## Authors

Implementation with comprehensive documentation and code assistance.
