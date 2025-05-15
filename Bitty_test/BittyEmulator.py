class BittyEmulator:
    # Static class variable to track overall instruction count
    STATIC_PC_VALUE = 0 # This seems unused within this class, consider if needed

    def __init__(self, data_memory_size=1024, memory=None): # Added data_memory_size
        # self.memory is now for DATA only
        if memory is not None:
            self.data_memory = memory
        else:
            self.data_memory = [0] * data_memory_size # Initialize data memory with zeros

        self.instruction_array = [] # For Bitty's program instructions

        self.d_out = 0
        #self.registers = [0] * 16 # Initialize all to 0 initially
        self.registers = [i * 10 for i in range(16)] # Original initialization
        # self.registers[0] = 0  # Register 0 is always 0 - ensured by [0]*16 and set_register_value
        self.pc = 0  # Program counter (index into instruction_array)
        print(f"BittyEmulator initialized. Data memory size: {len(self.data_memory)}")

    def load_instructions_from_file(self, file_path): # Renamed for clarity in original, kept here
        """
        Load Bitty instructions from a file into self.instruction_array.
        The file can contain instructions in binary (0b...), hex (0x...), or decimal,
        one per line. Lines starting with '#' are comments. Underscores are ignored.
        """
        loaded_instructions = []
        try:
            with open(file_path, 'r') as f:
                for line_number, line_content in enumerate(f, 1): # Added line_number for better error messages
                    s = line_content.strip()
                    if not s or s.startswith("#"):  # Skip empty lines and comments
                        continue
                    
                    # remove the visual underscores
                    s_cleaned = s.replace("_", "")
                    
                    # int(..., 0) will parse 0b... as binary, 0x... as hex, etc.
                    try:
                        instruction_value = int(s_cleaned, 0)
                    except ValueError as e:
                        print(f"Error parsing line {line_number} ('{s}'): {e}")
                        # Decide if one error should stop the whole process or just skip the line.
                        # For now, we'll skip this line and continue with others.
                        # If all instructions must be valid, you could 'return False' here.
                        continue 
                    
                    # Bitty instructions are 16-bit, so mask to keep lower 16 bits
                    loaded_instructions.append(instruction_value & 0xFFFF)
            
            self.instruction_array = loaded_instructions
            self.pc = 0 # Reset PC when new instructions are loaded
            print(f"Loaded {len(self.instruction_array)} Bitty instructions from {file_path}")
            return True
            
        except FileNotFoundError:
            print(f"Error: File not found at '{file_path}'")
            self.instruction_array = [] # Ensure it's cleared on error
            return False
        except Exception as e: # Catch other potential IOErrors or unexpected issues
            print(f"Error loading Bitty instruction file '{file_path}': {e}")
            self.instruction_array = [] # Ensure it's cleared on error
            return False

    def load_data_memory(self, data_list):
        """Allows pre-loading the data memory."""
        self.data_memory = list(data_list) # Make a copy
        print(f"Data memory pre-loaded with {len(self.data_memory)} values.")

    def run_program(self, max_instructions=10000): # Renamed for clarity
        """Evaluate the loaded program from self.instruction_array."""
        if not self.instruction_array:
            print("No Bitty program loaded in instruction_array")
            return

        self.pc = 0 # Ensure PC starts at 0 for a new run
        instruction_count = 0

        print("\nBittyEmulator Execution Trace:")
        while 0 <= self.pc < len(self.instruction_array) and instruction_count < max_instructions:
            instruction = self.instruction_array[self.pc]
            # print(f"Bitty PC={self.pc}: Evaluating instruction: 0x{instruction:04X}") # Verbose
            next_pc = self.evaluate(instruction)
            # print(f"Bitty Next PC: {next_pc}") # Verbose
            self.pc = next_pc
            instruction_count += 1

        if instruction_count >= max_instructions:
            print("BittyEmulator: Reached maximum instruction limit - possible infinite loop")
        elif self.pc >= len(self.instruction_array):
            print("BittyEmulator: Program completed - PC reached end of instruction_array")
        else: # pc < 0
            print(f"BittyEmulator: Program halted at PC={self.pc} (invalid PC)")

        # print(f"BittyEmulator executed {instruction_count} instructions.")
        return instruction_count # Return count for comparison script

    # Kept for potential direct use or backward compatibility if structure was different
    def evaluate_instructions_directly(self, instructions_list, max_instructions=1000):
        """Runs a given list of instructions directly."""
        self.instruction_array = list(instructions_list) # Use a copy
        return self.run_program(max_instructions)

    def evaluate(self, instruction):
        current_pc = self.pc # PC is an index into self.instruction_array
        format_code = instruction & 0x0003
        rx = (instruction >> 12) & 0xF
        ry_reg_idx, in_b = None, None # ry_reg_idx to avoid confusion with 'ry' (address)

        # Ensure rx is within RV32E bounds (0-15 for Bitty's 16 registers)
        if not (0 <= rx <= 15):
            print(f"Error: rx register index {rx} out of bounds (0-15). Instruction: 0x{instruction:04X}")
            return current_pc + 1 # Skip instruction

        if format_code == 0:  # Normal format (R-type)
            ry_reg_idx = (instruction >> 8) & 0xF
            if not (0 <= ry_reg_idx <= 15):
                print(f"Error: ry register index {ry_reg_idx} out of bounds (0-15). Instruction: 0x{instruction:04X}")
                return current_pc + 1 # Skip instruction
            in_b = self.registers[ry_reg_idx]
            # print(f"Normal format - rx: {rx}, ry_reg_idx: {ry_reg_idx}, in_b: {in_b}")
        elif format_code == 1:  # Immediate format
            in_b = (instruction & 0x0FC0) >> 6
            if in_b & (1 << 5):
                in_b = in_b - (1 << 6)
            # print(f"Immediate format - rx: {rx}, immediate (sign-extended): {in_b}")

        elif format_code == 2:  # Branch format
            branch_cond = (instruction >> 2) & 0x3
            if branch_cond < 3: # Conditional branches
                raw_imm = (instruction >> 4) & 0xFFF
                if raw_imm & 0x800:
                    raw_imm -= 0x1000
                offset_instr_indices = raw_imm >> 1 # Offset in terms of instruction indices

                # print(f"Branch format – cond: {branch_cond}, imm12: {raw_imm}, offset_indices: {offset_instr_indices}")
                # print(f"Branch checks d_out = {self.d_out}")

                branch_taken = False
                if branch_cond == 0 and self.d_out == 0: branch_taken = True
                elif branch_cond == 1 and self.d_out == 1: branch_taken = True # Assuming 1 means e.g. >0
                elif branch_cond == 2 and self.d_out == 2: branch_taken = True # Assuming 2 means e.g. <0

                return (current_pc + offset_instr_indices) if branch_taken else (current_pc + 1)
            else: # PC-get/set
                pc_g_or_s = (instruction >> 4) & 0x1
                if pc_g_or_s == 1: # Get PC (store PC+1 into rx)
                    # In RISC-V JAL, PC+4 is stored. Here, PC is an index, so PC+1.
                    self.set_register_value(rx, current_pc + 1)
                    return current_pc + 1 # Continue to next instruction
                else: # Set PC (jump to address in register rx)
                    # Value in register rx is an INSTRUCTION INDEX for Bitty
                    target_pc_index = self.get_register_value(rx)
                    return target_pc_index

        elif format_code == 3:  # Load/Store format
            ry_reg_idx = (instruction >> 8) & 0xF # Register holding the base address/index
            if not (0 <= ry_reg_idx <= 15):
                print(f"Error: L/S address register index {ry_reg_idx} out of bounds. Instruction: 0x{instruction:04X}")
                return current_pc + 1

            # 'address_index' is the INDEX into self.data_memory (data memory)
            # Bitty's instructions are 16-bit. If registers hold byte addresses,
            # and self.data_memory stores 16-bit words, an address from a register
            # needs to be treated as a byte address then converted to a word index.
            # Original code used `ry = self.registers[ry_bin]` directly as an index.
            # Let's assume registers hold WORD INDICES for self.data_memory for Bitty for now.
            address_index = self.registers[ry_reg_idx]

            # The original alignment check `if ry % 2 != 0` and `ry = ry - 1`
            # implied `ry` was a byte address for a 16-bit word memory.
            # If `address_index` is a WORD index, no alignment check on the index itself is needed.
            # However, RISC-V alignment refers to the BYTE address.
            # For simplicity here, we'll assume `address_index` is a valid word index.

            ls_code = (instruction & 0x0004) >> 2 # Shifted to get 0 for Load, 1 for Store

            if not (0 <= address_index < len(self.data_memory)):
                print(f"Data Memory access out of bounds: index {address_index}, memory size {len(self.data_memory)}. Instr: 0x{instruction:04X}")
                # Handle error: skip, trap, or wrap (wrapping not typical for general memory)
                # For now, let's make it a no-op and continue.
                return current_pc + 1

            if ls_code == 0:  # Load from self.data_memory (data memory)
                value_loaded = self.data_memory[address_index]
                self.set_register_value(rx, value_loaded)
                # print(f"Load: R{rx} <- M_data[{address_index}] (0x{value_loaded:04X})")
            else:  # Store to self.data_memory (data memory)
                value_to_store = self.get_register_value(rx)
                self.data_memory[address_index] = value_to_store & 0xFFFFFFFF # Bitty memory stores 32-bit words
                print(f"Store: M_data[{address_index}] <- R{rx} (0x{value_to_store:04X})")

            return current_pc + 1

        # ALU Operations
        alu_sel = (instruction >> 2) & 0xF
        if format_code == 0 or format_code == 1: # R-type or Immediate
            # Ensure in_b is defined (it would be if format_code was 0 or 1)
            if in_b is None: # Should not happen if logic above is correct
                print(f"Error: in_b not defined for ALU op. Instruction: 0x{instruction:04X}")
                return current_pc + 1

            result = 0
            # Register value for ALU ops
            val_rx = self.registers[rx]

            if alu_sel == 0x0:  result = (val_rx + in_b)
            elif alu_sel == 0x1:  result = (val_rx - in_b)
            elif alu_sel == 0x2:  result = val_rx & in_b
            elif alu_sel == 0x3:  result = val_rx | in_b
            elif alu_sel == 0x4:  result = val_rx ^ in_b
            elif alu_sel == 0x5:  result = (val_rx << (in_b & 0x1F)) # Shift amount masked to 5 bits for 32-bit reg
            elif alu_sel == 0x6:  result = (val_rx >> (in_b & 0x1F)) # Logical shift
            elif alu_sel == 0x7:  # Unsigned Compare (sets d_out)
                if val_rx == in_b: self.d_out = 0      # Equal
                elif val_rx > in_b: self.d_out = 1   # Greater
                else: self.d_out = 2                 # Less
                # print(f"UCompare: R{rx}({val_rx}) vs {in_b} -> d_out={self.d_out}")
                return current_pc + 1 # Compare doesn't write to rx
            elif alu_sel == 0x8:  # Signed Shift right (Arithmetic)
                # Treat val_rx as 32-bit signed for arithmetic shift
                signed_val_rx = val_rx if val_rx < 0x80000000 else val_rx - 0x100000000
                result = signed_val_rx >> (in_b & 0x1F)
            elif alu_sel == 0x9:  # Signed Compare (sets d_out)
                # Treat both as 32-bit signed for comparison
                s_val_rx = val_rx if val_rx < 0x80000000 else val_rx - 0x100000000
                # in_b for immediate is already sign-extended from 6-bit.
                # If in_b came from a register (format_code 0), it's a 32-bit value.
                s_in_b = in_b
                if format_code == 0: # in_b from register, interpret as signed 32-bit
                     s_in_b = in_b if in_b < 0x80000000 else in_b - 0x100000000
                # else: in_b from immediate is already correctly signed small number

                if s_val_rx == s_in_b: self.d_out = 0      # Equal
                elif s_val_rx > s_in_b: self.d_out = 1   # Greater
                else: self.d_out = 2                 # Less
                # print(f"SCompare: R{rx}({s_val_rx}) vs {s_in_b} -> d_out={self.d_out}")
                return current_pc + 1 # Compare doesn't write to rx
            else:
                print(f"Unknown ALU operation: {alu_sel}. Instruction: 0x{instruction:04X}")
                # Default to no-op or result 0.
                self.d_out = 0 # Or some error flag
                return current_pc + 1

            # Mask result to 32 bits for register storage
            final_result = result & 0xFFFFFFFF
            self.set_register_value(rx, final_result)
            self.d_out = final_result # Update d_out with the ALU result for non-compare ops
            # print(f"ALU op {alu_sel}: R{rx} <- 0x{final_result:08X}, d_out set.")
            return current_pc + 1

        # Fallthrough if no other format matched (should not happen with masked format_code)
        print(f"Warning: Instruction 0x{instruction:04X} did not match any format logic.")
        return current_pc + 1

    def get_register_value(self, reg_num):
        if not (0 <= reg_num <= 15):
            print(f"Error: Attempt to get invalid register r{reg_num}")
            return 0 # Or raise error
        return self.registers[reg_num]

    def set_register_value(self, reg_num, value):
        if not (0 <= reg_num <= 15):
            print(f"Error: Attempt to set invalid register r{reg_num}")
            return
        self.registers[reg_num] = value & 0xFFFFFFFF
        # print(f"Register R{reg_num} set to 0x{self.registers[reg_num]:08X}")

    def print_registers(self):
        """Write the current state of all registers to bitty_registers_output.txt."""
        try:
            with open("bitty_registers_output.txt", "w") as f:
                f.write("BittyEmulator Register Values:\n")
                for i in range(16):
                    f.write(f"R{i:<2}: 0x{self.registers[i]:08X} ({self.registers[i]})\n")
                f.write(f"PC  : {self.pc}\n")
                f.write(f"D_OUT: 0x{self.d_out:08X} ({self.d_out})\n")
            # print("Bitty registers saved to bitty_registers_output.txt")
        except Exception as e:
            print(f"Error writing Bitty registers to file: {e}")

    # Property for backward compatibility
    @property
    def memory(self):
        return self.data_memory
    
    @memory.setter
    def memory(self, value):
        self.data_memory = value
    
# Example usage (if run directly)
if __name__ == "__main__":
    # Initialize BittyEmulator with a data memory size
    bitty_emu = BittyEmulator(data_memory_size=256)

    # Example: Pre-load some data into Bitty's data memory
    bitty_emu.load_data_memory([i for i in range(10, 20)]) # M[0]=10, M[1]=11...

    # Load Bitty program instructions from a file
    if bitty_emu.load_instructions_from_file("bitty_binary.txt"):
        # Execute the loaded program
        bitty_emu.run_program(max_instructions=50) # Limit execution steps

        # Print final register and D_OUT state
        bitty_emu.print_registers()

        # Optionally, print some data memory
        print("\nBitty Data Memory (first few words):")
        for i in range(min(10, len(bitty_emu.data_memory))):
            print(f"M_data[{i}]: 0x{bitty_emu.data_memory[i]:04X}")