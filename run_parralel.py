# EmulatorComparison.py
from BittyEmulator import BittyEmulator
from RISCV32EMEmulator import RISCV32EMEmulator
from r_type import RiscVConverter

def load_instructions_from_file(filename, base=0):
    """
    Reads instructions from a text file, one per line.
    If base is 0, int() will auto-detect the base from the prefix.
    """
    instructions = []
    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments (lines starting with '#')
            if not line or line.startswith("#"):
                continue
            try:
                instructions.append(int(line, base))
            except ValueError as e:
                print(f"Error converting line '{line}': {e}")
    return instructions

def write_to_file(message, filename="comparison_output.txt"):
    """
    Write a message to the output file.
    """
    with open(filename, "a") as file:
        file.write(message + "\n")

def main():
    # Initialize both emulators
    bitty = BittyEmulator()
    riscv = RISCV32EMEmulator()
    translator = RiscVConverter()
   
    # Extend the BittyEmulator registers to 16 instead of 8 (for our comparison script only)
    if len(bitty.registers) == 8:
        bitty.registers.extend([10] * 8)  # Add 8 more registers to make it 16
   
    # Define mapping from RISC-V registers to Bitty registers (here 1:1 mapping)
    register_map = {i: i for i in range(16)}
   
    # Load instructions from files
    riscv.instruction_array = load_instructions_from_file("riscv_instructions.txt", base=0)
    
    # No longer loading bitty instructions from file as we'll generate them on the fly
   
    # Instruction counters
    bitty_instr_count = 0
    riscv_instr_count = 0
   
    # Maximum number of instructions to run (to prevent infinite loops)
    max_riscv_instructions = 100
   
    write_to_file("=== Starting Emulator Comparison ===")
   
    # Iterate through each instruction in RISCV array, and pass to `bitty_to_binary`
    while riscv_instr_count < max_riscv_instructions and riscv.pc < len(riscv.instruction_array):
        write_to_file(f"\n=== RISC-V Instruction {riscv_instr_count} at PC {riscv.pc} ===")
       
        # Fetch and execute one RISC-V instruction
        instruction = riscv.fetch_instruction()
        write_to_file(f"Instruction: 0x{instruction:08X}")
        next_pc = riscv.decode_and_execute(instruction)
       
        # Update RISC-V PC and instruction counter
        riscv.pc = next_pc
        riscv_instr_count += 1
       
        # Process the instruction in bitty_to_binary and iterate over returned instructions
        bitty_binary_instructions = translator.bitty_to_binary(instruction)
       
        write_to_file(f"\n=== Executing {len(bitty_binary_instructions)} Bitty Instructions ===")
        
        # Keep track of total Bitty instructions executed
        instructions_executed = 0
        
        for i, instr_bin in enumerate(bitty_binary_instructions):
            write_to_file(f"Executing Bitty Instruction {i}: 0x{instr_bin:04X}")
            
            # Directly pass the instruction to evaluate() rather than an address
            relative_offset = bitty.evaluate(instr_bin)
            
            # Increment the instruction count
            instructions_executed += 1
            
            # If the relative_offset is not 1, we have a branch
            if relative_offset != 1:
                write_to_file(f"Branch taken with offset {relative_offset}")
        
        # Update total Bitty instruction count
        bitty_instr_count += instructions_executed
       
        # Compare register values between emulators
        write_to_file("\n=== Register Comparison ===")
        write_to_file(f"{'Register':<10} {'RISC-V':<10} {'Bitty':<10} {'Match':<6}")
        write_to_file("-" * 40)
       
        for rv_reg, bitty_reg in register_map.items():
            rv_value = riscv.registers[rv_reg]
            bitty_value = bitty.registers[bitty_reg]
           
            # Compare lower 16 bits for RISCV register (if applicable)
            match = (rv_value & 0xFFFF) == bitty_value
            match_str = "✓" if match else "✗"
           
            write_to_file(f"x{rv_reg:<9} 0x{rv_value:08X} 0x{bitty_value:04X}   {match_str}")
   
    write_to_file("\n=== Comparison Complete ===")
    write_to_file(f"Executed {riscv_instr_count} RISC-V instructions and {bitty_instr_count} Bitty instructions")

if __name__ == "__main__":
    main()
