"""
shared_memory.py - Generate shared memory arrays for emulator comparison
"""

def generate_shared_memory(size=1024, seed=42):
    """
    Generate a memory array with consistent initial values for both emulators.
    
    Args:
        size: Size of the memory array to generate
        seed: Random seed for reproducibility
        
    Returns:
        A list representing memory with initialized values
    """
    import random
    random.seed(seed)
    
    # Create memory array with some non-zero initial values
    memory = []
    for i in range(size):
        # Generate values that are different based on address for easier debugging
        # Using a deterministic pattern based on the address
        if i % 16 == 0:
            # Every 16th word has a special pattern
            memory.append(0xA0000000 + i)
        elif i % 4 == 0:
            # Every 4th word has a different pattern
            memory.append(0x10000000 + (i * 16))
        else:
            # Other words get semi-random values
            memory.append(random.randint(0, 0xFFFFFFFF))
    
    return memory