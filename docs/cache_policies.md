# Cache Policies

This document explains the cache policies implemented in the simulator.

## Overview

The simulator implements three key policies:

1. **Write-Through**: Write operations propagate to lower levels
2. **No-Write-Allocate**: Write misses don't allocate cache lines
3. **Inclusive Cache** (optional): L1 ⊆ L2 (L1 is subset of L2)

---

## 1. Write-Through Policy

### What is Write-Through?

When writing to cache, the write **also propagates** to the next level (L2 or main memory).

### Contrast with Write-Back

| Policy | Write to Cache | Write to Memory |
|--------|----------------|-----------------|
| **Write-Through** | Immediate | Immediate |
| **Write-Back** | Immediate | Only on eviction |

### Implementation

In our simulator, write-through means:
- **L1 hit on write**: Write to L1 and L2
- **L2 hit on write**: Write to L2 and memory
- **Memory access**: Write directly to memory

```python
def _handle_write(self, address: int) -> str:
    # Check L1
    if self.l1.access(address):
        # Write to L1, implicitly also writes through to L2
        return "L1HIT"
    
    # Check L2
    if self.l2.access(address):
        # Write to L2, implicitly writes through to memory
        return "L2HIT"
    
    # Write directly to memory
    return "MEMACC"
```

### Why Write-Through?

**Advantages**:
- Simpler to implement
- Memory always has latest data (consistency)
- No "dirty" bits needed

**Disadvantages**:
- More memory traffic (every write goes to memory)
- Slower than write-back

---

## 2. No-Write-Allocate Policy

### What is No-Write-Allocate?

On a **write miss**, the data is **NOT** loaded into the cache.

### Contrast with Write-Allocate

| Policy | On Write Miss |
|--------|---------------|
| **No-Write-Allocate** | Write to memory only, don't load to cache |
| **Write-Allocate** | Load line to cache, then write |

### Implementation

```python
def _handle_write(self, address: int) -> str:
    # Check L1
    if self.l1.access(address):
        return "L1HIT"
    
    # L1 miss, check L2
    if self.l2.access(address):
        # L2 hit: DON'T load to L1 (no-write-allocate)
        return "L2HIT"
    
    # Both miss: DON'T load anywhere (no-write-allocate)
    return "MEMACC"
```

### Example

```
Write to address 0x100:

Scenario 1: Address NOT in cache
├─ Write-Allocate: Load 0x100 to cache, then write
└─ No-Write-Allocate: Write directly to memory, don't cache

Scenario 2: Address in L2 but not L1
├─ Write-Allocate: Load 0x100 to L1, then write
└─ No-Write-Allocate: Write to L2/memory, don't load to L1
```

### Why No-Write-Allocate?

**Advantages**:
- Don't pollute cache with write-only data
- Good for streaming writes (data written once, never read)

**Disadvantages**:
- If data is read soon after writing, it's a miss

### Common Combination

**Write-Through + No-Write-Allocate** (what we implement):
- Writes go directly to memory
- Write misses don't allocate
- Simple and predictable

**Write-Back + Write-Allocate** (alternative):
- Writes stay in cache
- Write misses allocate
- Better performance but more complex

---

## 3. Inclusive Cache Policy

### What is Inclusive Cache?

An **inclusive cache** maintains the property that **L1 ⊆ L2**:
- Everything in L1 is also in L2
- L2 can contain data not in L1
- If data is evicted from L2, it must be invalidated in L1

### Contrast with Exclusive Cache

| Policy | Relationship |
|--------|--------------|
| **Inclusive** | L1 ⊆ L2 (L1 subset of L2) |
| **Exclusive** | L1 ∩ L2 = ∅ (L1 and L2 disjoint) |
| **Non-Inclusive** | No restriction |

### Why Inclusive?

**Advantages**:
- Simplifies coherence protocols (in multicore systems)
- L2 can filter accesses from other cores
- Easier to maintain consistency

**Disadvantages**:
- L2 must be larger than L1 (some capacity "wasted")
- Extra invalidations needed

---

## Inclusive Cache Implementation

### On Read Miss (Both Levels)

When loading data from memory:

```python
def _handle_read(self, address: int) -> str:
    # ... checks omitted ...
    
    # Both L1 and L2 miss
    evicted_l2_address = self.l2.insert(address)
    
    # INCLUSIVE POLICY: If L2 evicts, invalidate from L1
    if self.inclusive and evicted_l2_address is not None:
        self.l1.invalidate(evicted_l2_address)
    
    # Now insert into L1
    self.l1.insert(address)
    
    return "MEMACC"
```

### Visual Example

#### Scenario: L2 Eviction Causes L1 Invalidation

```
Step 1: Initial state
L1: [A, B]
L2: [A, B, C, D]  (4 lines, all full)

Step 2: Read address E (miss in both)
- Insert E into L2
- L2 is full → evict A (LRU)

L2 before: [A, B, C, D]
L2 after:  [E, B, C, D]  (A evicted)

Step 3: Inclusive policy enforcement
- A was evicted from L2
- Must invalidate A from L1

L1 before: [A, B]
L1 after:  [-, B]  (A invalidated)

Step 4: Insert E into L1
L1 final:  [E, B]
L2 final:  [E, B, C, D]

Property maintained: L1 ⊆ L2 ✓
```

---

## Policy Interactions

### Read Operation Flow

```
Read address X:

1. Check L1
   ├─ HIT → "L1HIT" ✓
   └─ MISS ↓

2. Check L2
   ├─ HIT → Load to L1 → "L2HIT" ✓
   │        (L1 ⊆ L2 maintained)
   └─ MISS ↓

3. Load from memory
   - Load to L2 (may evict Y)
   - If inclusive & Y evicted: invalidate Y from L1
   - Load to L1
   → "MEMACC" ✓
```

### Write Operation Flow

```
Write to address X:

1. Check L1
   ├─ HIT → "L1HIT" ✓
   │        (write-through: also writes to L2)
   └─ MISS ↓

2. Check L2
   ├─ HIT → "L2HIT" ✓
   │        (no-write-allocate: DON'T load to L1)
   │        (write-through: also writes to memory)
   └─ MISS ↓

3. Write to memory
   → "MEMACC" ✓
   (no-write-allocate: DON'T load to any cache)
```

---

## Inclusive Policy Edge Cases

### Case 1: L1 Eviction (Normal)

```
L1 evicts A:
- Remove A from L1
- A might still be in L2 (allowed: L1 ⊆ L2)
- No action needed
```

### Case 2: L2 Eviction (Inclusive Policy)

```
L2 evicts A:
- Remove A from L2
- If A is in L1: invalidate it (maintain L1 ⊆ L2)
- If A not in L1: no action needed
```

### Case 3: Read Causes Both Evictions

```
Read X (miss in both):

Step 1: Insert to L2
- L2 evicts A

Step 2: Inclusive enforcement
- Invalidate A from L1 (if present)

Step 3: Insert to L1
- L1 might evict B (unrelated to A)
- B can stay in L2 (L1 ⊆ L2 maintained)
```

---

## Configuration Parameter

The inclusive policy is controlled by configuration:

```
CACHE_LINE_SIZE, CACHE_INCLUSIVE, L1_NUM_WAYS, L1_DATA_SIZE, L2_NUM_WAYS, L2_DATA_SIZE
                      ↑
                      TRUE or FALSE
```

**TRUE**: Enforce L1 ⊆ L2
**FALSE**: No inclusion property (L1 and L2 independent)

---

## Testing the Policies

### Test Write-Through + No-Write-Allocate

```
1. Write to address X (miss everywhere)
   → Result: MEMACC
   → X should NOT be in L1 or L2

2. Read address X
   → Result: MEMACC (because write didn't allocate)
   → Now X is loaded to both caches
```

### Test Inclusive Policy

```
1. Fill L2 completely
2. Fill L1 with subset of L2 data
3. Read new address (causes L2 eviction)
4. Verify evicted address is invalidated from L1
```

---

## Summary Table

| Policy | What It Does | Why |
|--------|-------------|-----|
| **Write-Through** | Writes propagate immediately | Simpler, consistent memory |
| **No-Write-Allocate** | Write misses don't load to cache | Avoid polluting cache |
| **Inclusive** | L1 ⊆ L2 enforced | Simplify coherence |

These policies work together to create a predictable and efficient cache hierarchy.
