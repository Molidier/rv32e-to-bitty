# shared_memory.py
import random

_shared_memory = None

def generate_shared_memory(size=2048):
    global _shared_memory
    if _shared_memory is None:
        _shared_memory = [random.randint(0, 0xFFF) for _ in range(size)]
    return _shared_memory