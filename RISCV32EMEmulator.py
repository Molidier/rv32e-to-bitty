# RISCV32EMEmulator.py

class RISCV32EMEmulator:
    def __init__(self, memory_array):
        # RISC-V has 32 registers (x0–x31), but RV32E uses only x0–x15
        self.registers = [i * 10 for i in range(16)]
        self.registers[0] = 0          # x0 is always zero
        self.pc = 0                    # program counter
        self.instruction_array = []
        self.memory_array = memory_array

        # Load hex‐encoded instructions from file
        try:
            with open("instructions_for_em.txt", "r") as infile:
                for line in infile:
                    instr = int(line.strip(), 16)
                    print(f"Instruction read and stored: {instr:08x}")
                    self.instruction_array.append(instr)
        except FileNotFoundError:
            print("Error opening file")

    def fetch_instruction(self):
        if 0 <= self.pc < len(self.instruction_array):
            return self.instruction_array[self.pc]
        else:
            print(f"PC out of range: {self.pc}")
            return 0  # treat as NOP

    def decode_and_execute(self, instruction):
        opcode = instruction & 0x7F
        print(f"Instruction @ PC={self.pc}: {instruction:08X}")

        # --- 1) M‑extension instructions (mul/div/rem) ---
        # opcode == 0110011 and funct7 == 0000001
        if opcode == 0b0110011 and ((instruction >> 25) & 0x7F) == 0x01:
            rd     = (instruction >> 7)  & 0x1F
            funct3 = (instruction >> 12) & 0x7
            rs1    = (instruction >> 15) & 0x1F
            rs2    = (instruction >> 20) & 0x1F

            # RV32E register bounds
            if rd > 15 or rs1 > 15 or rs2 > 15:
                print("Error: Register number exceeds 15 in RV32E mode")
                return self.pc + 1
            if rd == 0:
                return self.pc + 1

            # Fetch operand values
            v1 = self.registers[rs1]
            v2 = self.registers[rs2]
            # Signed views
            s1 = v1 if v1 < 0x80000000 else v1 - 0x100000000
            s2 = v2 if v2 < 0x80000000 else v2 - 0x100000000

            if   funct3 == 0x0:  # MUL
                result = (s1 * s2) & 0xFFFFFFFF
                print(f"MUL x{rd}, x{rs1}, x{rs2}: {s1} * {s2} = {result:08X}")
            elif funct3 == 0x1:  # MULH (high signed × signed)
                full = s1 * s2
                result = (full >> 32) & 0xFFFFFFFF
                print(f"MULH x{rd}, x{rs1}, x{rs2}: high({s1}*{s2}) = {result:08X}")
            elif funct3 == 0x2:  # MULHSU (high signed × unsigned)
                full = s1 * v2
                result = (full >> 32) & 0xFFFFFFFF
                print(f"MULHSU x{rd}, x{rs1}, x{rs2}: high({s1}*{v2}) = {result:08X}")
            elif funct3 == 0x3:  # MULHU (high unsigned × unsigned)
                full = v1 * v2
                result = (full >> 32) & 0xFFFFFFFF
                print(f"MULHU x{rd}, x{rs1}, x{rs2}: high({v1}*{v2}) = {result:08X}")
            elif funct3 == 0x4:  # DIV (signed)
                if s2 == 0:
                    result = 0xFFFFFFFF  # per spec: -1
                elif s1 == -0x80000000 and s2 == -1:
                    result = s1 & 0xFFFFFFFF
                else:
                    result = int(s1 // s2) & 0xFFFFFFFF
                print(f"DIV x{rd}, x{rs1}, x{rs2}: {s1}//{s2} = {result:08X}")
            elif funct3 == 0x5:  # DIVU (unsigned)
                if v2 == 0:
                    result = 0xFFFFFFFF
                else:
                    result = (v1 // v2) & 0xFFFFFFFF
                print(f"DIVU x{rd}, x{rs1}, x{rs2}: {v1}//{v2} = {result:08X}")
            elif funct3 == 0x6:  # REM (signed remainder)
                if s2 == 0:
                    result = s1 & 0xFFFFFFFF
                elif s1 == -0x80000000 and s2 == -1:
                    result = 0
                else:
                    result = int(s1 % s2) & 0xFFFFFFFF
                print(f"REM x{rd}, x{rs1}, x{rs2}: {s1}%{s2} = {result:08X}")
            elif funct3 == 0x7:  # REMU (unsigned remainder)
                if v2 == 0:
                    result = v1 & 0xFFFFFFFF
                else:
                    result = (v1 % v2) & 0xFFFFFFFF
                print(f"REMU x{rd}, x{rs1}, x{rs2}: {v1}%{v2} = {result:08X}")
            else:
                print(f"Unknown M‑extension funct3: {funct3}")
                return self.pc + 1

            self.registers[rd] = result
            return self.pc + 1

        # --- 2) Standard R‑type (ADD, SUB, SLL, etc.) ---
        elif opcode == 0b0110011:
            rd     = (instruction >> 7)  & 0x1F
            funct3 = (instruction >> 12) & 0x7
            rs1    = (instruction >> 15) & 0x1F
            rs2    = (instruction >> 20) & 0x1F
            funct7 = (instruction >> 25) & 0x7F

            if rd > 15 or rs1 > 15 or rs2 > 15:
                print("Error: Register number exceeds 15 in RV32E mode")
                return self.pc + 1

            # x0 stays zero
            if rd == 0:
                return self.pc + 1

            if funct3 == 0x0:
                if funct7 == 0x00:  # ADD
                    result = (self.registers[rs1] + self.registers[rs2]) & 0xFFFFFFFF
                    print(f"ADD x{rd}, x{rs1}, x{rs2}: {result}")
                elif funct7 == 0x20:  # SUB
                    result = (self.registers[rs1] - self.registers[rs2]) & 0xFFFFFFFF
                    print(f"SUB x{rd}, x{rs1}, x{rs2}: {result}")
                else:
                    print(f"Unknown funct7 for ADD/SUB: {funct7}")
                    return self.pc + 1
            elif funct3 == 0x1:  # SLL
                sh = self.registers[rs2] & 0x1F
                result = (self.registers[rs1] << sh) & 0xFFFFFFFF
                print(f"SLL x{rd}, x{rs1}, x{rs2}: <<{sh} = {result}")
            elif funct3 == 0x2:  # SLT
                # signed compare
                a = self.registers[rs1]
                b = self.registers[rs2]
                sa = a if a < 0x80000000 else a - 0x100000000
                sb = b if b < 0x80000000 else b - 0x100000000
                result = 1 if sa < sb else 0
                print(f"SLT x{rd}, x{rs1}, x{rs2}: {sa}<{sb} = {result}")
            elif funct3 == 0x3:  # SLTU
                result = 1 if (self.registers[rs1] & 0xFFFFFFFF) < (self.registers[rs2] & 0xFFFFFFFF) else 0
                print(f"SLTU x{rd}, x{rs1}, x{rs2}: = {result}")
            elif funct3 == 0x4:  # XOR
                result = self.registers[rs1] ^ self.registers[rs2]
                print(f"XOR x{rd}, x{rs1}, x{rs2}: = {result}")
            elif funct3 == 0x5:
                if funct7 == 0x00:  # SRL
                    sh = self.registers[rs2] & 0x1F
                    result = (self.registers[rs1] >> sh) & 0xFFFFFFFF
                    print(f"SRL x{rd}, x{rs1}, x{rs2}: >>{sh} = {result}")
                elif funct7 == 0x20:  # SRA
                    sh = self.registers[rs2] & 0x1F
                    val = self.registers[rs1]
                    if val & 0x80000000:
                        mask = ((1 << sh) - 1) << (32 - sh)
                        result = ((val >> sh) | mask) & 0xFFFFFFFF
                    else:
                        result = (val >> sh) & 0xFFFFFFFF
                    print(f"SRA x{rd}, x{rs1}, x{rs2}: >>a{sh} = {result}")
                else:
                    print(f"Unknown funct7 for SRL/SRA: {funct7}")
                    return self.pc + 1
            elif funct3 == 0x6:  # OR
                result = self.registers[rs1] | self.registers[rs2]
                print(f"OR x{rd}, x{rs1}, x{rs2}: = {result}")
            elif funct3 == 0x7:  # AND
                result = self.registers[rs1] & self.registers[rs2]
                print(f"AND x{rd}, x{rs1}, x{rs2}: = {result}")
            else:
                print(f"Unknown funct3 for R‑type: {funct3}")
                return self.pc + 1

            self.registers[rd] = result
            return self.pc + 1

        # --- 3) I‑type (immediate arithmetic and loads) ---
        elif opcode in (0b0010011, 0b0000011):
            rd     = (instruction >> 7)  & 0x1F
            funct3 = (instruction >> 12) & 0x7
            rs1    = (instruction >> 15) & 0x1F
            imm    = (instruction >> 20) & 0xFFF
            # sign‑extend
            if imm & 0x800:
                imm |= 0xFFFFF000

            if rd > 15 or rs1 > 15:
                print("Error: Register number exceeds 15 in RV32E mode")
                return self.pc + 1

            # --- arithmetic immediates ---
            if opcode == 0b0010011:
                if rd == 0:
                    return self.pc + 1
                if   funct3 == 0x0:  # ADDI
                    result = (self.registers[rs1] + imm) & 0xFFFFFFFF
                    print(f"ADDI x{rd}, x{rs1}, {imm} = {result}")
                elif funct3 == 0x1:  # SLLI
                    sh = imm & 0x1F
                    result = (self.registers[rs1] << sh) & 0xFFFFFFFF
                    print(f"SLLI x{rd}, x{rs1}, {sh} = {result}")
                elif funct3 == 0x2:  # SLTI
                    # similar signed logic...
                    sa = self.registers[rs1]
                    sa = sa if sa < 0x80000000 else sa - 0x100000000
                    imm_s = imm if imm < 0x800 else imm - 0x1000
                    result = 1 if sa < imm_s else 0
                    print(f"SLTI x{rd}, x{rs1}, {imm_s} = {result}")
                elif funct3 == 0x3:  # SLTIU
                    result = 1 if (self.registers[rs1] & 0xFFFFFFFF) < (imm & 0xFFFFFFFF) else 0
                    print(f"SLTIU x{rd}, x{rs1}, {imm} = {result}")
                elif funct3 == 0x4:  # XORI
                    result = self.registers[rs1] ^ imm
                    print(f"XORI x{rd}, x{rs1}, {imm} = {result}")
                elif funct3 == 0x5:  # SRLI/SRAI
                    sh = imm & 0x1F
                    t = (imm >> 5) & 0x7F
                    if t == 0x00:
                        result = (self.registers[rs1] >> sh) & 0xFFFFFFFF
                        print(f"SRLI x{rd}, x{rs1}, {sh} = {result}")
                    elif t == 0x20:
                        val = self.registers[rs1]
                        if val & 0x80000000:
                            mask = ((1 << sh) - 1) << (32 - sh)
                            result = ((val >> sh) | mask) & 0xFFFFFFFF
                        else:
                            result = (val >> sh) & 0xFFFFFFFF
                        print(f"SRAI x{rd}, x{rs1}, {sh} = {result}")
                    else:
                        print(f"Unknown shift type: {t}")
                        return self.pc + 1
                elif funct3 == 0x6:  # ORI
                    result = self.registers[rs1] | imm
                    print(f"ORI x{rd}, x{rs1}, {imm} = {result}")
                elif funct3 == 0x7:  # ANDI
                    result = self.registers[rs1] & imm
                    print(f"ANDI x{rd}, x{rs1}, {imm} = {result}")
                else:
                    print(f"Unknown funct3 for I‑type: {funct3}")
                    return self.pc + 1

                if rd != 0:
                    self.registers[rd] = result

            # --- loads ---
            else:  # opcode == 0000011
                address = (self.registers[rs1] + imm) & 0xFFFFFFFF
                if address >= len(self.memory_array):
                    print(f"Memory access out of bounds: {address}")
                    address %= len(self.memory_array)

                if rd == 0:
                    return self.pc + 1

                if funct3 == 0x0:   # LB
                    val = self.memory_array[address] & 0xFF
                    if val & 0x80: val |= 0xFFFFFF00
                    self.registers[rd] = val
                    print(f"LB x{rd}, {imm}(x{rs1}) = {val:08X}")
                elif funct3 == 0x1: # LH
                    if address % 2 != 0: address -= 1
                    val = self.memory_array[address] & 0xFFFF
                    if val & 0x8000: val |= 0xFFFF0000
                    self.registers[rd] = val
                    print(f"LH x{rd}, {imm}(x{rs1}) = {val:08X}")
                elif funct3 == 0x2: # LW
                    val = self.memory_array[address]
                    self.registers[rd] = val
                    print(f"LW x{rd}, {imm}(x{rs1}) = {val:08X}")
                elif funct3 == 0x4: # LBU
                    val = self.memory_array[address] & 0xFF
                    self.registers[rd] = val
                    print(f"LBU x{rd}, {imm}(x{rs1}) = {val:08X}")
                elif funct3 == 0x5: # LHU
                    if address % 2 != 0: address -= 1
                    val = self.memory_array[address] & 0xFFFF
                    self.registers[rd] = val
                    print(f"LHU x{rd}, {imm}(x{rs1}) = {val:08X}")
                else:
                    print(f"Unknown funct3 for load: {funct3}")
                    return self.pc + 1

            return self.pc + 1

        # --- 4) S‑type (stores) ---
        elif opcode == 0b0100011:
            funct3    = (instruction >> 12) & 0x7
            rs1       = (instruction >> 15) & 0x1F
            rs2       = (instruction >> 20) & 0x1F
            imm_lo    = (instruction >> 7)  & 0x1F
            imm_hi    = (instruction >> 25) & 0x7F
            imm       = (imm_hi << 5) | imm_lo
            if imm & 0x800: imm |= 0xFFFFF000

            if rs1 > 15 or rs2 > 15:
                print("Error: Register number exceeds 15 in RV32E mode")
                return self.pc + 1

            addr = (self.registers[rs1] + imm) & 0xFFFFFFFF
            if addr >= len(self.memory_array):
                print(f"Memory access out of bounds: {addr}")
                return self.pc + 1

            if funct3 == 0x0:   # SB
                b = self.registers[rs2] & 0xFF
                self.memory_array[addr] = (self.memory_array[addr] & 0xFFFFFF00) | b
                print(f"SB x{rs2}, {imm}(x{rs1})")
            elif funct3 == 0x1: # SH
                if addr % 2 != 0:
                    print(f"Misaligned SH at {addr}")
                    return self.pc + 1
                h = self.registers[rs2] & 0xFFFF
                self.memory_array[addr] = (self.memory_array[addr] & 0xFFFF0000) | h
                print(f"SH x{rs2}, {imm}(x{rs1})")
            elif funct3 == 0x2: # SW
                if addr % 4 != 0:
                    print(f"Misaligned SW at {addr}")
                    return self.pc + 1
                w = self.registers[rs2]
                self.memory_array[addr] = w
                print(f"SW x{rs2}, {imm}(x{rs1})")
            else:
                print(f"Unknown funct3 for store: {funct3}")
                return self.pc + 1

            return self.pc + 1

        # --- 5) B‑type (branches) ---
        elif opcode == 0b1100011:
            funct3 = (instruction >> 12) & 0x7
            rs1    = (instruction >> 15) & 0x1F
            rs2    = (instruction >> 20) & 0x1F
            bit7   = (instruction >> 31) & 0x1
            bit11  = (instruction >> 7)  & 0x1
            bits4_1  = (instruction >> 8)  & 0xF
            bits10_5 = (instruction >> 25) & 0x3F
            imm = (bit7 << 12) | (bit11 << 11) | (bits10_5 << 5) | (bits4_1 << 1)
            if imm & 0x1000: imm |= 0xFFFFE000

            if rs1 > 15 or rs2 > 15:
                print("Error: Register number exceeds 15 in RV32E mode")
                return self.pc + 1

            a = self.registers[rs1]
            b = self.registers[rs2]
            take = False
            if funct3 == 0x0:   # BEQ
                take = (a == b)
            elif funct3 == 0x1: # BNE
                take = (a != b)
            elif funct3 == 0x4: # BLT
                sa = a if a < 0x80000000 else a - 0x100000000
                sb = b if b < 0x80000000 else b - 0x100000000
                take = (sa < sb)
            elif funct3 == 0x5: # BGE
                sa = a if a < 0x80000000 else a - 0x100000000
                sb = b if b < 0x80000000 else b - 0x100000000
                take = (sa >= sb)
            elif funct3 == 0x6: # BLTU
                take = (a & 0xFFFFFFFF) < (b & 0xFFFFFFFF)
            elif funct3 == 0x7: # BGEU
                take = (a & 0xFFFFFFFF) >= (b & 0xFFFFFFFF)
            else:
                print(f"Unknown branch funct3: {funct3}")
                return self.pc + 1

            print(f"{'TAKE' if take else 'NO'} BRANCH {funct3} imm={imm}")
            return self.pc + (imm >> 1) if take else self.pc + 1

        # --- 6) U‑type (LUI/AUIPC) ---
        elif opcode in (0b0110111, 0b0010111):
            rd  = (instruction >> 7) & 0x1F
            imm = instruction & 0xFFFFF000
            if rd > 15:
                print("Error: Register number exceeds 15 in RV32E mode")
                return self.pc + 1
            if rd == 0:
                return self.pc + 1

            if opcode == 0b0110111:  # LUI
                self.registers[rd] = imm
                print(f"LUI x{rd}, 0x{imm>>12:X}")
            else:                    # AUIPC
                self.registers[rd] = (self.pc + imm) & 0xFFFFFFFF
                print(f"AUIPC x{rd}, 0x{imm>>12:X}")

            return self.pc + 1

        # --- 7) J‑type (JAL) ---
        elif opcode == 0b1101111:
            rd = (instruction >> 7) & 0x1F
            # imm[20|10:1|11|19:12]
            bit20    = (instruction >> 31) & 0x1
            bits10_1 = (instruction >> 21) & 0x3FF
            bit11    = (instruction >> 20) & 0x1
            bits19_12= (instruction >> 12) & 0xFF
            imm = (bit20 << 20) | (bits19_12 << 12) | (bit11 << 11) | (bits10_1 << 1)
            if imm & 0x100000: imm |= 0xFFE00000

            if rd <= 15 and rd != 0:
                self.registers[rd] = (self.pc + 1) & 0xFFFFFFFF
            next_pc = (self.pc + (imm >> 1)) & 0xFFFFFFFF
            print(f"JAL x{rd}, imm={imm} -> PC={next_pc}")
            return next_pc

        # --- 8) I‑type JALR ---
        elif opcode == 0b1100111:
            rd     = (instruction >> 7)  & 0x1F
            funct3 = (instruction >> 12) & 0x7
            rs1    = (instruction >> 15) & 0x1F
            imm    = (instruction >> 20) & 0xFFF
            if imm & 0x800: imm |= 0xFFFFF000

            if funct3 != 0x0 or rd > 15 or rs1 > 15:
                print(f"Unknown or out‑of‑range JALR")
                return self.pc + 1

            ret = (self.pc + 1) & 0xFFFFFFFF
            next_pc = (self.registers[rs1] + imm) & 0xFFFFFFFE
            if rd != 0:
                self.registers[rd] = ret
            print(f"JALR x{rd}, x{rs1}, {imm}: -> PC={next_pc}")
            return next_pc

        else:
            print(f"Unknown opcode: {opcode:02b}")
            return self.pc + 1
