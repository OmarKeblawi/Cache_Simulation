# Cache Simulator Documentation

Welcome to the cache simulator documentation. This guide explains the implementation of a two-level cache hierarchy simulator written in Python.

## Table of Contents

1. [Architecture Overview](architecture.md) - Class structure and organization
2. [Address Parsing](address_parsing.md) - How memory addresses are decoded
3. [LRU Replacement Policy](lru_policy.md) - Least Recently Used algorithm implementation
4. [Cache Policies](cache_policies.md) - Write policies and inclusive cache behavior
5. [Usage Guide](usage_guide.md) - How to run and test the simulator
6. [Example Walkthrough](example_walkthrough.md) - Step-by-step trace of a test case
7. [Test Results](TEST_RESULTS.md) - Complete test suite results and coverage
8. [TODO & Status](TODO.md) - Implementation status and enhancement ideas

## Quick Overview

The cache simulator implements a two-level memory hierarchy:

```
CPU → L1 Cache → L2 Cache → Main Memory
```

### Cache Lines Explained

A **cache line** is the smallest unit of data that can be transferred between a CPU cache and main memory. It typically consists of 64 bytes on modern processors.

Each cache entry includes:
- **Tag Bits**: Identify which memory address the data came from
- **Valid Bit**: Flag indicating if the data is current/valid
- **Data (Cache Line)**: The actual 64-byte data block

**Example**: When the CPU requests data at address `0x0005` from a 64-byte cache line starting at `0x0000`:
1. The entire 64-byte cache line is fetched from memory
2. The requested byte is extracted
3. All surrounding bytes are now cached for future access (spatial locality)

### Key Features

- **Two-level hierarchy**: L1 and L2 caches with configurable parameters
- **LRU replacement**: Least Recently Used eviction policy
- **Write-through**: Writes propagate to lower levels
- **No-write-allocate**: Write misses don't allocate cache lines
- **Inclusive cache option**: L1 can be a subset of L2
- **Configurable**: Line size, associativity, and cache size are all configurable

### Write Policies Explained

#### Write-Through
When data is written to the cache, it's **immediately written to the lower level** (L2 or main memory). This ensures all cache levels stay consistent.

**Example**:
```
CPU writes 42 to address (Tag=2)
L1 Cache has Tag 2 → HIT

Step 1: Write 42 to L1 cache
Step 2: IMMEDIATELY write 42 to L2/memory
Result: L1 = [42], L2 = [42] ✓ Consistent
```

#### No-Write-Allocate
When a write miss occurs (data not in cache), the data is written directly to the lower level **WITHOUT** loading it into the cache.

**Example**:
```
CPU writes 99 to address (Tag=5)
L1 Cache does NOT have Tag 5 → MISS

Step 1: Write 99 directly to L2/memory
Step 2: Do NOT load Tag 5 into L1 cache
Result: L1 still unchanged, L2 has new value 99
```

**Combined Behavior (Write-Through + No-Write-Allocate)**:
- **Write Hit**: Write to cache + write to lower level (write-through)
- **Write Miss**: Write to lower level only, don't allocate cache line (no-write-allocate)

This approach ensures consistency while avoiding cache pollution from write-only data.

### Class Hierarchy

```
CacheLine       - Individual cache line (tag, valid bit, LRU counter)
    ↓
CacheSet        - Set of cache lines (implements LRU)
    ↓
Cache           - Complete cache level (L1 or L2)
    ↓
CacheSimulator  - Manages both cache levels and policies
```

### Memory Access Results

For each memory access, the simulator returns one of three results:

- **L1HIT**: Data found in L1 cache
- **L2HIT**: Data not in L1, but found in L2 cache
- **MEMACC**: Data not in any cache, accessed from main memory

## Implementation Status

✅ **All 102 test cases passing (100%)**

The implementation is complete and fully functional! See [TODO.md](TODO.md) for:
- Detailed test coverage breakdown
- Optional enhancements and improvements
- Learning recommendations

## Getting Started

To understand the implementation:

1. Start with [Architecture Overview](architecture.md) to understand the class structure
2. Read [Address Parsing](address_parsing.md) to understand how addresses are decoded
3. Learn about [LRU Policy](lru_policy.md) to see how replacement works
4. Review [Cache Policies](cache_policies.md) for write and inclusion policies
5. See [Example Walkthrough](example_walkthrough.md) for a concrete example
6. Check [TODO.md](TODO.md) for enhancement ideas and future improvements

## Implementation Details

- **Language**: Python 3.10+
- **Dependencies**: Standard library only
- **Lines of Code**: ~350
- **Key Algorithms**: LRU replacement, address parsing, inclusive cache management
