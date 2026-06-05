# Architecture Overview

This document explains the class structure and organization of the cache simulator.

## Class Hierarchy

The simulator uses a bottom-up design with four main classes:

```
CacheLine (Basic Unit)
    ↓
CacheSet (Group of Lines)
    ↓
Cache (Complete Level)
    ↓
CacheSimulator (System Controller)
```

---

## 1. CacheLine Class

**Purpose**: Represents a single cache line (one slot in the cache)

### Attributes

```python
class CacheLine:
    valid: bool          # Is this line occupied?
    tag: int            # Which memory block is stored here?
    lru_counter: int    # When was this line last accessed?
```

### Key Methods

- `is_hit(tag)`: Check if this line contains the requested tag
- `update(tag, lru_value)`: Store new data and update LRU counter

### Why This Design?

Each cache line is independent and only needs to know:
1. Whether it contains valid data
2. Which block it's storing (tag)
3. When it was last used (for LRU)

---

## 2. CacheSet Class

**Purpose**: Manages a set of cache lines and implements LRU replacement

### Attributes

```python
class CacheSet:
    num_ways: int           # How many lines in this set?
    lines: List[CacheLine]  # The actual cache lines
    access_counter: int     # Global timestamp for LRU
```

### Key Methods

- `find_line(tag)`: Search for a tag among all ways
- `access(tag)`: Try to access a tag (returns hit/miss)
- `insert(tag)`: Add new tag using LRU (returns evicted tag)
- `invalidate(tag)`: Remove a tag from the set

### LRU Implementation

The set maintains an `access_counter` that increments with each access:

```python
def access(self, tag):
    # On hit: update the line's LRU counter
    self.access_counter += 1
    line.lru_counter = self.access_counter
```

When eviction is needed, it finds the line with the smallest `lru_counter`:

```python
def insert(self, tag):
    # Find least recently used
    lru_index = min(range(self.num_ways), 
                    key=lambda i: self.lines[i].lru_counter)
    # Evict and insert new
```

### Associativity Examples

- **Direct-mapped** (1-way): Each set has 1 line
- **2-way set-associative**: Each set has 2 lines
- **4-way set-associative**: Each set has 4 lines
- **Fully associative**: 1 set with many lines

---

## 3. Cache Class

**Purpose**: Represents a complete cache level (L1 or L2)

### Attributes

```python
class Cache:
    line_size: int      # Bytes per cache line
    num_ways: int       # Lines per set (associativity)
    data_size: int      # Total data bytes in cache
    num_sets: int       # Number of sets
    sets: List[CacheSet] # The actual sets
    
    # For address parsing
    offset_bits: int    # Bits for byte offset
    index_bits: int     # Bits for set selection
    tag_bits: int       # Bits for tag
```

### Key Calculations

**Number of sets**:
```python
total_lines = data_size / line_size
num_sets = total_lines / num_ways
```

**Example**:
- Data size: 64 bytes
- Line size: 4 bytes
- Num ways: 2
- Total lines: 64 / 4 = 16 lines
- Num sets: 16 / 2 = 8 sets

### Key Methods

- `access(address)`: Check if address hits in cache
- `insert(address)`: Add address to cache (returns evicted address)
- `invalidate(address)`: Remove address from cache
- `_parse_address(address)`: Break address into tag, index, offset

---

## 4. CacheSimulator Class

**Purpose**: Manages the complete two-level cache hierarchy

### Attributes

```python
class CacheSimulator:
    line_size: int      # Shared by both levels
    inclusive: bool     # Is L1 ⊆ L2?
    l1: Cache          # Level 1 cache
    l2: Cache          # Level 2 cache
```

### Key Method: memory_access()

This is the main entry point that routes operations:

```python
def memory_access(self, address, operation):
    if operation == 'R':
        return self._handle_read(address)
    else:  # operation == 'W'
        return self._handle_write(address)
```

### Read Flow

```
1. Check L1
   ├─ HIT → Return "L1HIT"
   └─ MISS → Check L2
              ├─ HIT → Load to L1, return "L2HIT"
              └─ MISS → Load to L2 and L1, return "MEMACC"
```

### Write Flow (No-Write-Allocate)

```
1. Check L1
   ├─ HIT → Return "L1HIT"
   └─ MISS → Check L2
              ├─ HIT → Return "L2HIT" (don't load to L1)
              └─ MISS → Return "MEMACC" (don't load anywhere)
```

---

## Data Flow Example

Let's trace what happens when reading address `0x00000000`:

1. **CacheSimulator** receives read request
2. Calls **L1.access(0x00000000)**
3. **Cache** parses address → tag=0, index=0, offset=0
4. Calls **sets[0].access(tag=0)**
5. **CacheSet** searches all lines for tag=0
6. **CacheLine** checks: `valid and tag == 0`?
7. Result bubbles back up the call stack

---

## Design Benefits

### 1. Separation of Concerns
- **CacheLine**: Knows only about one slot
- **CacheSet**: Knows only about LRU within one set
- **Cache**: Knows about address parsing and set organization
- **CacheSimulator**: Knows about hierarchy and policies

### 2. Reusability
- Same `Cache` class used for both L1 and L2
- Same `CacheSet` class works for any associativity
- Easy to extend to 3-level hierarchy

### 3. Testability
- Each class can be tested independently
- Clear interfaces between layers

### 4. Configurability
- All parameters (size, associativity, policies) are configurable
- No hardcoded constants

---

## Memory Organization Visual

```
Cache (L1 or L2)
├── Set 0
│   ├── Way 0 [Line: valid, tag, LRU]
│   ├── Way 1 [Line: valid, tag, LRU]
│   └── Way N [Line: valid, tag, LRU]
├── Set 1
│   ├── Way 0 [Line: valid, tag, LRU]
│   └── ...
└── Set M
    └── ...
```

Each access:
1. Uses **index bits** to select a set
2. Searches all **ways** in that set for matching **tag**
3. Uses **offset bits** to select byte within line (not simulated in detail here)
