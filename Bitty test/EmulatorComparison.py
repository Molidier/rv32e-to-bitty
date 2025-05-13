"""
EmulatorComparison.py - Compare RISCV32EMEmulator and BittyEmulator execution
"""
from RISCV32EMEmulator import RISCV32EMEmulator
from BittyEmulator import BittyEmulator
from shared_memory import generate_shared_memory
import copy  # Import copy to make a deep copy of initial memory

def load_instructions_from_file(filename):
    """
    Reads RISC-V encodings from a file, one per line, in binary form
    like 0b0000000_00001_00000_000_01010_0010011.
    """
    instructions = []
    with open(filename, "r") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            # remove the visual underscores
            s = s.replace("_", "")
            # int(..., 0) will parse 0b... as binary, 0x... as hex, etc.
            try:
                inst = int(s, 0)
            except ValueError as e:
                print(f"Error parsing '{line.strip()}': {e}")
                continue
            # ensure we only keep the low 32 bits
            instructions.append(inst & 0xFFFFFFFF)
    return instructions



def write_to_file(message, filename="comparison_output.txt", mode="a"):
    """
    Write a message to the output file.
    
    Args:
        message: Text to write
        filename: Output file path
        mode: File open mode ('w' for write, 'a' for append)
    """
    with open(filename, mode) as file:
        file.write(message + "\n")
    # Also print to console for real-time feedback
    print(message)


def run_riscv(riscv, instructions, max_instructions=1000):
    """
    Run the RISCV emulator on the given instructions.
    
    Args:
        riscv: RISCV32EMEmulator instance
        instructions: List of instructions to execute
        max_instructions: Maximum number of instructions to execute (prevents infinite loops)
    
    Returns:
        Number of instructions executed
    """
    # Store and init instruction array
    riscv.instruction_array = instructions
    riscv.pc = 0
    
    # Track instruction count for safety
    count = 0
    
    write_to_file("\nRISC-V Execution Trace:")
    write_to_file("----------------------")
    
    # Run until max count or end of instructions
    while count < max_instructions and 0 <= riscv.pc < len(riscv.instruction_array):
        instr = riscv.fetch_instruction()
        write_to_file(f"Step {count}: PC={riscv.pc}, Instr=0x{instr:08X}")
        
        # Execute instruction and get next PC
        next_pc = riscv.decode_and_execute(instr)
        
        # Update PC
        riscv.pc = next_pc
        count += 1
        
        # Debug registers every few instructions
        if count % 10 == 0 or count < 5:
            reg_str = " ".join([f"x{i}={riscv.registers[i]:08X}" for i in range(4)])
            write_to_file(f"Registers: {reg_str}...")
    
    # Save final register state
    riscv.print_registers()
    
    return count


def run_bitty(bitty, instructions, max_instructions=1000):
    """
    Run the BittyEmulator on the given instructions.
    
    Args:
        bitty: BittyEmulator instance
        instructions: List of instructions to execute
        max_instructions: Maximum number of instructions to execute (prevents infinite loops)
    
    Returns:
        Final PC value
    """
    # Set memory to our instructions
    bitty.memory = instructions.copy()
    bitty.pc = 0
    
    write_to_file("\nBitty Execution Trace:")
    write_to_file("---------------------")
    
    # Track instruction count for safety
    count = 0
    
    # Run until max count or end of instructions
    while count < max_instructions and 0 <= bitty.pc < len(bitty.memory):
        instr = bitty.memory[bitty.pc]
        write_to_file(f"Step {count}: PC={bitty.pc}, Instr=0x{instr:04X}")
        
        # Execute instruction and update PC internally
        next_pc = bitty.evaluate(instr)
        bitty.pc = next_pc
        count += 1
        
        # DEBUG: Periodically show some register values
        if count % 10 == 0 or count < 5:
            reg_str = " ".join([f"r{i}={bitty.registers[i]:08X}" for i in range(4)])
            write_to_file(f"Registers: {reg_str}...")
    
    # Save final register state
    bitty.print_registers()
    
    return count


def compare_memory_changes(initial_memory, current_memory, name="Memory"):
    """
    Compare initial memory state with current state and report changes.
    
    Args:
        initial_memory: Initial memory array
        current_memory: Current memory array after execution
        name: Name identifier for the memory comparison
        
    Returns:
        Tuple of (number of changes, total memory size)
    """
    changes = 0
    write_to_file(f"\n-- {name} Changes from Initial State --")
    write_to_file(f"{'Addr':<6}{'Initial':^12}{'Current':^12}{'Changed':^8}")
    write_to_file("-" * 40)
    
    memory_size = min(len(initial_memory), len(current_memory))
    
    # Check each memory location
    for addr in range(memory_size):
        initial_val = initial_memory[addr] & 0xFFFFFFFF
        current_val = current_memory[addr] & 0xFFFFFFFF
        
        if initial_val != current_val:
            changes += 1
            write_to_file(f"{addr:<6} 0x{initial_val:08X}  0x{current_val:08X}   ✗")
    
    # If no changes, note that as well
    if changes == 0:
        write_to_file("No memory changes detected")
    else:
        write_to_file(f"\nTotal memory changes: {changes}/{memory_size} ({changes/memory_size*100:.1f}%)")
    
    return changes, memory_size


def main():
    """Main comparison function"""
    # Reset output file
    write_to_file("=== Emulator Comparison ===", mode="w")
    write_to_file(f"Generated on: {__import__('datetime').datetime.now()}")

    # Create shared memory arrays with the same seed to ensure they're identical
    memory_size = 1024
    mem_seed = 42
    write_to_file(f"\nGenerating shared memory (size={memory_size}, seed={mem_seed})")
    
    mem_riscv = generate_shared_memory(size=memory_size, seed=mem_seed)
    mem_bitty = generate_shared_memory(size=memory_size, seed=mem_seed)

    # Make deep copies of initial memory state for later comparison
    mem_riscv_initial = copy.deepcopy(mem_riscv)
    mem_bitty_initial = copy.deepcopy(mem_bitty)

    # Verify the memory arrays are identical
    if mem_riscv[:10] == mem_bitty[:10]:
        write_to_file("Memory arrays initialized identically (verified first 10 elements)")
    else:
        write_to_file("WARNING: Memory arrays are not identical!")

    # Initialize emulators with their respective memory arrays
    riscv = RISCV32EMEmulator(memory_array=mem_riscv)
    bitty = BittyEmulator(memory=mem_bitty)

    # 1. Load & run RISC-V
    rv_insts = load_instructions_from_file("riscv_instructions.txt")
    write_to_file(f"\n-- Running RISC-V [{len(rv_insts)} instructions] --")
    rv_count = run_riscv(riscv, rv_insts)
    write_to_file(f"RISC-V executed {rv_count} instructions")

    # 2. Load & run Bitty
    bt_insts = load_instructions_from_file("bitty_binary.txt")
    write_to_file(f"\n-- Running Bitty [{len(bt_insts)} instructions] --")
    bt_count = run_bitty(bitty, bt_insts)
    write_to_file(f"Bitty executed {bt_count} instructions")

    # 3. Compare registers
    write_to_file("\n-- Register Comparison --")
    write_to_file(f"{'Reg':<6}{'RISC-V':^12}{'Bitty':^12}{'Match':^8}")
    write_to_file("-" * 40)
    
    # Count matching registers
    match_count = 0
    total_regs = min(len(riscv.registers), len(bitty.registers))
    
    # Compare all registers
    for reg in range(total_regs):
        rv_val = riscv.registers[reg] & 0xFFFFFFFF
        bt_val = bitty.registers[reg] & 0xFFFFFFFF
        match = "✓" if rv_val == bt_val else "✗"
        
        # Count matches
        if rv_val == bt_val:
            match_count += 1
            
        write_to_file(f"x{reg:<5} 0x{rv_val:08X}  0x{bt_val:08X}   {match}")
    
    write_to_file(f"\nRegister matches: {match_count}/{total_regs} ({match_count/total_regs*100:.1f}%)")

    # 4. Compare memory between emulators
    write_to_file("\n-- Memory Comparison Between Emulators --")
    write_to_file(f"{'Addr':<6}{'RISC-V':^12}{'Bitty':^12}{'Match':^8}")
    write_to_file("-" * 40)
    
    # Only check the first 50 memory locations (or modify as needed)
    memory_check_range = min(1000, len(mem_riscv), len(mem_bitty))
    memory_matches = 0
    
    for addr in range(memory_check_range):
        rv_word = mem_riscv[addr] & 0xFFFFFFFF
        bt_word = mem_bitty[addr] & 0xFFFFFFFF
        
        match = "✓" if rv_word == bt_word else "✗"
        if rv_word == bt_word:
            memory_matches += 1
            
        # Only show mismatches or first/last few elements
        if match == "✗" or addr < 50 or addr > memory_check_range - 5:
            write_to_file(f"{addr:<6} 0x{rv_word:08X}  0x{bt_word:08X}   {match}")
    
    write_to_file(f"\nMemory matches between emulators: {memory_matches}/{memory_check_range} ({memory_matches/memory_check_range*100:.1f}%)")

    # 5. Check memory changes from initial state
    riscv_changes, riscv_size = compare_memory_changes(
        mem_riscv_initial, mem_riscv, "RISC-V Memory"
    )
    
    bitty_changes, bitty_size = compare_memory_changes(
        mem_bitty_initial, mem_bitty, "Bitty Memory"
    )

    # 6. Compare memory change patterns
    write_to_file("\n-- Memory Change Pattern Comparison --")
    changed_same_locations = 0
    locations_changed_by_both = 0
    
    for addr in range(min(len(mem_riscv), len(mem_bitty))):
        riscv_changed = (mem_riscv_initial[addr] != mem_riscv[addr])
        bitty_changed = (mem_bitty_initial[addr] != mem_bitty[addr])
        
        if riscv_changed and bitty_changed:
            locations_changed_by_both += 1
            if mem_riscv[addr] == mem_bitty[addr]:
                changed_same_locations += 1
    
    write_to_file(f"Locations modified by both emulators: {locations_changed_by_both}")
    if locations_changed_by_both > 0:
        write_to_file(f"Locations modified identically: {changed_same_locations} ({changed_same_locations/locations_changed_by_both*100:.1f}%)")

    # Summary
    write_to_file("\n=== Comparison Summary ===")
    write_to_file(f"RISC-V ran {rv_count} instructions; Bitty ran {bt_count} instructions")
    write_to_file(f"Register match rate: {match_count/total_regs*100:.1f}%")
    write_to_file(f"Memory match rate between emulators: {memory_matches/memory_check_range*100:.1f}%")
    write_to_file(f"RISC-V memory changes: {riscv_changes}/{riscv_size} locations ({riscv_changes/riscv_size*100:.1f}% modified)")
    write_to_file(f"Bitty memory changes: {bitty_changes}/{bitty_size} locations ({bitty_changes/bitty_size*100:.1f}% modified)")
    
    # Output files locations
    write_to_file("\nDetailed register dumps can be found in:")
    write_to_file("- riscv_registers_output.txt")
    write_to_file("- bitty_registers_output.txt")


if __name__ == "__main__":
    main()