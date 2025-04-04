class RiscVConverter:
    opcodes = {
        0b0110011: "R",
        0b0110111: "lui",
        0b1101111: "jal",
        0b1100111: "jalr",
    }

    bitty_alu_instr = {
        "add": (0b0000, 0b00),
        "sub": (0b0001, 0b00),
        "and": (0b0010, 0b00),
        "or":  (0b0011, 0b00),
        "xor": (0b0100, 0b00),
        "shl": (0b0101, 0b00),
        "shr": (0b0110, 0b00),
        "cmp": (0b0111, 0b00), 
        "shrs": (0b1000, 0b00),
        "cmps": (0b1001, 0b00),
    
        "addi": (0b0000, 0b01),
        "subi": (0b0001, 0b01),
        "andi": (0b0010, 0b01),
        "ori":  (0b0011, 0b01),
        "xori": (0b0100, 0b01),
        "shli": (0b0101, 0b01),
        "shri": (0b0110, 0b01),
        "cmpi": (0b0111, 0b01),
    
        "bie": (0b00,    0b10),
        "bil": (0b01,    0b10),
        "big": (0b10,    0b10),
    }

    r_m_instr = {
        # Base RV32I R-type
        (0b0000000, 0b000): "add",
        (0b0100000, 0b000): "sub",
        (0b0000000, 0b001): "sll",
        (0b0000000, 0b010): "slt",
        (0b0000000, 0b011): "sltu",
        (0b0000000, 0b100): "xor",
        (0b0000000, 0b101): "srl",
        (0b0100000, 0b101): "sra",
        (0b0000000, 0b110): "or",
        (0b0000000, 0b111): "and",

        # M extension (RV32M)
        (0b0000001, 0b000): "mul",
        (0b0000001, 0b001): "mulh",
        (0b0000001, 0b010): "mulhsu",
        (0b0000001, 0b011): "mulhu",
        (0b0000001, 0b100): "div",
        (0b0000001, 0b101): "divu",
        (0b0000001, 0b110): "rem",
        (0b0000001, 0b111): "remu",
    }

    @staticmethod
    def identify_the_type(opcode):
        return RiscVConverter.opcodes.get(opcode, "unknown")

    @staticmethod
    def r_type(funct3, funct7):
        return RiscVConverter.r_m_instr.get((funct7, funct3), "unknown")

    @staticmethod
    def lego(instruction):
        opcode = instruction & 0b1111111
        rd     = (instruction >> 7) & 0b11111     # bits [11:7]
        rs1    = (instruction >> 15) & 0b11111    # bits [19:15]
        rs2    = (instruction >> 20) & 0b11111    # bits [24:20]
        instr_type = RiscVConverter.identify_the_type(opcode)
        if instr_type == "R":
            funct3 = (instruction >> 12) & 0b111      # bits [14:12]
            funct7 = (instruction >> 25) & 0b1111111  # bits [31:25]
            return instr_type, (RiscVConverter.r_type(funct3, funct7), rd, rs1, rs2)
        else:
            return "unknown"

    @staticmethod
    def riscV_to_bitty(instruction):
        instr_type, instr = RiscVConverter.lego(instruction)
        if instr_type == "R":
            result = []
            opcode = instr[0]
            rd     = int(instr[1])
            rs1    = int(instr[2])
            rs2    = int(instr[3])
            if rd != rs1 and rd != rs2:
                result.append(("sub", rd, rd))
                result.append(("add", rd, rs1))
            elif rd != rs1 and rd == rs2:
                #use x0 as rd
                rd = 0b0000                    
                result.append(("add", rd, rs1))


            if opcode in RiscVConverter.bitty_alu_instr:
                result.append((opcode, rd, rs2))
            else:
                if opcode == 'srl':
                    result.append(("shr", rd, rs2))
                elif opcode == 'sll':
                    result.append(("shl", rd, rs2))
                elif opcode == 'sra':
                    result.append(("shrs", rd, rs2)) # signed right shift -> should be implemented  
                elif opcode == 'slt' or opcode == 'sltu':
                    if opcode == 'slt':
                        result.append(("cmps", rd, rs2)) # signed comparison -> should be implemented
                    else:
                        result.append(("cmp", rd, rs2))
                    # branch and set handling
                    result.append(("bie", 8, None)) # big assign_one -> 4th instr after this
                    result.append(("bil", 6, None)) # big assign_one -> 3rd instr after this
                    result.append(("sub", rd, rd)) 
                    result.append(("addi", rd, 1))
                    result.append(("sub", rd, rd))
                else:
                    return "unknown"
            

            return result

    @staticmethod
    def bitty_to_binary(init_instr):
        instructions = RiscVConverter.riscV_to_bitty(init_instr)
        final_instructions = []
        # Convert the instruction to binary format
        for instr in instructions:
            opcode, rx, ry = instr

            mapping_value = RiscVConverter.bitty_alu_instr.get(opcode)
            if mapping_value is None:
                raise KeyError(f"Opcode {opcode} not found in bitty_alu_instr mapping.")
            alu, fmt = mapping_value

            instruction = 0

            if fmt == 0:
                # Construct the instruction
                reserved = 0b00

                # Place rx in bits [15:12]
                instruction |= (rx & 0b1111) << 12

                # Place ry in bits [11:8]
                instruction |= (ry & 0b1111) << 8

                # Place reserved in bits [7:6]
                instruction |= (reserved & 0b11) << 6

                # Place alu in bits [5:2]
                instruction |= (alu & 0b1111) << 2

                # Place format in bits [1:0]
                instruction |= (fmt & 0b11)
            elif fmt == 1:
                immid = ry
                # Place rx at bits [15:12]
                instruction |= (rx & 0xF) << 12
                # Place immid at bits [11:6]
                instruction |= (immid & 0x3F) << 6
                # Place alu at bits [5:2]
                instruction |= (alu & 0xF) << 2
                # Place format at bits [1:0]
                instruction |= (fmt & 0x3)
            elif fmt == 2:
                immid = rx
                cond = alu

                # Place immid in bits [15:4]
                instruction |= (immid & 0xFFF) << 4  # mask immid to 12 bits

                # Place cond in bits [3:2]
                instruction |= (cond & 0b11) << 2    # mask cond to 2 bits

                # Place the fixed pattern 0b10 in bits [1:0]
                instruction |= 0b10  # decimal 2, binary 10

            final_instructions.append(instruction)
        
        return final_instructions
