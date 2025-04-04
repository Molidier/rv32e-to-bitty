#!/usr/bin/env python3
# riscv32em_emulator.py

class RISCV32EMEmulator:
    def __init__(self):
        # For RISCV32E, we have only 16 registers (x0..x15); x0 is hardwired to 0.
        self.registers = [0] * 16
        self.pc = 0  # Program counter (index into the instruction list)
        
        # Instruction memory: list of 32-bit instructions
        self.instruction_memory = []
        try:
            with open("instructions_for_em.txt", "r") as infile:
                for line in infile:
                    line = line.strip()
                    if line:
                        # Each instruction is expected to be a 32-bit word in hex.
                        instr = int(line, 16)
                        self.instruction_memory.append(instr)
                        print(f"Loaded instruction: {instr:08X}")
        except FileNotFoundError:
            print("Error: Instructions file not found.")

        # Data memory: for simplicity, we simulate as a list of 1024 32-bit words.
        self.data_memory = [0] * 1024

    def sign_extend(self, value, bits):
        """Sign-extend the given value assuming it is 'bits' wide."""
        if (value >> (bits - 1)) & 1:
            return value | (~0 << bits)
        return value

    def run(self):
        """Run the emulator until we run out of instructions (or hit a safety limit)."""
        cycles = 0
        while 0 <= self.pc < len(self.instruction_memory):
            instr = self.instruction_memory[self.pc]
            new_pc = self.execute_instruction(instr)
            self.pc = new_pc
            cycles += 1
            if cycles > 1000:
                print("Cycle limit reached; halting to prevent infinite loop.")
                break

    def execute_instruction(self, instr):
        opcode = instr & 0x7F

        # R-type instructions (e.g., ADD, SUB, AND, OR, XOR, SLL, SRL, SRA, SLT, and MUL from the M-extension)
        if opcode == 0x33:
            rd   = (instr >> 7)  & 0x1F
            rs1  = (instr >> 15) & 0x1F
            rs2  = (instr >> 20) & 0x1F
            funct3 = (instr >> 12) & 0x7
            funct7 = (instr >> 25) & 0x7F

            # In RISCV32E, valid registers are 0..15.
            rd  &= 0xF
            rs1 &= 0xF
            rs2 &= 0xF

            if funct7 == 0x00:
                if funct3 == 0x0:  # ADD
                    result = (self.registers[rs1] + self.registers[rs2]) & 0xFFFFFFFF
                    print(f"ADD  x{rd}, x{rs1}, x{rs2}: {result:08X}")
                elif funct3 == 0x0 and funct7 == 0x20:  # SUB (should be checked separately)
                    result = (self.registers[rs1] - self.registers[rs2]) & 0xFFFFFFFF
                    print(f"SUB  x{rd}, x{rs1}, x{rs2}: {result:08X}")
                elif funct3 == 0x7:  # AND
                    result = self.registers[rs1] & self.registers[rs2]
                    print(f"AND  x{rd}, x{rs1}, x{rs2}: {result:08X}")
                elif funct3 == 0x6:  # OR
                    result = self.registers[rs1] | self.registers[rs2]
                    print(f"OR   x{rd}, x{rs1}, x{rs2}: {result:08X}")
                elif funct3 == 0x4:  # XOR
                    result = self.registers[rs1] ^ self.registers[rs2]
                    print(f"XOR  x{rd}, x{rs1}, x{rs2}: {result:08X}")
                elif funct3 == 0x1:  # SLL (Shift Left Logical)
                    shamt = self.registers[rs2] & 0x1F
                    result = (self.registers[rs1] << shamt) & 0xFFFFFFFF
                    print(f"SLL  x{rd}, x{rs1}, x{rs2}: {result:08X}")
                elif funct3 == 0x5:
                    shamt = self.registers[rs2] & 0x1F
                    if funct7 == 0x00:  # SRL (Shift Right Logical)
                        result = (self.registers[rs1] >> shamt) & 0xFFFFFFFF
                        print(f"SRL  x{rd}, x{rs1}, x{rs2}: {result:08X}")
                    elif funct7 == 0x20:  # SRA (Shift Right Arithmetic)
                        # Python’s >> on signed ints performs arithmetic shift.
                        result = (self.registers[rs1] >> shamt) & 0xFFFFFFFF
                        print(f"SRA  x{rd}, x{rs1}, x{rs2}: {result:08X}")
                    else:
                        result = 0
                        print("Unsupported shift instruction")
                elif funct3 == 0x2:  # SLT (Set Less Than)
                    # Compare as signed values.
                    result = 1 if self.registers[rs1] < self.registers[rs2] else 0
                    print(f"SLT  x{rd}, x{rs1}, x{rs2}: {result}")
                else:
                    result = 0
                    print("Unsupported R-type instruction")
            elif funct7 == 0x01:  # M extension instructions (only implement MUL as an example)
                if funct3 == 0x0:  # MUL
                    result = (self.registers[rs1] * self.registers[rs2]) & 0xFFFFFFFF
                    print(f"MUL  x{rd}, x{rs1}, x{rs2}: {result:08X}")
                else:
                    result = 0
                    print("Unsupported M-extension instruction")
            else:
                result = 0
                print("Unsupported R-type instruction")

            if rd != 0:  # Register x0 is read-only
                self.registers[rd] = result
            return self.pc + 1

        # I-type arithmetic (e.g., ADDI)
        elif opcode == 0x13:
            rd   = (instr >> 7)  & 0x1F
            rs1  = (instr >> 15) & 0x1F
            funct3 = (instr >> 12) & 0x7
            imm = self.sign_extend((instr >> 20) & 0xFFF, 12)

            rd  &= 0xF
            rs1 &= 0xF

            if funct3 == 0x0:  # ADDI
                result = (self.registers[rs1] + imm) & 0xFFFFFFFF
                print(f"ADDI x{rd}, x{rs1}, {imm}: {result:08X}")
            else:
                result = 0
                print("Unsupported I-type arithmetic instruction")
            if rd != 0:
                self.registers[rd] = result
            return self.pc + 1

        # I-type load instructions (only LW implemented as example)
        elif opcode == 0x03:
            rd   = (instr >> 7)  & 0x1F
            rs1  = (instr >> 15) & 0x1F
            funct3 = (instr >> 12) & 0x7
            imm = self.sign_extend((instr >> 20) & 0xFFF, 12)

            rd  &= 0xF
            rs1 &= 0xF

            address = self.registers[rs1] + imm
            if funct3 == 0x2:  # LW (Load Word)
                if 0 <= address < len(self.data_memory):
                    result = self.data_memory[address]
                else:
                    result = 0
                    print("Load address out of range")
                print(f"LW   x{rd}, {imm}(x{rs1}): {result:08X}")
            else:
                result = 0
                print("Unsupported load instruction")
            if rd != 0:
                self.registers[rd] = result
            return self.pc + 1

        # S-type store instructions (only SW implemented as example)
        elif opcode == 0x23:
            rs1  = (instr >> 15) & 0x1F
            rs2  = (instr >> 20) & 0x1F
            funct3 = (instr >> 12) & 0x7
            # Immediate is split between bits [31:25] and [11:7]
            imm = ((instr >> 25) << 5) | ((instr >> 7) & 0x1F)
            imm = self.sign_extend(imm, 12)

            rs1 &= 0xF
            rs2 &= 0xF

            address = self.registers[rs1] + imm
            if funct3 == 0x2:  # SW (Store Word)
                if 0 <= address < len(self.data_memory):
                    self.data_memory[address] = self.registers[rs2]
                    print(f"SW   x{rs2}, {imm}(x{rs1}) stored {self.registers[rs2]:08X} at address {address}")
                else:
                    print("Store address out of range")
            else:
                print("Unsupported store instruction")
            return self.pc + 1

        # B-type branch instructions (e.g., BEQ, BNE)
        elif opcode == 0x63:
            rs1  = (instr >> 15) & 0x1F
            rs2  = (instr >> 20) & 0x1F
            funct3 = (instr >> 12) & 0x7

            # Decode branch immediate:
            imm = (((instr >> 31) & 0x1) << 12) | \
                  (((instr >> 7)  & 0x1) << 11) | \
                  (((instr >> 25) & 0x3F) << 5) | \
                  (((instr >> 8)  & 0xF) << 1)
            imm = self.sign_extend(imm, 13)

            rs1 &= 0xF
            rs2 &= 0xF
            taken = False
            if funct3 == 0x0:  # BEQ
                if self.registers[rs1] == self.registers[rs2]:
                    taken = True
                    print(f"BEQ taken: x{rs1} == x{rs2}")
            elif funct3 == 0x1:  # BNE
                if self.registers[rs1] != self.registers[rs2]:
                    taken = True
                    print(f"BNE taken: x{rs1} != x{rs2}")
            else:
                print("Unsupported branch instruction")
            if taken:
                # pc is an instruction index; branch immediate is in bytes.
                return self.pc + (imm >> 2)
            else:
                return self.pc + 1

        # U-type instructions (LUI)
        elif opcode == 0x37:
            rd = (instr >> 7) & 0x1F
            imm = instr & 0xFFFFF000
            rd &= 0xF
            if rd != 0:
                self.registers[rd] = imm
            print(f"LUI  x{rd}, {imm:08X}")
            return self.pc + 1

        # J-type instruction (JAL)
        elif opcode == 0x6F:
            rd = (instr >> 7) & 0x1F
            # Decode JAL immediate:
            imm = (((instr >> 31) & 0x1) << 20) | \
                  (((instr >> 21) & 0x3FF) << 1) | \
                  (((instr >> 20) & 0x1) << 11) | \
                  (((instr >> 12) & 0xFF) << 12)
            imm = self.sign_extend(imm, 21)
            rd &= 0xF
            return_addr = self.pc + 1
            if rd != 0:
                # Save return address (in bytes) in rd.
                self.registers[rd] = return_addr * 4
            print(f"JAL  x{rd}, offset {imm}")
            return self.pc + (imm >> 2)

        # I-type JALR instruction
        elif opcode == 0x67:
            rd  = (instr >> 7)  & 0x1F
            rs1 = (instr >> 15) & 0x1F
            imm = self.sign_extend((instr >> 20) & 0xFFF, 12)
            rd  &= 0xF
            rs1 &= 0xF
            return_addr = self.pc + 1
            target = (self.registers[rs1] + imm) & ~1  # Ensure target is even
            if rd != 0:
                self.registers[rd] = return_addr * 4
            print(f"JALR x{rd}, x{rs1}, {imm}")
            return target // 4

        else:
            print(f"Unsupported opcode: {opcode:02X}")
            return self.pc + 1


if __name__ == "__main__":
    emulator = RISCV32EMEmulator()
    emulator.run()
