"""
EmulatorComparison.py - Compare RISCV32EMEmulator and BittyEmulator execution
"""
from RISCV32EMEmulator import RISCV32EMEmulator
from BittyEmulator import BittyEmulator
from shared_memory import generate_shared_memory
import copy  # Import copy to make a deep copy of initial memory

def read_ints_from_file(filename = "pc_map_output.txt"):
    with open(filename, 'r') as f:
        return [
            int(line)
            for line in (l.strip() for l in f)
            if line and line.isdigit()
        ]


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
    #print(message)


def compare_registers(riscv, bitty):
    """
    Compare registers between RISC-V and Bitty emulators.
    
    Args:
        riscv: RISCV32EMEmulator instance
        bitty: BittyEmulator instance
        
    Returns:
        Tuple of (match count, total registers compared)
    """
    write_to_file("\n-- Register Comparison at RV PC={}, Bitty PC={} --".format(riscv.pc, bitty.pc))
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
    return match_count, total_regs


def compare_memory(mem_riscv, mem_bitty, check_range=500):
    """
    Compare memory between RISC-V and Bitty emulators.
    
    Args:
        mem_riscv: RISC-V memory array
        mem_bitty: Bitty memory array
        check_range: Number of memory locations to check
        
    Returns:
        Tuple of (match count, total memory locations compared)
    """
    write_to_file("\n-- Memory Comparison Between Emulators --")
    write_to_file(f"{'Addr':<6}{'RISC-V':^12}{'Bitty':^12}{'Match':^8}")
    write_to_file("-" * 40)
    
    # Check specified range of memory locations
    memory_check_range = min(check_range, len(mem_riscv), len(mem_bitty))
    memory_matches = 0
    
    for addr in range(memory_check_range):
        rv_word = mem_riscv[addr] & 0xFFFFFFFF
        bt_word = mem_bitty[addr] & 0xFFFFFFFF
        
        match = "✓" if rv_word == bt_word else "✗"
        if rv_word == bt_word:
            memory_matches += 1
            
        # Only show mismatches or first/last few elements
        if match == "✗" or addr < 5 or addr > memory_check_range - 5:
            write_to_file(f"{addr:<6} 0x{rv_word:08X}  0x{bt_word:08X}   {match}")
    
    write_to_file(f"\nMemory matches between emulators: {memory_matches}/{memory_check_range} ({memory_matches/memory_check_range*100:.1f}%)")
    return memory_matches, memory_check_range


def run_riscv(riscv, instructions, map_pc, bitty, mem_riscv, mem_bitty_data, max_instructions=1000):
    """
    Run the RISCV emulator on the given instructions and coordinate with Bitty execution.
    
    Args:
        riscv: RISCV32EMEmulator instance
        instructions: List of RISC-V instructions to execute
        map_pc: Mapping from RISC-V PC to Bitty PC
        bitty: BittyEmulator instance
        mem_riscv: RISC-V memory array
        mem_bitty_data: Bitty data memory array (not instruction memory)
        max_instructions: Maximum number of instructions to execute (prevents infinite loops)
    
    Returns:
        Number of instructions executed
    """
    # Store and init instruction array
    riscv.instruction_array = instructions
    riscv.pc = 0
    
    # Track instruction count for safety
    count = 0
    bitty_total_count = 0
    
    write_to_file("\nCoordinated Execution Trace:")
    write_to_file("---------------------------")
    
    # Run until max count or end of instructions
    while count < max_instructions and 0 <= riscv.pc < len(riscv.instruction_array):
        old_pc = riscv.pc
        instr = riscv.fetch_instruction()
        write_to_file(f"\nRISC-V Step {count}: PC={old_pc}, Instr=0x{instr:08X}")
        
        # Execute instruction and get next PC
        next_pc = riscv.decode_and_execute(instr)
        
        # Update PC
        riscv.pc = next_pc
        count += 1
        
        # Print register state after execution
        reg_str = " ".join([f"x{i}={riscv.registers[i]:08X}" for i in range(4)])
        write_to_file(f"RISC-V Registers after step: {reg_str}...")
        
        # Now run Bitty until it reaches the PC corresponding to the next RISC-V PC
        # Look up the mapped PC for this RISC-V PC
        if riscv.pc < len(map_pc):
            target_bitty_pc = map_pc[riscv.pc]
            
            write_to_file(f"Running Bitty until PC={target_bitty_pc} (mapped from RISC-V PC={riscv.pc})")
            bitty_steps = run_bitty_to_pc(bitty, target_bitty_pc, max_instructions=1000)
            bitty_total_count += bitty_steps
            
            # Compare state at corresponding points
            write_to_file(f"\n=== State comparison at RISC-V PC={riscv.pc}, Bitty PC={bitty.pc} ===")
            reg_matches, total_regs = compare_registers(riscv, bitty)
            # FIXED: Compare RISC-V memory with Bitty's data_memory
            mem_matches, mem_check_range = compare_memory(mem_riscv, mem_bitty_data, check_range=500)
        else:
            write_to_file(f"Warning: RISC-V PC={riscv.pc} is outside the PC mapping range!")
    
    # Save final register state
    riscv.print_registers()
    
    return count, bitty_total_count


def run_bitty_to_pc(bitty, target_pc, max_instructions=1000):
    """
    Run the BittyEmulator until it reaches the target PC.
    
    Args:
        bitty: BittyEmulator instance
        target_pc: Target PC to run to
        max_instructions: Maximum number of instructions to execute (prevents infinite loops)
    
    Returns:
        Number of instructions executed
    """
    count = 0
    
    # Run until max count, end of instructions, or target PC is reached
    while count < max_instructions and 0 <= bitty.pc < len(bitty.instruction_array):  # FIXED: Use instruction_array
        # If we've reached the target PC, stop
        if bitty.pc == target_pc:
            write_to_file(f"Bitty reached target PC={target_pc} after {count} steps")
            break
            
        # FIXED: Get instruction from instruction_array, not memory
        instr = bitty.instruction_array[bitty.pc]
        write_to_file(f"Bitty Step {count}: PC={bitty.pc}, Instr=0x{instr:04X}")
        
        # Execute instruction and update PC internally
        next_pc = bitty.evaluate(instr)
        bitty.pc = next_pc
        count += 1
        
        # Show register values occasionally
        if count % 10 == 0 or count < 5:
            reg_str = " ".join([f"r{i}={bitty.registers[i]:08X}" for i in range(4)])
            write_to_file(f"Bitty Registers: {reg_str}...")
    
    # Check if we exited due to hitting max instructions
    if count >= max_instructions:
        write_to_file(f"Warning: Reached max instructions ({max_instructions}) before reaching target PC")
    
    return count


def main():
    """Main comparison function"""
    # Reset output file
    write_to_file("=== Emulator Comparison with PC Mapping ===", mode="w")
    write_to_file(f"Generated on: {__import__('datetime').datetime.now()}")

    # Create shared memory arrays with the same seed to ensure they're identical
    memory_size = 1024
    mem_seed = 42
    write_to_file(f"\nGenerating shared memory (size={memory_size}, seed={mem_seed})")
    
    mem_riscv = generate_shared_memory(size=memory_size, seed=mem_seed)
    # FIXED: For Bitty, we need to properly set up data memory
    mem_bitty_data = generate_shared_memory(size=memory_size, seed=mem_seed)

    # Make deep copies of initial memory state for later comparison
    mem_riscv_initial = copy.deepcopy(mem_riscv)
    mem_bitty_data_initial = copy.deepcopy(mem_bitty_data)

    # Verify the memory arrays are identical
    if mem_riscv[:10] == mem_bitty_data[:10]:
        write_to_file("Memory arrays initialized identically (verified first 10 elements)")
    else:
        write_to_file("WARNING: Memory arrays are not identical!")

    # Initialize emulators with their respective memory arrays
    riscv = RISCV32EMEmulator(memory_array=mem_riscv)
    # FIXED: Initialize BittyEmulator with data memory
    bitty = BittyEmulator(data_memory_size=memory_size, memory=mem_bitty_data)

    # Load mapping of RV PC to Bitty PC
    # index of map_pc is the PC of RV, and value is the corresponding Bitty PC
    map_pc = read_ints_from_file("pc_map_output.txt")
    write_to_file(f"Loaded PC mapping with {len(map_pc)} entries")

    # Load instructions
    rv_insts = load_instructions_from_file("riscv_instructions.txt")
    write_to_file(f"\nLoaded RISC-V instructions: {len(rv_insts)} instructions")
    
    bt_insts = load_instructions_from_file("bitty_binary.txt")
    write_to_file(f"Loaded Bitty instructions: {len(bt_insts)} instructions")
    
    # FIXED: Set Bitty's instruction_array properly instead of overwriting data memory
    bitty.instruction_array = bt_insts.copy()

    # Run coordinated execution
    write_to_file(f"\n-- Starting coordinated execution --")
    # FIXED: Pass the correct Bitty data memory reference
    rv_count, bitty_count = run_riscv(riscv, rv_insts, map_pc, bitty, mem_riscv, bitty.data_memory)
    
    write_to_file(f"\nRISC-V executed {rv_count} instructions")
    write_to_file(f"Bitty executed {bitty_count} instructions")

    # 5. Check memory changes from initial state
    riscv_changes, riscv_size = compare_memory_changes(
        mem_riscv_initial, mem_riscv, "RISC-V Memory"
    )
    
    # FIXED: Compare changes to Bitty's data memory, not instruction memory
    bitty_changes, bitty_size = compare_memory_changes(
        mem_bitty_data_initial, bitty.data_memory, "Bitty Memory"
    )

    # 6. Compare memory change patterns
    write_to_file("\n-- Memory Change Pattern Comparison --")
    changed_same_locations = 0
    locations_changed_by_both = 0
    
    # FIXED: Compare RISC-V memory with Bitty's data memory
    for addr in range(min(len(mem_riscv), len(bitty.data_memory))):
        riscv_changed = (mem_riscv_initial[addr] != mem_riscv[addr])
        bitty_changed = (mem_bitty_data_initial[addr] != bitty.data_memory[addr])
        
        if riscv_changed and bitty_changed:
            locations_changed_by_both += 1
            if mem_riscv[addr] == bitty.data_memory[addr]:
                changed_same_locations += 1
    
    write_to_file(f"Locations modified by both emulators: {locations_changed_by_both}")
    if locations_changed_by_both > 0:
        write_to_file(f"Locations modified identically: {changed_same_locations} ({changed_same_locations/locations_changed_by_both*100:.1f}%)")

    # Summary
    write_to_file("\n=== Comparison Summary ===")
    write_to_file(f"RISC-V ran {rv_count} instructions; Bitty ran {bitty_count} instructions")
    write_to_file(f"RISC-V memory changes: {riscv_changes}/{riscv_size} locations ({riscv_changes/riscv_size*100:.1f}% modified)")
    write_to_file(f"Bitty memory changes: {bitty_changes}/{bitty_size} locations ({bitty_changes/bitty_size*100:.1f}% modified)")
    
    # Output files locations
    write_to_file("\nDetailed register dumps can be found in:")
    write_to_file("- riscv_registers_output.txt")
    write_to_file("- bitty_registers_output.txt")


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


if __name__ == "__main__":
    main()