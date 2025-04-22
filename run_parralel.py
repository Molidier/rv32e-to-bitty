# EmulatorComparison.py
from BittyEmulator import BittyEmulator
from RISCV32EMEmulator import RISCV32EMEmulator
from translator import RiscVConverter
from shared_memory import generate_shared_memory  # Import shared memory generator


def load_instructions_from_file(filename, base=0):
    """
    Reads instructions from a text file, one per line.
    If base is 0, int() will auto-detect the base from the prefix.
    """
    instructions = []
    try:
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
    except FileNotFoundError:
        print(f"Warning: File {filename} not found. Using sample instructions.")
        # Add some sample instructions if file not found
        if "riscv" in filename.lower():
            # Sample RISC-V instructions: add x1, x2, x3
            instructions = [0x003100B3]  # ADD x1, x2, x3
    return instructions

def write_to_file(message, filename="comparison_output.txt"):
    """
    Write a message to the output file.
    """
    with open(filename, "a") as file:
        file.write(message + "\n")

def main():
    # Clear the output file before starting
    with open("comparison_output.txt", "w") as file:
        file.write("=== Starting Emulator Comparison ===\n")
    
    # Generate shared memory for both emulators
    memory = generate_shared_memory()

    # Initialize both emulators
    bitty = BittyEmulator(memory = memory)
    riscv = RISCV32EMEmulator(memory_array=memory)
    translator = RiscVConverter()
   
    # Define mapping from RISC-V registers to Bitty registers (here 1:1 mapping)
    register_map = {i: i for i in range(16)}
   
    # Load instructions from files
    try:
        riscv.instruction_array = load_instructions_from_file("riscv_instructions.txt", base=0)
    except Exception as e:
        print(f"Error loading instructions: {e}")
        write_to_file(f"Error loading instructions: {e}")
        return
   
    # Instruction counters
    bitty_instr_count = 0
    riscv_instr_count = 0
   
    # Maximum number of instructions to run (to prevent infinite loops)
    max_riscv_instructions = 100
   
    write_to_file("=== Starting Emulator Comparison ===")
   
    # Iterate through each instruction in the RISCV array, and pass to `bitty_to_binary`
    while riscv_instr_count < max_riscv_instructions and riscv.pc < len(riscv.instruction_array):
        write_to_file(f"\n=== RISC-V Instruction {riscv_instr_count} at PC {riscv.pc} ===")
       
        # Fetch and execute one RISC-V instruction
        instruction = riscv.fetch_instruction()
        write_to_file(f"Instruction: 0x{instruction:08X}")
        next_pc = riscv.decode_and_execute(instruction)
        

        # Update RISC-V PC and instruction counter
        riscv.pc = next_pc
        riscv_instr_count += 1
       
        # Process the instruction in bitty_to_binary and get equivalent Bitty instructions
        try:
            bitty_binary_instructions = translator.bitty_to_binary(instruction)
        except Exception as e:
            write_to_file(f"Error in translation: {e}")
            bitty_binary_instructions = []
       
        write_to_file(f"\n=== Executing {len(bitty_binary_instructions)} Bitty Instructions ===")
        
        # Log each Bitty instruction before execution
        for i, instr_bin in enumerate(bitty_binary_instructions):
            write_to_file(f"Bitty Instruction {i}: 0x{instr_bin:04X}")
            
        # Use evaluate_instructions_array to execute all instructions at once
        if bitty_binary_instructions:
            # Save the current PC to restore later if needed
            start_pc = bitty.pc
            
            # Execute all instructions in the array
            bitty.pc = 0  # Reset PC to 0 for this instruction batch
            end_pc = bitty.evaluate_instructions_array(bitty_binary_instructions)
            
            if end_pc != len(bitty_binary_instructions):
                write_to_file(f"Branch taken, ended at PC {end_pc}")
                
            bitty_instr_count += len(bitty_binary_instructions)
       
        # Compare register values between emulators (now considering 32-bit values)
        write_to_file("\n=== Register Comparison ===")
        write_to_file(f"{'Register':<10} {'RISC-V':<10} {'Bitty':<10} {'Match':<6}")
        write_to_file("-" * 40)
       
        for rv_reg, bitty_reg in register_map.items():
            rv_value = riscv.registers[rv_reg]
            bitty_value = bitty.registers[bitty_reg]
           
            # Compare the full 32-bit values
            match = (rv_value & 0xFFFFFFFF) == (bitty_value & 0xFFFFFFFF)
            match_str = "✓" if match else "✗"
           
            write_to_file(f"x{rv_reg:<9} 0x{rv_value:08X} 0x{bitty_value:08X}   {match_str}")
          # Increment the STATIC_PC_VALUE in BittyEmulator when RISC-V PC advances
        BittyEmulator.STATIC_PC_VALUE += 1
        write_to_file(f"STATIC_PC_VALUE incremented to: {BittyEmulator.STATIC_PC_VALUE}")
    
    write_to_file("\n=== Comparison Complete ===")
    write_to_file(f"Executed {riscv_instr_count} RISC-V instructions and {bitty_instr_count} Bitty instructions")
  
       
    write_to_file(f"Final STATIC_PC_VALUE: {BittyEmulator.STATIC_PC_VALUE}")
    RiscVConverter.print_map()

if __name__ == "__main__":
    main()