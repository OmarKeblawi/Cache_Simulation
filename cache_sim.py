import sys
from typing import Optional, Tuple


class CacheLine:
    """
    Represents a single cache line (also called a cache block).
    
    Each cache line stores:
    - valid: Whether this line contains valid data
    - tag: The tag portion of the address (used to identify which block this line holds)
    - lru_counter: Used for LRU replacement policy (higher = more recently used)
    """
    
    def __init__(self):
        self.valid = False
        self.tag = None
        self.lru_counter = 0
    
    def is_hit(self, tag: int) -> bool:
        """Check if this line contains the requested tag"""
        return self.valid and self.tag == tag
    
    def update(self, tag: int, lru_value: int):
        """Update this line with new tag and mark as most recently used"""
        self.valid = True
        self.tag = tag
        self.lru_counter = lru_value


class CacheSet:
    """
    Represents a set in a set-associative cache.
    
    A set contains multiple 'ways' (cache lines). For example:
    - Direct-mapped cache: 1 way per set
    - 2-way set-associative: 2 ways per set
    - Fully associative: 1 set with many ways
    
    This class implements the LRU (Least Recently Used) replacement policy.
    """
    
    def __init__(self, num_ways: int):
        self.num_ways = num_ways
        self.lines = [CacheLine() for _ in range(num_ways)]
        self.access_counter = 0  # Global counter for LRU tracking
    
    def find_line(self, tag: int) -> Optional[int]:
        """
        Search for a tag in this set.
        Returns the way index if found, None otherwise.
        """
        for i, line in enumerate(self.lines):
            if line.is_hit(tag):
                return i
        return None
    
    def access(self, tag: int) -> Tuple[bool, Optional[int]]:
        """
        Try to access a tag in this set.
        
        Returns:
            (hit, evicted_tag): 
            - hit: True if tag was found
            - evicted_tag: The tag that was evicted (if any), None otherwise
        """
        # Check if it's a hit
        way_index = self.find_line(tag)
        if way_index is not None:
            # Hit: update LRU counter
            self.access_counter += 1
            self.lines[way_index].lru_counter = self.access_counter
            return True, None
        
        # Miss: need to insert the tag
        return False, None
    
    def insert(self, tag: int) -> Optional[int]:
        """
        Insert a new tag into this set using LRU replacement.
        
        Returns:
            evicted_tag: The tag that was evicted (if any), None if there was an empty line
        """
        # First, try to find an invalid (empty) line
        for line in self.lines:
            if not line.valid:
                self.access_counter += 1
                line.update(tag, self.access_counter)
                return None
        
        # All lines are valid, need to evict the LRU line
        lru_index = min(range(self.num_ways), key=lambda i: self.lines[i].lru_counter)
        evicted_tag = self.lines[lru_index].tag
        
        self.access_counter += 1
        self.lines[lru_index].update(tag, self.access_counter)
        
        return evicted_tag
    
    def invalidate(self, tag: int) -> bool:
        """
        Invalidate a line with the given tag (used for inclusive cache policy).
        
        Returns:
            True if the tag was found and invalidated, False otherwise
        """
        way_index = self.find_line(tag)
        if way_index is not None:
            self.lines[way_index].valid = False
            self.lines[way_index].tag = None
            return True
        return False


class Cache:
    """
    Represents a cache level (L1 or L2).
    
    The cache is organized as:
    - Multiple sets (determined by DATA_SIZE / (LINE_SIZE * NUM_WAYS))
    - Each set contains NUM_WAYS lines
    
    Address breakdown (32 bits total):
    - Tag bits: identify which memory block
    - Index bits: select which set
    - Offset bits: select byte within cache line
    """
    
    def __init__(self, line_size: int, num_ways: int, data_size: int, name: str = "Cache"):
        self.line_size = line_size
        self.num_ways = num_ways
        self.data_size = data_size
        self.name = name
        
        # Calculate number of sets
        # Total lines = data_size / line_size
        # Number of sets = total_lines / num_ways
        total_lines = data_size // line_size
        self.num_sets = total_lines // num_ways
        
        # Create the sets
        self.sets = [CacheSet(num_ways) for _ in range(self.num_sets)]
        
        # Calculate bit widths for address parsing
        self.offset_bits = self._log2(line_size)
        self.index_bits = self._log2(self.num_sets)
        self.tag_bits = 32 - self.offset_bits - self.index_bits
    
    @staticmethod
    def _log2(n: int) -> int:
        """Calculate log2 of n (assumes n is a power of 2)"""
        if n == 1:
            return 0
        count = 0
        while n > 1:
            n //= 2
            count += 1
        return count
    
    def _parse_address(self, address: int) -> Tuple[int, int, int]:
        """
        Parse a 32-bit address into tag, index, and offset.
        
        Returns:
            (tag, index, offset)
        """
        offset = address & ((1 << self.offset_bits) - 1)
        index = (address >> self.offset_bits) & ((1 << self.index_bits) - 1)
        tag = address >> (self.offset_bits + self.index_bits)
        
        return tag, index, offset
    
    def access(self, address: int) -> bool:
        """
        Try to access an address in this cache.
        
        Returns:
            True if hit, False if miss
        """
        tag, index, _ = self._parse_address(address)
        hit, _ = self.sets[index].access(tag)
        return hit
    
    def insert(self, address: int) -> Optional[int]:
        """
        Insert an address into this cache (on a miss).
        
        Returns:
            evicted_address: The full address that was evicted (if any), None otherwise
        """
        tag, index, _ = self._parse_address(address)
        evicted_tag = self.sets[index].insert(tag)
        
        if evicted_tag is not None:
            # Reconstruct the full address from the evicted tag
            evicted_address = (evicted_tag << (self.offset_bits + self.index_bits)) | (index << self.offset_bits)
            return evicted_address
        
        return None
    
    def invalidate(self, address: int) -> bool:
        """
        Invalidate a cache line containing the given address.
        Used for inclusive cache policy.
        
        Returns:
            True if invalidated, False if not found
        """
        tag, index, _ = self._parse_address(address)
        return self.sets[index].invalidate(tag)


class CacheSimulator:
    """
    Simulates a two-level cache hierarchy with L1, L2, and main memory.
    
    Policies implemented:
    - LRU replacement
    - Write-through (writes go to lower levels)
    - No-write-allocate (write misses don't allocate in cache)
    - Optional inclusive cache (L1 ⊆ L2)
    """
    
    def __init__(self, line_size: int, inclusive: bool, 
                 l1_num_ways: int, l1_data_size: int,
                 l2_num_ways: int, l2_data_size: int):
        
        self.line_size = line_size
        self.inclusive = inclusive
        
        # Create L1 and L2 caches
        self.l1 = Cache(line_size, l1_num_ways, l1_data_size, "L1")
        self.l2 = Cache(line_size, l2_num_ways, l2_data_size, "L2")
    
    def memory_access(self, address: int, operation: str) -> str:
        """
        Simulate a memory access.
        
        Args:
            address: The memory address to access
            operation: 'R' for read, 'W' for write
        
        Returns:
            'L1HIT', 'L2HIT', or 'MEMACC'
        """
        if operation == 'R':
            return self._handle_read(address)
        else:  # operation == 'W'
            return self._handle_write(address)
    
    def _handle_read(self, address: int) -> str:
        """
        Handle a read operation.
        
        Read policy:
        - L1 hit: return L1HIT
        - L1 miss, L2 hit: load to L1, return L2HIT
        - L1 miss, L2 miss: load to both L1 and L2, return MEMACC
        """
        # Check L1
        if self.l1.access(address):
            return "L1HIT"
        
        # L1 miss, check L2
        if self.l2.access(address):
            # L2 hit: load into L1
            evicted_address = self.l1.insert(address)
            # Note: evicted_address is handled by inclusive policy if needed
            return "L2HIT"
        
        # L2 miss: load into both L2 and L1
        evicted_l2_address = self.l2.insert(address)
        
        # Handle inclusive cache: if L2 evicts, invalidate from L1
        if self.inclusive and evicted_l2_address is not None:
            self.l1.invalidate(evicted_l2_address)
        
        # Now insert into L1
        self.l1.insert(address)
        
        return "MEMACC"
    
    def _handle_write(self, address: int) -> str:
        """
        Handle a write operation.
        
        Write policy (write-through + no-write-allocate):
        - L1 hit: return L1HIT
        - L1 miss, L2 hit: don't load to L1, return L2HIT
        - L1 miss, L2 miss: don't load anywhere, return MEMACC
        """
        # Check L1
        if self.l1.access(address):
            return "L1HIT"
        
        # L1 miss, check L2
        if self.l2.access(address):
            # L2 hit: don't load into L1 (no-write-allocate)
            return "L2HIT"
        
        # Both miss: don't allocate (no-write-allocate)
        return "MEMACC"


def parse_config(config_file: str) -> Tuple[int, bool, int, int, int, int]:
    """Parse the configuration file."""
    with open(config_file, 'r') as f:
        line = f.readline().strip()
        parts = [p.strip() for p in line.split(',')]
        
        line_size = int(parts[0])
        inclusive = parts[1].upper() == 'TRUE'
        l1_num_ways = int(parts[2])
        l1_data_size = int(parts[3])
        l2_num_ways = int(parts[4])
        l2_data_size = int(parts[5])
        
        return line_size, inclusive, l1_num_ways, l1_data_size, l2_num_ways, l2_data_size


def parse_trace(trace_file: str):
    """Generator that yields memory accesses from the trace file."""
    with open(trace_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            parts = [p.strip() for p in line.split(',')]
            address = int(parts[0], 16)  # Parse hex address
            operation = parts[1].upper()  # 'R' or 'W'
            
            yield address, operation


def main():
    if len(sys.argv) != 4:
        print("Usage: python cache_sim.py <config_file> <trace_file> <output_file>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    trace_file = sys.argv[2]
    output_file = sys.argv[3]
    
    # Parse configuration
    line_size, inclusive, l1_num_ways, l1_data_size, l2_num_ways, l2_data_size = parse_config(config_file)
    
    # Create simulator
    sim = CacheSimulator(line_size, inclusive, l1_num_ways, l1_data_size, l2_num_ways, l2_data_size)
    
    # Process trace and write output
    with open(output_file, 'w') as out:
        for address, operation in parse_trace(trace_file):
            result = sim.memory_access(address, operation)
            out.write(result + '\n')


if __name__ == '__main__':
    main()
