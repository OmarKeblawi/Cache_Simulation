# Address Parsing

This document explains how 32-bit memory addresses are parsed and used to access the cache.

## Address Structure

Every memory address is 32 bits and is divided into three parts:

```
|    Tag    |    Index    |   Offset   |
|-----------|-------------|------------|
 High bits   Middle bits   Low bits
```

### Three Components

1. **Offset**: Selects which byte within a cache line
2. **Index**: Selects which set in the cache
3. **Tag**: Identifies which memory block is stored

---

## Bit Width Calculations

### Offset Bits

The offset field selects a byte within a cache line.

```python
offset_bits = log2(line_size)
```

**Example**: If `line_size = 4 bytes`:
- `offset_bits = log2(4) = 2 bits`
- Can address bytes 0, 1, 2, 3 within a line

### Index Bits

The index field selects which set to access.

```python
num_sets = (data_size / line_size) / num_ways
index_bits = log2(num_sets)
```

**Example**: If we have 8 sets:
- `index_bits = log2(8) = 3 bits`
- Can select sets 0-7

### Tag Bits

The remaining bits form the tag.

```python
tag_bits = 32 - offset_bits - index_bits
```

**Example**: If offset=2 and index=3:
- `tag_bits = 32 - 2 - 3 = 27 bits`

---

## Complete Example

### Configuration
```
Line size: 4 bytes
L1: Direct-mapped (1-way), 16 bytes data
```

### Calculations

1. **Total lines**: 16 / 4 = 4 lines
2. **Number of sets**: 4 / 1 = 4 sets
3. **Offset bits**: log2(4) = 2 bits
4. **Index bits**: log2(4) = 2 bits
5. **Tag bits**: 32 - 2 - 2 = 28 bits

### Address Breakdown

```
32-bit Address: 0x00000010
Binary: 0000 0000 0000 0000 0000 0000 0001 0000

Breaking it down:
┌─────────────────────────────┬────┬────┐
│ Tag (28 bits)               │Idx │Off │
│ 0000000000000000000000000001│ 00 │ 00 │
└─────────────────────────────┴────┴────┘

Tag    = 0x0000001 (higher 28 bits)
Index  = 0 (bits 3-2)
Offset = 0 (bits 1-0)
```

This address maps to:
- **Set 0** (index = 0)
- **Tag 1** (identifies this specific memory block)
- **Byte 0** within the line (offset = 0)

---

## Parsing Implementation

```python
def _parse_address(self, address: int) -> Tuple[int, int, int]:
    # Extract offset (lowest bits)
    offset_mask = (1 << self.offset_bits) - 1
    offset = address & offset_mask
    
    # Extract index (middle bits)
    index_mask = (1 << self.index_bits) - 1
    index = (address >> self.offset_bits) & index_mask
    
    # Extract tag (highest bits)
    tag = address >> (self.offset_bits + self.index_bits)
    
    return tag, index, offset
```

### Step-by-Step Example

Address: `0x00000014` (binary: `...0001 0100`)
- Line size: 4 bytes → offset_bits = 2
- 4 sets → index_bits = 2

```python
# Step 1: Extract offset (last 2 bits)
offset_mask = (1 << 2) - 1 = 0b11 = 3
offset = 0x14 & 3 = 0b10100 & 0b00011 = 0b00 = 0

# Step 2: Extract index (next 2 bits)
shifted = 0x14 >> 2 = 0b00101
index_mask = (1 << 2) - 1 = 0b11 = 3
index = 0b00101 & 0b00011 = 0b01 = 1

# Step 3: Extract tag (remaining bits)
tag = 0x14 >> (2 + 2) = 0x14 >> 4 = 0b00001 = 1

Result: tag=1, index=1, offset=0
```

This maps to **Set 1**, looking for **Tag 1**.

---

## Why This Matters

### 1. Set Selection
The index bits determine which set to search:
- Different indices → different sets
- No conflict between addresses with different indices

### 2. Tag Comparison
Within a set, the tag identifies the specific memory block:
- Same tag + same index = **cache hit**
- Different tag but same index = **conflict** (may need eviction)

### 3. Alignment
The offset bits are ignored for cache lookup:
- `0x00000000`, `0x00000001`, `0x00000002`, `0x00000003` all map to the same cache line
- They differ only in which byte within the line

---

## Example: Address Mapping

Given configuration:
- Line size: 4 bytes (offset_bits = 2)
- 4 sets (index_bits = 2)

| Address    | Binary (last 4 bits) | Offset | Index | Tag | Set | Line |
|------------|----------------------|--------|-------|-----|-----|------|
| 0x00000000 | 0000                 | 00     | 00    | 0   | 0   | Same |
| 0x00000001 | 0001                 | 01     | 00    | 0   | 0   | Same |
| 0x00000004 | 0100                 | 00     | 01    | 0   | 1   | Diff |
| 0x00000010 | 0000                 | 00     | 00    | 1   | 0   | Diff |

**Key Observations**:
- `0x00` and `0x01` map to the same line (same tag & index, different offset)
- `0x00` and `0x04` map to different sets (different index)
- `0x00` and `0x10` map to the same set but different tags (conflict!)

---

## Address Reconstruction

When a line is evicted, we need to reconstruct its full address:

```python
def reconstruct_address(tag, index, offset=0):
    address = (tag << (index_bits + offset_bits)) | \
              (index << offset_bits) | \
              offset
    return address
```

**Example**:
- tag = 1, index = 2, offset = 0
- offset_bits = 2, index_bits = 2

```python
address = (1 << 4) | (2 << 2) | 0
        = 16 | 8 | 0
        = 24 = 0x00000018
```

---

## Visual Summary

```
Memory Address Space
├── Block 0 (Tag 0, Maps to Set 0)
│   ├── 0x00000000 (Offset 0)
│   ├── 0x00000001 (Offset 1)
│   ├── 0x00000002 (Offset 2)
│   └── 0x00000003 (Offset 3)
├── Block 1 (Tag 0, Maps to Set 1)
│   ├── 0x00000004 (Offset 0)
│   └── ...
├── Block 4 (Tag 1, Maps to Set 0) ← Conflicts with Block 0!
│   ├── 0x00000010 (Offset 0)
│   └── ...
└── ...
```

Addresses that map to the same set but have different tags will **conflict** and may evict each other.
