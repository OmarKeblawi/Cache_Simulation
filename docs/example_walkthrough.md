# Example Walkthrough

This document walks through the provided example step-by-step to show how the cache simulator works.

## Configuration

From `def.txt`:
```
4, TRUE, 1, 16, 2, 64
```

### Parsed Configuration

| Parameter | Value | Meaning |
|-----------|-------|---------|
| Line size | 4 bytes | Each cache line holds 4 bytes |
| Inclusive | TRUE | L1 ⊆ L2 (inclusive cache) |
| L1 ways | 1 | Direct-mapped |
| L1 data size | 16 bytes | Total data in L1 |
| L2 ways | 2 | 2-way set-associative |
| L2 data size | 64 bytes | Total data in L2 |

### Calculated Cache Structure

**L1 Cache**:
- Lines: 16 / 4 = **4 lines**
- Sets: 4 / 1 = **4 sets** (direct-mapped)
- Ways per set: **1**

**L2 Cache**:
- Lines: 64 / 4 = **16 lines**
- Sets: 16 / 2 = **8 sets**
- Ways per set: **2**

### Address Bit Fields

**L1**:
- Offset bits: log₂(4) = **2 bits** (selects byte 0-3)
- Index bits: log₂(4) = **2 bits** (selects set 0-3)
- Tag bits: 32 - 2 - 2 = **28 bits**

**L2**:
- Offset bits: log₂(4) = **2 bits**
- Index bits: log₂(8) = **3 bits** (selects set 0-7)
- Tag bits: 32 - 2 - 3 = **27 bits**

---

## Memory Trace

From `input.txt`:
```
00000000 , R
00000004 , R
00000000 , R
00000010 , R
00000000 , R
00000000 , W
```

---

## Step-by-Step Execution

### Access 1: Read 0x00000000

**Address breakdown**:
```
0x00000000 = 0000 0000 0000 0000 0000 0000 0000 0000

L1: tag=0, index=0, offset=0
L2: tag=0, index=0, offset=0
```

**Execution**:
1. Check L1 set 0 for tag 0 → **MISS** (empty)
2. Check L2 set 0 for tag 0 → **MISS** (empty)
3. Load from memory → **MEMACC**
4. Insert into L2 set 0, way 0
5. Insert into L1 set 0

**Result**: `MEMACC`

**Cache state**:
```
L1 Set 0: [tag=0, valid=1, lru=1]
L2 Set 0: [tag=0, valid=1, lru=1] [empty]
```

---

### Access 2: Read 0x00000004

**Address breakdown**:
```
0x00000004 = 0000 0000 0000 0000 0000 0000 0000 0100

L1: tag=0, index=1, offset=0
L2: tag=0, index=1, offset=0
```

**Execution**:
1. Check L1 set 1 for tag 0 → **MISS** (empty)
2. Check L2 set 1 for tag 0 → **MISS** (empty)
3. Load from memory → **MEMACC**
4. Insert into L2 set 1, way 0
5. Insert into L1 set 1

**Result**: `MEMACC`

**Cache state**:
```
L1 Set 0: [tag=0, valid=1, lru=1]
L1 Set 1: [tag=0, valid=1, lru=2]

L2 Set 0: [tag=0, valid=1, lru=1] [empty]
L2 Set 1: [tag=0, valid=1, lru=2] [empty]
```

---

### Access 3: Read 0x00000000

**Address breakdown**:
```
L1: tag=0, index=0, offset=0
L2: tag=0, index=0, offset=0
```

**Execution**:
1. Check L1 set 0 for tag 0 → **HIT!**
2. Update LRU counter

**Result**: `L1HIT`

**Cache state**:
```
L1 Set 0: [tag=0, valid=1, lru=3]  ← Updated!
L1 Set 1: [tag=0, valid=1, lru=2]

L2 Set 0: [tag=0, valid=1, lru=3]  ← Also updated!
L2 Set 1: [tag=0, valid=1, lru=2]
```

---

### Access 4: Read 0x00000010

**Address breakdown**:
```
0x00000010 = 0000 0000 0000 0000 0000 0000 0001 0000

L1: tag=1, index=0, offset=0
L2: tag=0, index=4, offset=0
```

**Key observation**: 
- In L1: maps to **set 0** (same as 0x00000000)
- In L2: maps to **set 4** (different set)

**Execution**:
1. Check L1 set 0 for tag 1 → **MISS** (has tag 0)
2. Check L2 set 4 for tag 0 → **MISS** (empty)
3. Load from memory → **MEMACC**
4. Insert into L2 set 4, way 0
5. Insert into L1 set 0 (evicts tag 0)

**Result**: `MEMACC`

**Cache state**:
```
L1 Set 0: [tag=1, valid=1, lru=4]  ← Replaced! (was tag=0)
L1 Set 1: [tag=0, valid=1, lru=2]

L2 Set 0: [tag=0, valid=1, lru=3]  ← Still here!
L2 Set 1: [tag=0, valid=1, lru=2]
L2 Set 4: [tag=0, valid=1, lru=4]  ← New!
```

**Important**: Tag 0 was evicted from L1 but still exists in L2 (allowed in inclusive cache).

---

### Access 5: Read 0x00000000

**Address breakdown**:
```
L1: tag=0, index=0, offset=0
L2: tag=0, index=0, offset=0
```

**Execution**:
1. Check L1 set 0 for tag 0 → **MISS** (now has tag 1)
2. Check L2 set 0 for tag 0 → **HIT!** (still there from Access 1)
3. Insert into L1 set 0 (evicts tag 1)

**Result**: `L2HIT`

**Cache state**:
```
L1 Set 0: [tag=0, valid=1, lru=5]  ← Brought back!
L1 Set 1: [tag=0, valid=1, lru=2]

L2 Set 0: [tag=0, valid=1, lru=5]  ← Updated LRU
L2 Set 1: [tag=0, valid=1, lru=2]
L2 Set 4: [tag=0, valid=1, lru=4]
```

---

### Access 6: Write 0x00000000

**Address breakdown**:
```
L1: tag=0, index=0, offset=0
L2: tag=0, index=0, offset=0
```

**Execution**:
1. Check L1 set 0 for tag 0 → **HIT!**
2. Update LRU counter
3. (Write-through: also updates L2)

**Result**: `L1HIT`

**Cache state**:
```
L1 Set 0: [tag=0, valid=1, lru=6]  ← Updated!
L1 Set 1: [tag=0, valid=1, lru=2]

L2 Set 0: [tag=0, valid=1, lru=6]  ← Updated!
L2 Set 1: [tag=0, valid=1, lru=2]
L2 Set 4: [tag=0, valid=1, lru=4]
```

---

## Complete Results

```
MEMACC  (Access 1: 0x00000000 R)
MEMACC  (Access 2: 0x00000004 R)
L1HIT   (Access 3: 0x00000000 R)
MEMACC  (Access 4: 0x00000010 R)
L2HIT   (Access 5: 0x00000000 R)
L1HIT   (Access 6: 0x00000000 W)
```

This matches the expected output in `output.txt`!

---

## Key Insights

### 1. Address Conflicts

Addresses 0x00000000 and 0x00000010:
- Both map to **L1 set 0** (conflict!)
- Map to **different L2 sets** (no conflict)

This is why:
- Access 4 evicts 0x00000000 from L1
- But 0x00000000 still in L2
- Access 5 finds it in L2 → L2HIT

### 2. Inclusive Cache Behavior

After Access 4:
```
L1 has: 0x00000010 in set 0
L2 has: 0x00000000 in set 0, 0x00000010 in set 4
```

L1 ⊆ L2 is maintained:
- Everything in L1 (0x00000010) is also in L2 ✓
- L2 can have extra data (0x00000000) ✓

### 3. Write Behavior

Access 6 (write to 0x00000000):
- Found in L1 → L1HIT
- No-write-allocate doesn't matter (it's a hit)
- Write-through updates both L1 and L2

---

## Timeline Visualization

```
Time  Address    Op  L1 State        L2 State        Result
────────────────────────────────────────────────────────────
1     0x00000000 R   [0₁,-,-,-]     [0₁,...]        MEMACC
2     0x00000004 R   [0₁,0₂,-,-]    [0₁,0₂,...]     MEMACC
3     0x00000000 R   [0₃,0₂,-,-]    [0₃,0₂,...]     L1HIT
4     0x00000010 R   [1₄,0₂,-,-]    [0₃,0₂,-,-,0₄]  MEMACC
5     0x00000000 R   [0₅,0₂,-,-]    [0₅,0₂,-,-,0₄]  L2HIT
6     0x00000000 W   [0₆,0₂,-,-]    [0₆,0₂,-,-,0₄]  L1HIT

Format: [Set0,Set1,Set2,Set3] for L1
        Subscripts show LRU counter values
        First number in each entry is tag
```

---

## Testing Edge Cases

Based on this example, here are interesting test cases:

### Test 1: Write Miss (No-Write-Allocate)
```
Input:
  0x00000000 , W
  0x00000000 , R

Expected:
  MEMACC  (write miss: don't allocate)
  MEMACC  (read miss: wasn't loaded)
```

### Test 2: L2 Eviction with Inclusive
```
Fill L2 completely, then:
- Add new address (evicts from L2)
- Verify evicted address invalidated from L1
```

### Test 3: Conflict Pattern
```
Alternately access 0x00000000 and 0x00000010:
- Both map to same L1 set
- Should see L2HIT pattern
```

---

## Debugging Tips

If your output doesn't match:

1. **Print address parsing**:
   ```python
   print(f"Address 0x{address:08X} → L1: tag={tag1}, index={idx1}")
   ```

2. **Print cache state after each access**:
   ```python
   print(f"L1 Set {idx}: {self.l1.sets[idx].lines}")
   ```

3. **Verify LRU ordering**:
   ```python
   print(f"LRU counters: {[line.lru_counter for line in set.lines]}")
   ```

4. **Check evictions**:
   ```python
   if evicted:
       print(f"Evicted: 0x{evicted:08X}")
   ```
