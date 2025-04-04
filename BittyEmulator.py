# BittyEmulator.py

class BittyEmulator:
    def __init__(self):
        self.d_out = 0
        self.registers = [10] * 16
        
        # No longer storing instructions in an array
        # No shared memory initialization
        print("BittyEmulator initialized with default register values")

    def evaluate(self, instruction):
        """
        Evaluates a single instruction and updates emulator state
        Returns the next instruction address relative to current (usually +1)
        """
        # Format code remains the same (bits [1:0])
        format_code = instruction & 0x0003
        
        # Rewrite: rx now occupies bits [15:12]
        rx = (instruction >> 12) & 0xF
        
        # We'll define ry and in_b, but only set ry in Normal or Load/Store format
        ry, in_b = None, None

        if format_code == 0:  # Normal (R-type) format
            # Rewrite: ry now occupies bits [11:8]
            ry = (instruction >> 8) & 0xF
            in_b = self.registers[ry]
            print(f"Normal format - rx: {rx}, ry: {ry}, in_b: {in_b}")
        elif format_code == 1:  # Immediate format
            in_b = (instruction & 0x1FE0) >> 5
            print(f"Immediate format - rx: {rx}, immediate value: {in_b}")
        elif format_code == 2:  # Branch format
            branch_cond = (instruction & 0x000C) >> 2
            branch_immediate = (instruction & 0x0FF0) >> 4
            print(f"Branch format - condition: {branch_cond}, immediate: {branch_immediate}")
            
            compare_value = self.d_out
            print(f"Branch checking d_out value: {compare_value}")
            
            # Branch logic unchanged, but return value is relative offset
            if branch_cond == 0 and compare_value == 0:
                return branch_immediate  # Return relative jump amount
            elif branch_cond == 1 and compare_value == 1:
                return branch_immediate  # Return relative jump amount
            elif branch_cond == 2 and compare_value == 2:
                return branch_immediate  # Return relative jump amount
            else:
                return 1  # No branch taken, move to next instruction
        elif format_code == 3:  # Load/Store format
            # Since we're removing memory_array, this section needs to be modified
            # Just print what would have happened for demonstration purposes
            ry = (instruction >> 8) & 0xF
            ls_code = instruction & 0x0004
            
            if ls_code == 0:  # Load
                print(f"Load operation - would load from address in register {ry} to register {rx}")
                # Since there's no memory, we'll just set rx to a dummy value
                self.set_register_value(rx, 0xCAFE)  # Placeholder value
            else:  # Store
                print(f"Store operation - would store value from register {rx} to address in register {ry}")
            
            return 1  # Move to next instruction

        # Rewrite: alu_sel occupies bits [5:2] (4 bits)
        alu_sel = (instruction >> 2) & 0xF
        
        # ALU operations remain the same
        if format_code == 0 or format_code == 1:
            result = 0
            if alu_sel == 0x0:  # Addition
                result = (self.registers[rx] + in_b) & 0xFFFF
                print(f"Addition: {self.registers[rx]} + {in_b} = {result}")
            elif alu_sel == 0x1:  # Subtraction
                result = (self.registers[rx] - in_b) & 0xFFFF
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
                result = (self.registers[rx] << (in_b % 16)) & 0xFFFF
                print(f"Shift left: {self.registers[rx]} << {in_b} = {result}")
            elif alu_sel == 0x6:  # Shift right
                result = (self.registers[rx] >> (in_b % 16)) & 0xFFFF
                print(f"Shift right: {self.registers[rx]} >> {in_b} = {result}")
            elif alu_sel == 0x7:  # Compare
                if self.registers[rx] == in_b:
                    result = 0
                    print(f"Compare: {self.registers[rx]} == {in_b} -> Equal (0)")
                elif self.registers[rx] > in_b:
                    result = 1
                    print(f"Compare: {self.registers[rx]} > {in_b} -> Greater (1)")
                else:
                    result = 2
                    print(f"Compare: {self.registers[rx]} < {in_b} -> Less (2)")
            
            print(f"Emulator result: {result}")
            self.registers[rx] = result
            self.d_out = result

        return 1  # Default is to move to next instruction

    def get_register_value(self, reg_num):
        return self.registers[reg_num]

    def set_register_value(self, reg_num, value):
        self.registers[reg_num] = value & 0xFFFF  # Ensure value is treated as 16-bit unsigned
        print(f"Register {reg_num} set to {self.registers[reg_num]:04X}")