# Usage Guide

This guide explains how to run and test the cache simulator.

## Running the Simulator

### Command Line Usage

```bash
python cache_sim.py <config_file> <trace_file> <output_file>
```

### Parameters

- `config_file`: Configuration file with cache parameters
- `trace_file`: File containing memory accesses
- `output_file`: Where to write results

### Example

```bash
python cache_sim.py def.txt input.txt output.txt
```

---

## Configuration File Format

### Syntax

Single line with 6 comma-separated values:

```
CACHE_LINE_SIZE, CACHE_INCLUSIVE, L1_NUM_WAYS, L1_DATA_SIZE, L2_NUM_WAYS, L2_DATA_SIZE
```

### Parameters Explained

| Parameter | Description | Example |
|-----------|-------------|---------|
| `CACHE_LINE_SIZE` | Bytes per cache line (for both L1 and L2) | 4 |
| `CACHE_INCLUSIVE` | TRUE or FALSE (is L1 ⊆ L2?) | TRUE |
| `L1_NUM_WAYS` | Number of ways in L1 (1 = direct-mapped) | 1 |
| `L1_DATA_SIZE` | Total data bytes in L1 (excluding tags) | 16 |
| `L2_NUM_WAYS` | Number of ways in L2 | 2 |
| `L2_DATA_SIZE` | Total data bytes in L2 | 64 |

### Example Configuration

```
4, TRUE, 1, 16, 2, 64
```

This means:
- **Line size**: 4 bytes
- **Inclusive**: Yes (L1 ⊆ L2)
- **L1**: Direct-mapped (1-way), 16 bytes data = 4 lines
- **L2**: 2-way set-associative, 64 bytes data = 16 lines = 8 sets

### Constraints

All numeric values must be:
- Powers of 2 (including 1)
- Line size ≥ 2
- L2 must be larger than L1

---

## Trace File Format

### Syntax

Each line contains:
```
<ADDRESS> , <OPERATION>
```

### Components

- `ADDRESS`: Hexadecimal address (without `0x` prefix)
- `OPERATION`: Either `R` (read) or `W` (write)

### Example Trace File

```
00000000 , R
00000004 , R
00000000 , R
00000010 , R
00000000 , W
```

### Notes

- Addresses are in hexadecimal
- No `0x` prefix needed
- Spaces around commas are optional
- Case-insensitive for R/W

---

## Output File Format

### Syntax

One line per memory access:
```
L1HIT
L2HIT
MEMACC
```

### Results Explained

- `L1HIT`: Data found in L1 cache
- `L2HIT`: Data not in L1, but found in L2
- `MEMACC`: Data not in any cache, accessed from main memory

### Example Output

```
MEMACC
MEMACC
L1HIT
MEMACC
L2HIT
L1HIT
```

---

## Complete Example

### Step 1: Create Configuration File (def.txt)

```
4, TRUE, 1, 16, 2, 64
```

### Step 2: Create Trace File (input.txt)

```
00000000 , R
00000004 , R
00000000 , R
00000010 , R
00000000 , R
00000000 , W
```

### Step 3: Run Simulator

```bash
python cache_sim.py def.txt input.txt output.txt
```

### Step 4: Check Output (output.txt)

```
MEMACC
MEMACC
L1HIT
MEMACC
L2HIT
L1HIT
```

---

## Testing Your Implementation

### Provided Test Cases

The assignment includes two test cases:
1. `def.txt`, `input.txt`, `output.txt`
2. `def2.txt`, `input2.txt`, `output2.txt`

### Verify Correctness

```bash
# Test 1
python cache_sim.py def.txt input.txt my_output.txt
diff my_output.txt output.txt

# Test 2
python cache_sim.py def2.txt input2.txt my_output2.txt
diff my_output2.txt output2.txt
```

If `diff` produces no output, the tests pass!

### Create Your Own Tests

To build intuition, create simple test cases:

**Test: Direct-Mapped, Single Address**
```
Config: 4, FALSE, 1, 16, 1, 64
Trace:
  00000000 , R
  00000000 , R
Expected:
  MEMACC  (first access: miss)
  L1HIT   (second access: hit)
```

**Test: Write Miss (No-Write-Allocate)**
```
Config: 4, FALSE, 1, 16, 1, 64
Trace:
  00000000 , W
  00000000 , R
Expected:
  MEMACC  (write miss: don't allocate)
  MEMACC  (read miss: wasn't allocated)
```

---

## Common Issues

### Issue 1: Command Not Found

```
python: command not found
```

**Solution**: Try `python3` instead:
```bash
python3 cache_sim.py def.txt input.txt output.txt
```

### Issue 2: File Not Found

```
FileNotFoundError: [Errno 2] No such file or directory: 'def.txt'
```

**Solution**: Make sure you're in the correct directory:
```bash
ls  # Check if files exist
pwd  # Check current directory
```

### Issue 3: Wrong Output

If your output doesn't match expected:

1. **Check configuration parsing**: Print parsed values
2. **Trace execution**: Add debug prints for each access
3. **Verify calculations**: Check num_sets, index_bits, etc.
4. **Test incrementally**: Start with simple traces

### Issue 4: Hex Parsing

```
ValueError: invalid literal for int() with base 16
```

**Solution**: Make sure addresses are valid hexadecimal:
- ✅ `00000000`
- ✅ `ABCDEF12`
- ❌ `0x00000000` (remove `0x`)
- ❌ `GHIJK` (invalid hex)

---

## Debug Mode (Optional Enhancement)

You can add verbose output for debugging:

```python
def main():
    # ... existing code ...
    
    # Add debug flag
    debug = '--debug' in sys.argv
    
    for address, operation in parse_trace(trace_file):
        result = sim.memory_access(address, operation)
        
        if debug:
            print(f"Address: 0x{address:08X}, Op: {operation}, Result: {result}")
        
        out.write(result + '\n')
```

Usage:
```bash
python cache_sim.py def.txt input.txt output.txt --debug
```

---

## Performance Testing

### Large Traces

To test with larger workloads:

```python
# generate_trace.py
for i in range(10000):
    address = i * 4  # Sequential addresses
    print(f"{address:08X} , R")
```

```bash
python generate_trace.py > large_trace.txt
python cache_sim.py def.txt large_trace.txt large_output.txt
```

### Timing

```bash
time python cache_sim.py def.txt large_trace.txt output.txt
```

---

## Requirements Checklist

Before submission, verify:

- ✅ Python 3.10+ compatible
- ✅ Standard library only (no external packages)
- ✅ Correct command-line interface
- ✅ Handles both test cases correctly
- ✅ Proper file I/O
- ✅ No hardcoded values (all configurable)
- ✅ Clean, readable code
- ✅ Proper error handling (optional but recommended)

---

## Submission

Package your submission:

```bash
zip hw1_submission.zip cache_sim.py hw1.pdf
```

The zip should contain:
- `cache_sim.py` - Your implementation
- `hw1.pdf` - Dry part answers

---

## Additional Resources

### Understanding Your Configuration

To understand what your configuration creates:

```python
# calc_cache_params.py
line_size = 4
l1_ways = 1
l1_data = 16

l1_lines = l1_data / line_size
l1_sets = l1_lines / l1_ways

print(f"L1: {l1_lines} lines, {l1_sets} sets, {l1_ways}-way")
```

### Visualizing Address Mapping

```python
# show_mapping.py
def parse(addr, offset_bits, index_bits):
    offset = addr & ((1 << offset_bits) - 1)
    index = (addr >> offset_bits) & ((1 << index_bits) - 1)
    tag = addr >> (offset_bits + index_bits)
    print(f"0x{addr:08X} → tag={tag}, index={index}, offset={offset}")

# Example
parse(0x00000000, 2, 2)  # tag=0, index=0, offset=0
parse(0x00000004, 2, 2)  # tag=0, index=1, offset=0
parse(0x00000010, 2, 2)  # tag=1, index=0, offset=0
```
