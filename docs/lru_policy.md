# LRU Replacement Policy

This document explains how the Least Recently Used (LRU) replacement policy is implemented.

## What is LRU?

**LRU (Least Recently Used)** is a cache replacement policy that evicts the cache line that hasn't been accessed for the longest time.

### Intuition

If we need to make room for new data, we evict the data that we least recently used, assuming it's less likely to be needed again soon.

---

## Implementation Strategy

We use a **timestamp-based approach** with counters:

1. Each cache line has an `lru_counter`
2. Each set has an `access_counter` that increments on every access
3. When a line is accessed, its `lru_counter` = current `access_counter`
4. When eviction is needed, we evict the line with the smallest `lru_counter`

---

## Data Structure

### CacheLine
```python
class CacheLine:
    lru_counter: int  # Timestamp of last access
```

### CacheSet
```python
class CacheSet:
    access_counter: int  # Global timestamp
    lines: List[CacheLine]
```

---

## Access Flow

### When Accessing an Existing Line

```python
def access(self, tag):
    # Find the line
    way_index = self.find_line(tag)
    if way_index is not None:
        # HIT: Update timestamp
        self.access_counter += 1  # Increment global counter
        self.lines[way_index].lru_counter = self.access_counter
        return True, None
```

**Example Timeline**:
```
Initial state (all counters = 0):
Set 0: [Line 0: tag=A, lru=0] [Line 1: tag=B, lru=0]
access_counter = 0

Access tag A:
access_counter = 1
Set 0: [Line 0: tag=A, lru=1] [Line 1: tag=B, lru=0]
       ↑ Updated!

Access tag B:
access_counter = 2
Set 0: [Line 0: tag=A, lru=1] [Line 1: tag=B, lru=2]
                               ↑ Updated!

Access tag A again:
access_counter = 3
Set 0: [Line 0: tag=A, lru=3] [Line 1: tag=B, lru=2]
       ↑ Updated again!
```

---

## Insertion and Eviction

### When Inserting a New Line

```python
def insert(self, tag):
    # Step 1: Try to find an empty line
    for line in self.lines:
        if not line.valid:
            self.access_counter += 1
            line.update(tag, self.access_counter)
            return None  # No eviction needed
    
    # Step 2: All lines are valid, must evict
    # Find line with SMALLEST lru_counter
    lru_index = min(range(self.num_ways), 
                    key=lambda i: self.lines[i].lru_counter)
    
    evicted_tag = self.lines[lru_index].tag
    
    # Step 3: Replace the LRU line
    self.access_counter += 1
    self.lines[lru_index].update(tag, self.access_counter)
    
    return evicted_tag
```

---

## Complete Example

### Configuration
- 2-way set-associative (each set has 2 lines)
- Focusing on Set 0

### Sequence of Accesses

#### Initial State
```
Set 0: [Empty] [Empty]
access_counter = 0
```

#### Access 1: Insert tag A
```
Set 0: [tag=A, lru=1] [Empty]
access_counter = 1
```
- Line 0 is empty → insert there
- No eviction needed

#### Access 2: Insert tag B
```
Set 0: [tag=A, lru=1] [tag=B, lru=2]
access_counter = 2
```
- Line 1 is empty → insert there
- No eviction needed

#### Access 3: Access tag A (hit)
```
Set 0: [tag=A, lru=3] [tag=B, lru=2]
access_counter = 3
```
- Tag A found in line 0
- Update lru_counter to 3

#### Access 4: Insert tag C (eviction required)
```
Before eviction:
Set 0: [tag=A, lru=3] [tag=B, lru=2]
                       ↑ Smallest lru_counter → LRU

After eviction:
Set 0: [tag=A, lru=3] [tag=C, lru=4]
access_counter = 4
```
- Both lines are valid
- Line 1 has smallest lru_counter (2 < 3)
- Evict B, insert C

#### Access 5: Insert tag D (eviction required)
```
Before eviction:
Set 0: [tag=A, lru=3] [tag=C, lru=4]
       ↑ Smallest lru_counter → LRU

After eviction:
Set 0: [tag=D, lru=5] [tag=C, lru=4]
access_counter = 5
```
- Both lines are valid
- Line 0 has smallest lru_counter (3 < 4)
- Evict A, insert D

---

## Visual Timeline

```
Time  Action      Set State           access_counter  Notes
────────────────────────────────────────────────────────────────
0     Start       [-, -]              0               Empty
1     Insert A    [A₁, -]             1               A inserted
2     Insert B    [A₁, B₂]            2               B inserted
3     Access A    [A₃, B₂]            3               A updated
4     Insert C    [A₃, C₄]            4               B evicted (lru=2)
5     Insert D    [D₅, C₄]            5               A evicted (lru=3)
6     Access C    [D₅, C₆]            6               C updated
7     Access D    [D₇, C₆]            7               D updated
8     Insert E    [D₇, E₈]            8               C evicted (lru=6)

Subscripts show lru_counter values
```

---

## Why This Works

### Correctness
At any point, the line with the smallest `lru_counter` is the one that was accessed longest ago.

### Efficiency
- **Time complexity**: O(num_ways) to find LRU
  - For small num_ways (1, 2, 4), this is very fast
- **Space complexity**: One integer per line
- **No complex data structures**: Just counters

### Edge Cases Handled

1. **Empty lines**: Checked first, no eviction needed
2. **All lines same age**: `min()` picks the first one (deterministic)
3. **Single way**: LRU is trivial (only one line to evict)

---

## LRU vs Other Policies

### FIFO (First In, First Out)
- **FIFO**: Evict the oldest inserted line
- **LRU**: Evict the least recently accessed line
- **Difference**: FIFO ignores accesses, LRU considers them

**Example**:
```
Insert A, Insert B, Access A, Insert C

FIFO would evict A (first inserted)
LRU evicts B (least recently accessed)
```

### LFU (Least Frequently Used)
- **LFU**: Evict the least frequently accessed line
- **LRU**: Evict the least recently accessed line
- **Difference**: LFU counts total accesses, LRU only cares about recency

### Random
- **Random**: Evict a random line
- **LRU**: Evict based on access pattern
- **Difference**: Random is simpler but less effective

---

## Implementation Notes

### Counter Overflow?

With a 64-bit integer, the counter would take millions of years to overflow at typical access rates. In practice, this is not a concern.

### Alternative: Stack-based LRU

Another implementation uses a stack:
- On access, move line to top of stack
- Evict from bottom of stack

Our counter approach is simpler and more efficient for hardware simulation.

---

## LRU in Different Associativities

### Direct-Mapped (1-way)
```python
num_ways = 1
# Only one line per set
# LRU is trivial: always evict the only line
```

### 2-Way Set-Associative
```python
num_ways = 2
# Compare 2 lru_counters
# Fast min() operation
```

### 4-Way Set-Associative
```python
num_ways = 4
# Compare 4 lru_counters
# Still efficient
```

### Fully Associative
```python
num_ways = num_lines  # All lines in one set
# More comparisons, but still O(n)
```

---

## Testing LRU

To verify LRU is working:

1. Fill a set completely
2. Access lines in a known order
3. Insert a new line
4. Verify the correct line was evicted

**Example test**:
```python
# 2-way set
insert(A)  # Set: [A, -]
insert(B)  # Set: [A, B]
access(A)  # Set: [A*, B]  (* = more recent)
insert(C)  # Should evict B
# Expected: [A, C]
```
