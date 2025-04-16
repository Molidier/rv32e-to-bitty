class BittyEmulator:
    def __init__(self, memory):
        # Initialize 16 registers with dummy 32-bit values.
        self.memory = memory
        self.d_out = 0
        self.registers = [i * 10 for i in range(16)]
        self.registers[0] = 0  # Register 0 is always 0.
        self.pc = 0  # Program counter.
        print("BittyEmulator initialized with default 32-bit register values")
    
    def evaluate_instructions_array(self, instructions):
        self.pc = 0
        while self.pc < len(instructions):
            instruction = instructions[self.pc]
            print(f"Evaluating instruction: {instruction:04X}")
            next_pc = self.evaluate(instruction)
            print(f"Next PC: {next_pc:04X}")
            self.pc = next_pc
        return self.pc

    def evaluate(self, instruction):
        # Get the current PC value (for relative branches).
        current_pc = self.pc
        format_code = instruction & 0x0003
        rx = (instruction >> 12) & 0xF
        ry, in_b = None, None

        if format_code == 0:  # Normal format (R-type)
            ry = (instruction >> 8) & 0xF
            in_b = self.registers[ry]
            print(f"Normal format - rx: {rx}, ry: {ry}, in_b: {in_b}")
        elif format_code == 1:  # Immediate format
            # Extract the 6-bit immediate from bits [11:6]
            in_b = (instruction & 0x0FC0) >> 6

            # Sign-extend the 6-bit immediate to 32 bits.
            # Check if the sign bit (bit 5) is set.
            if in_b & (1 << 5):  # if bit 5 is 1
                in_b = in_b - (1 << 6)

            print(f"Immediate format - rx: {rx}, immediate value (sign-extended): {in_b}")

        elif format_code == 2:  # Branch format
            branch_cond = (instruction & 0x000C) >> 2
            branch_immediate = ((instruction & 0x0FF0) >> 4) // 2
            print(f"Branch format - condition: {branch_cond}, immediate: {branch_immediate}")
            
            compare_value = self.d_out
            print(f"Branch checking d_out value: {compare_value}")
            
            # Branch logic uses current PC for relative jumps.
            if branch_cond == 0 and compare_value == 0:
                return current_pc + branch_immediate
            elif branch_cond == 1 and compare_value == 1:
                return current_pc + branch_immediate
            elif branch_cond == 2 and compare_value == 2:
                return current_pc + branch_immediate
            else:
                #BittyEmulator.set_register_value(self, rx, STATIC_PC_VALUE)
                return current_pc + 1
        elif format_code == 3:  # Load/Store format
            ry_bin = (instruction >> 8) & 0xF
            ls_code = instruction & 0x0004
            ry = self.registers[ry_bin]

            
            # Make sure address is within memory bounds
            if ry >= len(self.memory):
                print(f"Memory access out of bounds: {ry}")
                print(f"New address is: ", ry % len(self.memory))
                ry = ry % len(self.memory)
            #---------------------------------
            #To CHeck LH instruction
            #CHANGED ONLY FOR SIMULATION PURPOSES

            #---------------------------------
            if ry % 2 != 0:
                print(f"Misaligned memory access for LH: {ry}")
                ry = ry - 1
            
            if ls_code == 0:  # Load
                print(f"Value form the ")
                print(f"Load operation - would load from address in register {ry_bin} the value {self.memory[ry]:08x} to register {rx}")
                self.set_register_value(rx, self.memory[ry])  # Placeholder value.
            else:  # Store
                print(f"Store operation - would store value {self.registers[rx]:08x} from register {rx} to address in register {ry_bin}")
                self.memory[ry] = self.get_register_value(rx)  # Placeholder value.
            return current_pc + 1  # Next instruction.

        # ALU Operations (for normal and immediate formats).
        alu_sel = (instruction >> 2) & 0xF
        if format_code == 0 or format_code == 1:
            result = 0
            if alu_sel == 0x0:  # Addition
                result = (self.registers[rx] + in_b) & 0xFFFFFFFF
                print(f"Addition: {self.registers[rx]} + {in_b} = {result}")
            elif alu_sel == 0x1:  # Subtraction
                result = (self.registers[rx] - in_b) & 0xFFFFFFFF
                print(f"Subtraction: {self.registers[rx]} - {in_b} = {result}")
            elif alu_sel == 0x2:  # Bitwise AND
                result = self.registers[rx] & in_b
                print(f"Bitwise AND: {self.registers[rx]} & {in_b} = {result}")
            elif alu_sel == 0x3:  # Bitwise OR
                result = self.registers[rx] | in_b
                print(f"Bitwise OR: {self.registers[rx]} | {in_b} = {result}")
            elif alu_sel == 0x4:  # Bitwise XOR
                result = self.registers[rx] ^ in_b
                print(f"Bitwise XOR: {self.registers[rx]} ^ {in_b} = {result}")
            elif alu_sel == 0x5:  # Shift left
                result = (self.registers[rx] << (in_b % 32)) & 0xFFFFFFFF
                print(f"Shift left: {self.registers[rx]} << {in_b} = {result}")
            elif alu_sel == 0x6:  # Shift right (logical)
                result = (self.registers[rx] >> (in_b % 32)) & 0xFFFFFFFF
                print(f"Shift right: {self.registers[rx]} >> {in_b} = {result}")
            elif alu_sel == 0x7:  # Unsigned Compare
                if self.registers[rx] == in_b:
                    result = 0
                    print(f"Compare: {self.registers[rx]} == {in_b} -> Equal (0)")
                elif self.registers[rx] > in_b:
                    result = 1
                    print(f"Compare: {self.registers[rx]} > {in_b} -> Greater (1)")
                else:
                    result = 2
                    print(f"Compare: {self.registers[rx]} < {in_b} -> Less (2)")
            elif alu_sel == 0x8:  # Signed Shift right (Arithmetic Shift)
                # Convert to 32-bit signed integer.
                signed_rx = self.registers[rx] if self.registers[rx] < 0x80000000 else self.registers[rx] - 0x100000000
                result = signed_rx >> (in_b % 32)
                # Mask result to 32 bits.
                result = result & 0xFFFFFFFF
                print(f"Signed Shift right: {signed_rx} >> {in_b} = {result}")
            elif alu_sel == 0x9:  # Signed Compare
                signed_rx = self.registers[rx] if self.registers[rx] < 0x80000000 else self.registers[rx] - 0x100000000
                signed_in_b = in_b if in_b < 0x80000000 else in_b - 0x100000000
                if signed_rx == signed_in_b:
                    result = 0
                    print(f"Compare: {signed_rx} == {signed_in_b} -> Equal (0)")
                elif signed_rx > signed_in_b:
                    result = 1
                    print(f"Compare: {signed_rx} > {signed_in_b} -> Greater (1)")
                else:
                    result = 2
                    print(f"Compare: {signed_rx} < {signed_in_b} -> Less (2)")
            else:
                print(f"Unknown ALU operation: {alu_sel}")
                result = 0

            # Update register rx with the result (except for compare operations if needed).
            if alu_sel not in (0x7, 0x9):  # For compare, you might not want to update rx.
                self.set_register_value(rx, result)
                print(f"Register {rx} updated with result: {result:08X}")
            self.d_out = result

        return current_pc + 1  # Return next instruction address.

    def get_register_value(self, reg_num):
        return self.registers[reg_num]

    def set_register_value(self, reg_num, value):
        self.registers[reg_num] = value & 0xFFFFFFFF  # Ensure value is 32-bit.
        print(f"Register {reg_num} set to {self.registers[reg_num]:08X}")
