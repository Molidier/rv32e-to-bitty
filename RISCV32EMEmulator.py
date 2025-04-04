# RISCV32EMEmulator.py
from shared_memory import generate_shared_memory  # Import shared memory generator

class RISCV32EMEmulator:
    def __init__(self):
        # RISC-V has 32 registers (x0-x31), but x0 is hardwired to 0
        # For RV32E (embedded), only 16 registers (x0-x15) are used
        self.registers = [10] * 16  # RV32E has 16 registers
        self.pc = 0  # Program counter
        self.instruction_array = []
        self.memory_array = generate_shared_memory()  # Shared memory instance
        
        # # Display initial memory state
        # for index, el in enumerate(self.memory_array):
        #     print(f"Emulator Memory {index}: {el:08X}")
        
        # Load instructions from file
        try:
            with open("instructions_for_em.txt", "r") as infile:
                for line in infile:
                    instr = int(line.strip(), 16)
                    print(f"Instruction read and stored: {instr:08x}")
                    self.instruction_array.append(instr)
        except FileNotFoundError:
            print("Error opening file")
            
    
    def fetch_instruction(self):
        """Fetch the instruction at the current PC"""
        if 0 <= self.pc < len(self.instruction_array):
            return self.instruction_array[self.pc]
        else:
            print(f"PC out of range: {self.pc}")
            return 0  # NOP instruction
    
    def decode_and_execute(self, instruction):
        """Decode and execute a RISC-V instruction"""
        # Extract the opcode (bits 0-6)
        opcode = instruction & 0x7F
        print(f"Instruction: {instruction:08X}")
        
        # R-type instruction format
        if opcode == 0b0110011:
            rd = (instruction >> 7) & 0x1F
            funct3 = (instruction >> 12) & 0x7
            rs1 = (instruction >> 15) & 0x1F
            rs2 = (instruction >> 20) & 0x1F
            funct7 = (instruction >> 25) & 0x7F
            
            # Ensure we only use registers 0-15 for RV32E
            if rd > 15 or rs1 > 15 or rs2 > 15:
                print(f"Error: Register number exceeds 15 in RV32E mode")
                return self.pc + 1
            
            # Register x0 is hardwired to 0
            if rd == 0:
                result = 0
            else:
                # Execute R-type instruction based on funct3 and funct7
                if funct3 == 0x0:
                    if funct7 == 0x00:  # ADD
                        result = (self.registers[rs1] + self.registers[rs2]) & 0xFFFFFFFF
                        print(f"ADD x{rd}, x{rs1}, x{rs2}: {self.registers[rs1]} + {self.registers[rs2]} = {result}")
                    elif funct7 == 0x20:  # SUB
                        result = (self.registers[rs1] - self.registers[rs2]) & 0xFFFFFFFF
                        print(f"SUB x{rd}, x{rs1}, x{rs2}: {self.registers[rs1]} - {self.registers[rs2]} = {result}")
                    else:
                        print(f"Unknown funct7 for R-type ADD/SUB: {funct7:02x}")
                        return self.pc + 1
                elif funct3 == 0x1:  # SLL - Shift Left Logical
                    shift_amount = self.registers[rs2] & 0x1F  # Only lower 5 bits used for 32-bit shifts
                    result = (self.registers[rs1] << shift_amount) & 0xFFFFFFFF
                    print(f"SLL x{rd}, x{rs1}, x{rs2}: {self.registers[rs1]} << {shift_amount} = {result}")
                elif funct3 == 0x2:  # SLT - Set Less Than
                    # Signed comparison
                    rs1_val = self.registers[rs1]
                    rs2_val = self.registers[rs2]
                    # Convert to signed 32-bit integers
                    if rs1_val & 0x80000000:
                        rs1_val = rs1_val - 0x100000000
                    if rs2_val & 0x80000000:
                        rs2_val = rs2_val - 0x100000000
                    result = 1 if rs1_val < rs2_val else 0
                    print(f"SLT x{rd}, x{rs1}, x{rs2}: {rs1_val} < {rs2_val} = {result}")
                elif funct3 == 0x3:  # SLTU - Set Less Than Unsigned
                    result = 1 if (self.registers[rs1] & 0xFFFFFFFF) < (self.registers[rs2] & 0xFFFFFFFF) else 0
                    print(f"SLTU x{rd}, x{rs1}, x{rs2}: {self.registers[rs1]} < {self.registers[rs2]} = {result}")
                elif funct3 == 0x4:  # XOR
                    result = self.registers[rs1] ^ self.registers[rs2]
                    print(f"XOR x{rd}, x{rs1}, x{rs2}: {self.registers[rs1]} ^ {self.registers[rs2]} = {result}")
                elif funct3 == 0x5:
                    if funct7 == 0x00:  # SRL - Shift Right Logical
                        shift_amount = self.registers[rs2] & 0x1F
                        result = (self.registers[rs1] >> shift_amount) & 0xFFFFFFFF
                        print(f"SRL x{rd}, x{rs1}, x{rs2}: {self.registers[rs1]} >> {shift_amount} = {result}")
                    elif funct7 == 0x20:  # SRA - Shift Right Arithmetic
                        shift_amount = self.registers[rs2] & 0x1F
                        # Preserve sign bit
                        if self.registers[rs1] & 0x80000000:
                            mask = ((1 << shift_amount) - 1) << (32 - shift_amount)
                            result = ((self.registers[rs1] >> shift_amount) | mask) & 0xFFFFFFFF
                        else:
                            result = (self.registers[rs1] >> shift_amount) & 0xFFFFFFFF
                        print(f"SRA x{rd}, x{rs1}, x{rs2}: {self.registers[rs1]} >> {shift_amount} (arithmetic) = {result}")
                    else:
                        print(f"Unknown funct7 for R-type SRL/SRA: {funct7:02x}")
                        return self.pc + 1
                elif funct3 == 0x6:  # OR
                    result = self.registers[rs1] | self.registers[rs2]
                    print(f"OR x{rd}, x{rs1}, x{rs2}: {self.registers[rs1]} | {self.registers[rs2]} = {result}")
                elif funct3 == 0x7:  # AND
                    result = self.registers[rs1] & self.registers[rs2]
                    print(f"AND x{rd}, x{rs1}, x{rs2}: {self.registers[rs1]} & {self.registers[rs2]} = {result}")
                else:
                    print(f"Unknown funct3 for R-type: {funct3}")
                    return self.pc + 1
                
                # Store result in destination register (except x0)
                if rd != 0:
                    self.registers[rd] = result
            
            return self.pc + 1
        
        # I-type instruction format (immediate arithmetic and loads)
        elif opcode == 0b0010011 or opcode == 0b0000011:
            rd = (instruction >> 7) & 0x1F
            funct3 = (instruction >> 12) & 0x7
            rs1 = (instruction >> 15) & 0x1F
            imm = (instruction >> 20) & 0xFFF
            
            # Sign extend the 12-bit immediate
            if imm & 0x800:
                imm |= 0xFFFFF000
            
            # Ensure we only use registers 0-15 for RV32E
            if rd > 15 or rs1 > 15:
                print(f"Error: Register number exceeds 15 in RV32E mode")
                return self.pc + 1
            
            # I-type arithmetic operations
            if opcode == 0b0010011:
                # Register x0 is hardwired to 0
                if rd == 0:
                    return self.pc + 1
                
                if funct3 == 0x0:  # ADDI
                    result = (self.registers[rs1] + imm) & 0xFFFFFFFF
                    print(f"ADDI x{rd}, x{rs1}, {imm}: {self.registers[rs1]} + {imm} = {result}")
                elif funct3 == 0x1:  # SLLI - Shift Left Logical Immediate
                    shift_amount = imm & 0x1F
                    result = (self.registers[rs1] << shift_amount) & 0xFFFFFFFF
                    print(f"SLLI x{rd}, x{rs1}, {shift_amount}: {self.registers[rs1]} << {shift_amount} = {result}")
                elif funct3 == 0x2:  # SLTI - Set Less Than Immediate
                    # Signed comparison
                    rs1_val = self.registers[rs1]
                    if rs1_val & 0x80000000:
                        rs1_val = rs1_val - 0x100000000
                    if imm & 0x80000000:
                        imm = imm - 0x100000000
                    result = 1 if rs1_val < imm else 0
                    print(f"SLTI x{rd}, x{rs1}, {imm}: {rs1_val} < {imm} = {result}")
                elif funct3 == 0x3:  # SLTIU - Set Less Than Immediate Unsigned
                    result = 1 if (self.registers[rs1] & 0xFFFFFFFF) < (imm & 0xFFFFFFFF) else 0
                    print(f"SLTIU x{rd}, x{rs1}, {imm}: {self.registers[rs1]} < {imm} = {result}")
                elif funct3 == 0x4:  # XORI
                    result = self.registers[rs1] ^ imm
                    print(f"XORI x{rd}, x{rs1}, {imm}: {self.registers[rs1]} ^ {imm} = {result}")
                elif funct3 == 0x5:
                    # Check upper bits of immediate for shift type
                    shift_type = (imm >> 5) & 0x7F
                    shift_amount = imm & 0x1F
                    
                    if shift_type == 0x00:  # SRLI - Shift Right Logical Immediate
                        result = (self.registers[rs1] >> shift_amount) & 0xFFFFFFFF
                        print(f"SRLI x{rd}, x{rs1}, {shift_amount}: {self.registers[rs1]} >> {shift_amount} = {result}")
                    elif shift_type == 0x20:  # SRAI - Shift Right Arithmetic Immediate
                        # Preserve sign bit
                        if self.registers[rs1] & 0x80000000:
                            mask = ((1 << shift_amount) - 1) << (32 - shift_amount)
                            result = ((self.registers[rs1] >> shift_amount) | mask) & 0xFFFFFFFF
                        else:
                            result = (self.registers[rs1] >> shift_amount) & 0xFFFFFFFF
                        print(f"SRAI x{rd}, x{rs1}, {shift_amount}: {self.registers[rs1]} >> {shift_amount} (arithmetic) = {result}")
                    else:
                        print(f"Unknown shift type for I-type SRLI/SRAI: {shift_type:02x}")
                        return self.pc + 1
                elif funct3 == 0x6:  # ORI
                    result = self.registers[rs1] | imm
                    print(f"ORI x{rd}, x{rs1}, {imm}: {self.registers[rs1]} | {imm} = {result}")
                elif funct3 == 0x7:  # ANDI
                    result = self.registers[rs1] & imm
                    print(f"ANDI x{rd}, x{rs1}, {imm}: {self.registers[rs1]} & {imm} = {result}")
                else:
                    print(f"Unknown funct3 for I-type arithmetic: {funct3}")
                    return self.pc + 1
                
                # Store result in destination register (except x0)
                if rd != 0:
                    self.registers[rd] = result
            
            # Load instructions
            elif opcode == 0b0000011:
                # Calculate memory address
                address = (self.registers[rs1] + imm) & 0xFFFFFFFF
                
                # Make sure address is within memory bounds
                if address >= len(self.memory_array):
                    print(f"Memory access out of bounds: {address}")
                    return self.pc + 1
                
                # Register x0 is hardwired to 0
                if rd == 0:
                    return self.pc + 1
                
                if funct3 == 0x0:  # LB - Load Byte
                    value = self.memory_array[address] & 0xFF
                    # Sign extend
                    if value & 0x80:
                        value |= 0xFFFFFF00
                    self.registers[rd] = value
                    print(f"LB x{rd}, {imm}(x{rs1}): Loaded {value:08X} from address {address:08X}")
                elif funct3 == 0x1:  # LH - Load Halfword
                    # Ensure address is halfword-aligned
                    if address % 2 != 0:
                        print(f"Misaligned memory access for LH: {address}")
                        return self.pc + 1
                    
                    value = self.memory_array[address] & 0xFFFF
                    # Sign extend
                    if value & 0x8000:
                        value |= 0xFFFF0000
                    self.registers[rd] = value
                    print(f"LH x{rd}, {imm}(x{rs1}): Loaded {value:08X} from address {address:08X}")
                elif funct3 == 0x2:  # LW - Load Word
                    # Ensure address is word-aligned
                    if address % 4 != 0:
                        print(f"Misaligned memory access for LW: {address}")
                        return self.pc + 1
                    
                    value = self.memory_array[address]
                    self.registers[rd] = value
                    print(f"LW x{rd}, {imm}(x{rs1}): Loaded {value:08X} from address {address:08X}")
                elif funct3 == 0x4:  # LBU - Load Byte Unsigned
                    value = self.memory_array[address] & 0xFF
                    self.registers[rd] = value
                    print(f"LBU x{rd}, {imm}(x{rs1}): Loaded {value:08X} from address {address:08X}")
                elif funct3 == 0x5:  # LHU - Load Halfword Unsigned
                    # Ensure address is halfword-aligned
                    if address % 2 != 0:
                        print(f"Misaligned memory access for LHU: {address}")
                        return self.pc + 1
                    
                    value = self.memory_array[address] & 0xFFFF
                    self.registers[rd] = value
                    print(f"LHU x{rd}, {imm}(x{rs1}): Loaded {value:08X} from address {address:08X}")
                else:
                    print(f"Unknown funct3 for load: {funct3}")
                    return self.pc + 1
            
            return self.pc + 1
        
        # S-type instruction format (stores)
        elif opcode == 0b0100011:
            funct3 = (instruction >> 12) & 0x7
            rs1 = (instruction >> 15) & 0x1F
            rs2 = (instruction >> 20) & 0x1F
            imm_4_0 = (instruction >> 7) & 0x1F
            imm_11_5 = (instruction >> 25) & 0x7F
            imm = (imm_11_5 << 5) | imm_4_0
            
            # Sign extend the 12-bit immediate
            if imm & 0x800:
                imm |= 0xFFFFF000
            
            # Ensure we only use registers 0-15 for RV32E
            if rs1 > 15 or rs2 > 15:
                print(f"Error: Register number exceeds 15 in RV32E mode")
                return self.pc + 1
            
            # Calculate memory address
            address = (self.registers[rs1] + imm) & 0xFFFFFFFF
            
            # Make sure address is within memory bounds
            if address >= len(self.memory_array):
                print(f"Memory access out of bounds: {address}")
                return self.pc + 1
            
            if funct3 == 0x0:  # SB - Store Byte
                value = self.registers[rs2] & 0xFF
                # Mask the byte in memory and add the new value
                self.memory_array[address] = (self.memory_array[address] & 0xFFFFFF00) | value
                print(f"SB x{rs2}, {imm}(x{rs1}): Stored {value:02X} to address {address:08X}")
            elif funct3 == 0x1:  # SH - Store Halfword
                # Ensure address is halfword-aligned
                if address % 2 != 0:
                    print(f"Misaligned memory access for SH: {address}")
                    return self.pc + 1
                
                value = self.registers[rs2] & 0xFFFF
                # Mask the halfword in memory and add the new value
                self.memory_array[address] = (self.memory_array[address] & 0xFFFF0000) | value
                print(f"SH x{rs2}, {imm}(x{rs1}): Stored {value:04X} to address {address:08X}")
            elif funct3 == 0x2:  # SW - Store Word
                # Ensure address is word-aligned
                if address % 4 != 0:
                    print(f"Misaligned memory access for SW: {address}")
                    return self.pc + 1
                
                value = self.registers[rs2]
                self.memory_array[address] = value
                print(f"SW x{rs2}, {imm}(x{rs1}): Stored {value:08X} to address {address:08X}")
            else:
                print(f"Unknown funct3 for store: {funct3}")
                return self.pc + 1
            
            return self.pc + 1
        
        # B-type instruction format (branches)
        elif opcode == 0b1100011:
            funct3 = (instruction >> 12) & 0x7
            rs1 = (instruction >> 15) & 0x1F
            rs2 = (instruction >> 20) & 0x1F
            
            # Extract and compose branch immediate
            imm_11 = (instruction >> 7) & 0x1
            imm_4_1 = (instruction >> 8) & 0xF
            imm_10_5 = (instruction >> 25) & 0x3F
            imm_12 = (instruction >> 31) & 0x1
            
            imm = (imm_4_1 << 1) | (imm_10_5 << 5) | (imm_11 << 11) | (imm_12 << 12)
            
            # Sign extend the 13-bit immediate
            if imm & 0x1000:
                imm |= 0xFFFFE000
            
            # Ensure we only use registers 0-15 for RV32E
            if rs1 > 15 or rs2 > 15:
                print(f"Error: Register number exceeds 15 in RV32E mode")
                return self.pc + 1
            
            take_branch = False
            
            if funct3 == 0x0:  # BEQ - Branch if Equal
                take_branch = self.registers[rs1] == self.registers[rs2]
                print(f"BEQ x{rs1}, x{rs2}, {imm}: {self.registers[rs1]} == {self.registers[rs2]} = {take_branch}")
            elif funct3 == 0x1:  # BNE - Branch if Not Equal
                take_branch = self.registers[rs1] != self.registers[rs2]
                print(f"BNE x{rs1}, x{rs2}, {imm}: {self.registers[rs1]} != {self.registers[rs2]} = {take_branch}")
            elif funct3 == 0x4:  # BLT - Branch if Less Than
                # Signed comparison
                rs1_val = self.registers[rs1]
                rs2_val = self.registers[rs2]
                if rs1_val & 0x80000000:
                    rs1_val = rs1_val - 0x100000000
                if rs2_val & 0x80000000:
                    rs2_val = rs2_val - 0x100000000
                take_branch = rs1_val < rs2_val
                print(f"BLT x{rs1}, x{rs2}, {imm}: {rs1_val} < {rs2_val} = {take_branch}")
            elif funct3 == 0x5:  # BGE - Branch if Greater or Equal
                # Signed comparison
                rs1_val = self.registers[rs1]
                rs2_val = self.registers[rs2]
                if rs1_val & 0x80000000:
                    rs1_val = rs1_val - 0x100000000
                if rs2_val & 0x80000000:
                    rs2_val = rs2_val - 0x100000000
                take_branch = rs1_val >= rs2_val
                print(f"BGE x{rs1}, x{rs2}, {imm}: {rs1_val} >= {rs2_val} = {take_branch}")
            elif funct3 == 0x6:  # BLTU - Branch if Less Than Unsigned
                take_branch = (self.registers[rs1] & 0xFFFFFFFF) < (self.registers[rs2] & 0xFFFFFFFF)
                print(f"BLTU x{rs1}, x{rs2}, {imm}: {self.registers[rs1]} < {self.registers[rs2]} = {take_branch}")
            elif funct3 == 0x7:  # BGEU - Branch if Greater or Equal Unsigned
                take_branch = (self.registers[rs1] & 0xFFFFFFFF) >= (self.registers[rs2] & 0xFFFFFFFF)
                print(f"BGEU x{rs1}, x{rs2}, {imm}: {self.registers[rs1]} >= {self.registers[rs2]} = {take_branch}")
            else:
                print(f"Unknown funct3 for branch: {funct3}")
                return self.pc + 1
            
            if take_branch:
                return self.pc + (imm >> 1)  # Adjust for proper branching
            else:
                return self.pc + 1
        
        # U-type instruction format (LUI, AUIPC)
        elif opcode == 0b0110111 or opcode == 0b0010111:
            rd = (instruction >> 7) & 0x1F
            imm = instruction & 0xFFFFF000  # Top 20 bits
            
            # Ensure we only use registers 0-15 for RV32E
            if rd > 15:
                print(f"Error: Register number exceeds 15 in RV32E mode")
                return self.pc + 1
            
            # Register x0 is hardwired to 0
            if rd == 0:
                return self.pc + 1
            
            if opcode == 0b0110111:  # LUI - Load Upper Immediate
                self.registers[rd] = imm
                print(f"LUI x{rd}, 0x{imm >> 12:05X}: Loaded {imm:08X} to register {rd}")
            elif opcode == 0b0010111:  # AUIPC - Add Upper Immediate to PC
                self.registers[rd] = (self.pc + imm) & 0xFFFFFFFF
                print(f"AUIPC x{rd}, 0x{imm >> 12:05X}: PC {self.pc:08X} + {imm:08X} = {self.registers[rd]:08X}")
            
            return self.pc + 1
        
        # J-type instruction format (JAL)
        elif opcode == 0b1101111:
            rd = (instruction >> 7) & 0x1F
            
            # Extract and compose jump immediate
            imm_19_12 = (instruction >> 12) & 0xFF
            imm_11 = (instruction >> 20) & 0x1
            imm_10_1 = (instruction >> 21) & 0x3FF
            imm_20 = (instruction >> 31) & 0x1
            
            imm = (imm_10_1 << 1) | (imm_11 << 11) | (imm_19_12 << 12) | (imm_20 << 20)
            
            # Sign extend the 21-bit immediate
            if imm & 0x100000:
                imm |= 0xFFE00000
            
            # Ensure we only use registers 0-15 for RV32E
            if rd > 15:
                print(f"Error: Register number exceeds 15 in RV32E mode")
                return self.pc + 1
            
            # Calculate return address
            if rd != 0:
                self.registers[rd] = (self.pc + 1) & 0xFFFFFFFF
            
            # Jump to target address
            next_pc = (self.pc + (imm >> 1)) & 0xFFFFFFFF
            print(f"JAL x{rd}, {imm}: Jump from {self.pc:08X} to {next_pc:08X}, link {(self.pc + 1) & 0xFFFFFFFF:08X}")
            
            return next_pc
        
        # I-type instruction format (JALR)
        elif opcode == 0b1100111:
            rd = (instruction >> 7) & 0x1F
            funct3 = (instruction >> 12) & 0x7
            rs1 = (instruction >> 15) & 0x1F
            imm = (instruction >> 20) & 0xFFF
            
            # Sign extend the 12-bit immediate
            if imm & 0x800:
                imm |= 0xFFFFF000
            
            # Ensure we only use registers 0-15 for RV32E
            if rd > 15 or rs1 > 15:
                print(f"Error: Register number exceeds 15 in RV32E mode")
                return self.pc + 1
            
            if funct3 == 0x0:  # JALR - Jump and Link Register
                # Calculate return address
                if rd != 0:
                    self.registers[rd] = (self.pc + 1) & 0xFFFFFFFF
                
                # Jump to target address (rs1 + imm), clearing the lowest bit
                next_pc = (self.registers[rs1] + imm) & 0xFFFFFFFE
                print(f"JALR x{rd}, x{rs1}, {imm}: Jump from {self.pc:08X} to {next_pc:08X}, link {(self.pc + 1) & 0xFFFFFFFF:08X}")
                
                return next_pc
            else:
                print(f"Unknown funct3 for JALR: {funct3}")
                return self.pc + 1
        
        # M-extension instructions (multiplication and division)
        elif opcode == 0b0110011 and ((instruction >> 25) & 0x7F) == 0x01:
            rd = (instruction >> 7) & 0x1F
            funct3 = (instruction >> 12) & 0x7
            rs1 = (instruction >> 15) & 0x1F
            rs2 = (instruction >> 20) & 0x1F
            
            # Ensure we only use registers 0-15 for RV32E
            if rd > 15 or rs1 > 15 or rs2 > 15:
                print(f"Error: Register number exceeds 15 in RV32E mode")
                return self.pc + 1
            
            # Register x0 is hardwired to 0
            if rd == 0:
                return self.pc + 1
            
            # Multiplication operations
            if funct3 == 0x0:  # MUL - Multiply
                # Signed multiplication, lower 32 bits
                result = ((self.registers[rs1] * self.registers[rs2]) & 0xFFFFFFFF)
                self.registers[rd] = result
                print(f"MUL x{rd}, x{rs1}, x{rs2}: {self.registers[rs1]} * {self.registers[rs2]} = {result:08X}")
            elif funct3 == 0x1:  # MULH - Multiply High Signed
                # Convert to signed 32-bit integers
                rs1_val = self.registers[rs1]
                rs2_val = self.registers[rs2]
                if rs1_val & 0x80000000:
                    rs1_val = rs1_val - 0x100000000
                if rs2_val & 0x80000000:
                    rs2_val = rs2_val - 0x100000000
                
                # Full 64-bit multiplication
                result_64 = rs1_val * rs2_val