class RiscVConverter:
    # Class variable to track the program counter
    RISCV_PC = 0
    Bitty_PC = 0
    map_pc = {} #RiscV PC to Bitty PC mapping
    branch_pc = {} #Branch instrcutions PC -> PC + offset mapping
    instr_of_bitty_assembly = [] #List of instructions to be executed -> each element is tuple of three elements
    instr_of_bitty_binary = []

    def change_branch_offsets():
        for branch_bitty_pc, pc in RiscVConverter.branch_pc.items():
            #(BittyPC - branch_pc) * 2
            new_offset = (RiscVConverter.map_pc[pc] - branch_bitty_pc) * 2
            branch, _, placeholder = RiscVConverter.instr_of_bitty_assembly[branch_bitty_pc]
            new_instr = (branch, new_offset, placeholder)
            new_binary = RiscVConverter.bitty_to_binary(new_instr)
            print("Branch instruction:", branch, "New offset:", new_offset, )
            #add new instrucitons to the list of instructions
            RiscVConverter.instr_of_bitty_assembly[branch_bitty_pc] = new_instr
            RiscVConverter.instr_of_bitty_binary[branch_bitty_pc] = new_binary
    
    def print_assembly():
        for i, instr in enumerate(RiscVConverter.instr_of_bitty_assembly):
            print(f"Instruction {i}: {instr}")
    
    def print_binary():
        with open("bitty_binary.txt", "w") as f:
            for i, instr in enumerate(RiscVConverter.instr_of_bitty_binary):
                f.write(f"0b{instr:016b}\n")


    opcodes = {
        0b0110011: "R",
        0b0000011: "I", #load instructions
        0b0010011: "I", #ALU immediate instructions
        0b1100011: "B", #branch instructions
        0b1101111: "J",
        0b1100111: "J",
        0b0010111: "U",
        0b0110111: "U",
        0b0100011: "S", #store instructions

    }

    bitty_alu_instr = {
        "add":   (0b0000, 0b00),
        "sub":   (0b0001, 0b00),
        "and":   (0b0010, 0b00),
        "or":    (0b0011, 0b00),
        "xor":   (0b0100, 0b00),
        "shl":   (0b0101, 0b00),
        "shr":   (0b0110, 0b00),
        "cmp":   (0b0111, 0b00), 
        "shrs":  (0b1000, 0b00),
        "cmps":  (0b1001, 0b00),
    
        "addi":  (0b0000, 0b01),
        "subi":  (0b0001, 0b01),
        "andi":  (0b0010, 0b01),
        "ori":   (0b0011, 0b01),
        "xori":  (0b0100, 0b01),
        "shli":  (0b0101, 0b01),
        "shri":  (0b0110, 0b01),
        "cmpi":  (0b0111, 0b01),
        "shrsi": (0b1000, 0b01),
        "cmpsi": (0b1001, 0b01),
        
        "bie":   (0b00,   0b10),
        "big":   (0b01,   0b10),
        "bil":   (0b10,   0b10),
        #pc edition
        "gtpc":  (0b011,  0b10), #get pc to rx
        "stpc":  (0b111,  0b10), #set pc from rx
        
        "ld":    (0b0,    0b11),
        "st":    (0b1,    0b11),


    }
    # R-type instructions (Base RV32I + M extension)
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

    # I-type ALU instructions (non-shift) – opcode = 0b0010011
    i_instr = {
        0b000: "addi",   # imm[11:0], rs1, 000, rd, 0010011
        0b010: "slti",   # imm[11:0], rs1, 010, rd, 0010011
        0b011: "sltiu",  # imm[11:0], rs1, 011, rd, 0010011
        0b100: "xori",   # imm[11:0], rs1, 100, rd, 0010011
        0b110: "ori",    # imm[11:0], rs1, 110, rd, 0010011
        0b111: "andi",   # imm[11:0], rs1, 111, rd, 0010011
    }

    # I-type shift-immediate instructions – opcode = 0b0010011
    # Keyed by (funct7, funct3) from imm[11:5] and imm[4:2], etc.
    i_shift_instr = {
        (0b0000000, 0b001): "slli",
        (0b0000000, 0b101): "srli",
        (0b0100000, 0b101): "srai",
    }

    # I-type LOAD instructions – opcode = 0b0000011
    # funct3 selects which load variant
    l_instr = {
        0b000: "lb",   # load byte
        0b001: "lh",   # load halfword
        0b010: "lw",   # load word
        0b100: "lbu",  # load byte unsigned
        0b101: "lhu",  # load halfword unsigned
    }

    # S-type instructions (Store) – opcode = 0b0100011
    s_instr = {
        0b000: "sb",   # store byte
        0b001: "sh",   # store halfword
        0b010: "sw",   # store word
    }

    # B-type instructions (Branch) – opcode = 0b1100011
    b_instr = {
        0b000: "beq",   # branch if equal
        0b001: "bne",   # branch if not equal
        0b100: "blt",   # branch if less than
        0b101: "bge",   # branch if greater than or equal
        0b110: "bltu",  # branch if less than (unsigned)
        0b111: "bgeu",  # branch if greater/equal (unsigned)
    }

    # U-type instructions
    # LUI: opcode = 0b0110111, AUIPC: opcode = 0b0010111
    u_instr = {
        0b0110111: "lui",    # load upper immediate
        0b0010111: "auipc",  # add upper immediate to pc
    }

    # J-type instruction (only one in RV32EM)
    # JAL: opcode = 0b1101111
    j_instr = {
        0b1101111: "jal",    # jump and link
    }


    @staticmethod
    def identify_the_type(opcode):
        return RiscVConverter.opcodes.get(opcode, "unknown")

    @staticmethod
    def r_type(funct3, funct7):
        return RiscVConverter.r_m_instr.get((funct7, funct3), "unknown")
    

    @staticmethod
    def lego(instruction):
        opcode = instruction         & 0b1111111
        rd     = (instruction >> 7)  & 0b11111     # bits [11:7]
        rs1    = (instruction >> 15) & 0b11111    # bits [19:15]
        rs2    = (instruction >> 20) & 0b11111    # bits [24:20]
        instr_type = RiscVConverter.identify_the_type(opcode)
        if instr_type == "R":
            funct3 = (instruction >> 12) & 0b111      # bits [14:12]
            funct7 = (instruction >> 25) & 0b1111111  # bits [31:25]
            return instr_type, (RiscVConverter.r_type(funct3, funct7), rd, rs1, rs2)
        #I type instruction decoding
        elif instr_type == "I":
            print("I type instruction in lego")
            funct3 = (instruction >> 12) & 0b111
            funct7 = (instruction >> 25) & 0b1111111
            print("Lego:",
                format(funct3, '03b'),
                format(funct7, '07b'),
                format(rd, '05b'),
                format(rs1, '05b'),
                format(rs2, '05b'))
            if opcode == 0b0010011 and funct3 in RiscVConverter.i_instr: # ALU immediate instructions
                immediate = (instruction >> 20) & 0b111111111111
                return instr_type, (RiscVConverter.i_instr[funct3], rd, rs1, immediate)
            elif opcode == 0b0010011 and (funct3, funct7) in RiscVConverter.i_shift_instr: # Load instructions
                shamt =  (instruction >> 20) & 0b111111
                print("I type instruction in lego shift")
                print(funct7, funct3, rd, rs1, shamt)
                return instr_type, (RiscVConverter.i_shift_instr[(funct7, funct3)], rd, rs1, shamt)
            elif opcode == 0b0000011 and funct3 in RiscVConverter.l_instr: # Load instructions
                immediate = (instruction >> 20) & 0b111111111111
                return instr_type, (RiscVConverter.l_instr[funct3], rd, rs1, immediate)
            else:
                print("Unknown instruction type")
        elif instr_type == "B":
            funct3 = (instruction >> 12) & 0b111
            imm_12   = (instruction >> 31) & 0x1      # instruction[31]
            imm_10_5 = (instruction >> 25) & 0x3F     # instruction[30:25]
            imm_4_1  = (instruction >>  8) & 0xF      # instruction[11:8]
            imm_11   = (instruction >>  7) & 0x1      # instruction[7]
            immediate = (imm_12   << 12) \
                    | (imm_11   << 11) \
                    | (imm_10_5 <<  5) \
                    | (imm_4_1  <<  1)
            #Saving branch information for the future usage
            return instr_type, (RiscVConverter.b_instr[funct3], rs1, rs2, immediate)
        elif instr_type == "U":
            immediate = (instruction >> 12) & 0xFFFFF # instruction[31:12]
            if opcode == 0b0110111:
                return instr_type, ("lui", rd, immediate, None)
            elif opcode == 0b0010111:
                return instr_type, ("auipc", rd, immediate, None)
        elif instr_type == "J":
            if opcode == 0b1101111: # JAL instruction
                # Extract the components of the immediate:
                imm_20 = (instruction >> 20) & 0x1           # imm[20]
                imm_10_1 = (instruction >> 1) & 0x3FF         # imm[10:1] (10 bits)
                imm_11 = (instruction >> 11) & 0x1            # imm[11]
                imm_19_12 = (instruction >> 12) & 0xFF        # imm[19:12] (8 bits)

                # Concatenate the parts to form the full 20-bit immediate
                immediate = (imm_20 << 19) | (imm_19_12 << 11) | (imm_11 << 10) | imm_10_1
                
                return instr_type, ("jal", rd, immediate, None)
            elif opcode == 0b1100111: # JALR instruction:
                immediate = (instruction >> 20) & 0xFFF 
                return instr_type, ("jalr", rd, rs1, immediate)  
        elif instr_type == "S":
            imm_11_5 = (instruction >> 25) & 0x7F
            imm_4_0  = (instruction >> 7)  & 0x1F
            funct3 = (instruction >> 12) & 0b111
            immediate = (imm_11_5 << 5) | imm_4_0           # combine into imm[11:0]
            # sign-extend the 12-bit value:
            if immediate & (1 << 11):
                immediate |= - (1 << 12)

            if funct3 in RiscVConverter.s_instr:
                immediate = (imm_11_5 << 5) | imm_4_0
                return instr_type, (RiscVConverter.s_instr[funct3], rs1, rs2, immediate)
        
        return "unknown"

    @staticmethod
    def riscV_to_bitty(instruction):
        instr_type, instr = RiscVConverter.lego(instruction)
        rd_is_R0 = False
        result = []
        opcode_binary = instruction & 0b1111111


        if instr_type == "R":
            opcode = instr[0]
            rd     = int(instr[1])
            rs1    = int(instr[2])
            rs2    = int(instr[3])

            #Handling the case when rd != rs1 != rs2
            if rd != rs1 and rd != rs2 and opcode not in ["mul", "mulh", "mulhsu", "mulhu", "div", "rem", "divu", "remu"]:
                result.append(("sub", rd, rd))
                result.append(("add", rd, rs1))
            #Handling the case when rd == rs2
            elif rd != rs1 and rd == rs2:
                #use x0 as rd
                rd = 0b0000                    
                result.append(("add", rd, rs1))
                rd_is_R0 = True
            
            #Else (rd==rs1), we just use the rd as rx in Bitty ISA
            #because both of them are the destination register

            if opcode in RiscVConverter.bitty_alu_instr:
                result.append((opcode, rd, rs2))
            else:
                if opcode == 'srl':
                    result.append(("shr",  rd, rs2))
                elif opcode == 'sll':
                    result.append(("shl",  rd, rs2))
                elif opcode == 'sra':
                    result.append(("shrs", rd, rs2)) # signed right shift -> should be implemented  
                elif opcode == 'slt' or opcode == 'sltu':
                    if opcode == 'slt':
                        result.append(("cmps", rd, rs2)) # signed comparison -> should be implemented
                    else:
                        result.append(("cmp",  rd, rs2))
                    # branch and set handling
                    result.append(("bie",  12, None)) # big assign_one -> 4th instr after this
                    result.append(("big",  10, None)) # big assign_one -> 3rd instr after this
                    result.append(("sub",  rd, rd)) 
                    result.append(("addi", rd, 1))
                    result.append(("cmpi", rd, 1))
                    result.append(("bie",  4,  None))
                    result.append(("sub",  rd, rd))

                #M instrucutions
                # elif opcode == 'mul':
                #     result.append(("mul", rd, rs2))
                # elif opcode == 'mulh':
                #     result.append(("mulh", rd, rs2))
                # elif opcode == 'mulhsu':
                #     result.append(("mulhsu", rd, rs2))
                # elif opcode == 'mulhu':
                #     result.append(("mulhu", rd, rs2))

                elif opcode == 'div':
                    rd_init = rd
                    if rd != rs1 and rd != rs2:
                        result.append(("sub", rd,   rd)) 
                    elif rd == rs1 and rd != rs2:
                        rd = 0b0000 # use x0 as rd

                    result.append(("cmp", rs2, 0))
                    result.append(("big", 10, None)) #not_zero
                    #to handle cases when rs2 = 0 -> res should be all F's
                    result.append(("sub", rd, rd)) 
                    result.append(("subi",  rd,  1))
                    result.append(("cmpsi", rd, -1))
                    result.append(("bie", 26, None)) 

                    #handle base cases
                    result.append(("cmp", rs1,  rs2)) #def not_zero
                    result.append(("bil", 70,   None)) #rs1 <  rs2 -> rd = 0 -> branch to the end
                    result.append(("bie", 66,   None)) #rs1 == rs2 -> rd = 1 -> branch to last instruction
                    
                    result.append(("cmps", rs1, 0)) #is rs1 positive or negative
                    result.append(("big", 8, None)) # to check rs2
                    result.append(("addi", rd, 1))
                    result.append(("xor", rs1, 0))
                    result.append(("addi", rs1, 1))
                    result.append(("cmp", rs2, 0)) # def check_rs2
                    result.append(("big", 8, None)) #to xor_check
                    result.append(("addi", rd, 1))
                    result.append(("xor", rs2, 0))
                    result.append(("addi", rs2, 1))
                    result.append(("cmpi", rd, 1)) # def xor_check
                    result.append(("bie", 4, None)) #to save_one
                    result.append(("st", 0, 2)) 
                    result.append(("st", rd, 2)) # def save_one: st rd R2
                    result.append(("sub", rd, rd))
                    result.append(("subi", 2, 4)) # R2 = R2 - 4
                    result.append(("st", rs1, 2)) # st rs1 R2
                    result.append(("addi", rd, 1)) # def div_loop:
                    result.append(("sub", rs1, rs2)) 
                    result.append(("cmp", rs1, rs2))
                    result.append(("big", -6, None)) # div_loop
                    result.append(("bie", -8, None)) # div_loop
                    result.append(("addi", 2, 4)) 
                    result.append(("ld", rs1, 2))
                    result.append(("cmp", rs1, 0)) 
                    result.append(("bie", 6, None)) 
                    result.append(("xor", rd, 0)) 
                    result.append(("addi", rd, 1))
                    result.append(("subi", 2, 4)) #def end
                    result.append(("ld", rs1, 2)) 
                    result.append(("addi", 2, 4)) # move stack pлointer back
                    result.append(("addi", rd, -1)) #to remove the effect of the last line
                    result.append(("addi", rd,  1)) #to handle cases when rs1 == rs2

                
                    if rd_init == rs1 and rd_init != rs2:
                        result.append(("sub", rs1, rs1))
                        result.append(("add", rs1, rd)) #rs1 == R0
                        result.append(("sub", rd, rd)) #rd == R0
                    elif rd_init == rs2 and rd_init != rs1:
                        result.append(("sub", rs2, rs2))
                        result.append(("add", rs2, rd)) #rs2 == R0
                        result.append(("sub", rd, rd)) #rd == R0

                elif opcode == 'divu':
                    rd_init = rd
                    if rd != rs1 and rd != rs2:
                        result.append(("sub", rd,   rd)) 
                    elif rd == rs1 and rd != rs2:
                        rd = 0b0000 # use x0 as rd
                    
                    result.append(("cmp", rs2, 0))
                    result.append(("big", 10, None)) #not_zero
                    #to handle cases when rs2 = 0 -> res should be all F's
                    result.append(("sub", rd, rd)) 
                    result.append(("subi", rd, 1))
                    result.append(("cmpsi", rd, -1))
                    result.append(("bie", 26, None)) 

                    result.append(("cmp", rs1,  rs2)) #def not_zero
                    result.append(("bil", 22,   None)) #rs1 <  rs2 -> rd = 0 -> branch to the end
                    result.append(("bie", 18,   None)) #rs1 == rs2 -> rd = 1 -> branch to last instruction
                    result.append(("st",  rs1,  2)) 

                    result.append(("addi",  rd, 1))  
                    result.append(("sub",  rs1, rs2))
                    result.append(("cmp",  rs1, rs2))
                    result.append(("big",  -6,  None))
                    result.append(("bie", 4, None))
                    result.append(("addi", rd, -1))
                    result.append(("ld",   rs1, 2))   
                    result.append(("addi", rd,  1))  

                    if rd_init == rs1 and rd_init != rs2:
                        result.append(("sub", rs1, rs1))
                        result.append(("add", rs1, rd)) #rs1 == R0
                        result.append(("sub", rd, rd)) #rd == R0
                    elif rd_init == rs2 and rd_init != rs1:
                        result.append(("sub", rs2, rs2))
                        result.append(("add", rs2, rd)) #rs2 == R0
                        result.append(("sub", rd, rd)) #rd == R0

                else:
                    return "unknown"
            if rd_is_R0:
                result.append(("sub", rs2, rs2))
                result.append(("add", rs2, rd))
                result.append(("sub", rd, rd)) #rd == R0
            
        #I type instruction binary to Bitty assembly conversion
        elif instr_type == "I":
            opcode    =     instr[0]
            rd        = int(instr[1])
            rs1       = int(instr[2])
            immediate = int(instr[3]) & 0xfff
            # Extract imm[11:6] (upper 6 bits)
            imm_upper = (immediate >> 6) & 0x3F  # 0x3F = 0b111111

            # Extract imm[5:3] (middle 3 bits)
            imm_mid = (immediate >> 3) & 0x7     # 0x7 = 0b111

            # Extract imm[2:0] (lower 3 bits)j
            imm_lower = immediate & 0x7          # 0x7 = 0b111

            
            #Handling the case when rd != rs1
            if rd == rs1:
                if opcode not in ["lb", "lh", "lw", "lbu", "lhu"]:
                    rd = 0b0000 # use x0 as rd
                    rd_is_R0 = True
                    #print("rd == rs1")
            #when rd != rs1
            else:
                result.append(("sub", rd, rd))

            if (opcode in RiscVConverter.bitty_alu_instr 
                 or opcode == "slti" or opcode == "sltiu"):
                print("opcode in RiscVConverter.bitty_alu_instr:", opcode)
                result.append(("addi", rd, imm_upper)) #addi rd, imm[11:6]
                result.append(("shli", rd, 3))
                result.append(("addi", rd, imm_mid)) #addi rd, imm[5:3]
                result.append(("shli", rd, 3))
                result.append(("addi", rd, imm_lower)) #addi rd, imm[2:0]
            #Handling shift instructions-> rd != rs1 case
            elif rd != rs1 and opcode in RiscVConverter.i_shift_instr.values():
                result.append(("sub",  rd, rd))
                result.append(("add",  rd, rs1))
                immediate = immediate & 0x1F # Mask to 5 bits for shift instructions
            #handling load instrucitons -> we ignore the offset 
            #also handle-> lw rd, offset(rs1)
            elif opcode_binary == 0b0000011: # Load instructions
                result.append(("ld", rd, rs1))

            #print("HERE 1")
            #Else (rd==rs1), we just use the rd as rx in Bitty ISA
            #because both of them are the destination register

            if opcode in RiscVConverter.bitty_alu_instr:
                result.append((opcode[:len(opcode)-1], rd, rs1))
            else:
                if opcode == 'slli':
                    result.append(("shli",  rd, immediate))
                elif opcode == 'srli':
                    result.append(("shri",  rd, immediate))
                elif opcode == 'srai':
                    result.append(("shrsi", rd, immediate))
                elif opcode == 'slti' or opcode == 'sltiu':
                    if opcode == 'slti':
                        result.append(("cmpsi", rd, rs1))
                    else:
                        result.append(("cmpi",  rd, rs1))
                    # branch and set handling
                    result.append(("bie",   12, None)) # big assign_one -> 4th instr after this
                    result.append(("bil",   10, None)) # big assign_one -> 3rd instr after this
                    result.append(("sub",   rd, rd))
                    result.append(("addi",  rd, 1))
                    result.append(("cmpi",  rd, 1))
                    result.append(("bie",   4,  None))
                    result.append(("sub",   rd, rd))
                #load instructions handler
                # i hope that accessing memory 
                # that is not %4==0 is not a problem
                elif opcode == 'lb': 
                    result.append(('ld', rd, rs1))
                    result.append(("shli",  rd, 24))
                    result.append(("shrsi", rd, 24))
                elif opcode == 'lh':
                    result.append(('ld', rd, rs1))
                    result.append(("shli",  rd, 16))
                    result.append(("shrsi", rd, 16))
                elif opcode == 'lbu':
                    result.append(('ld', rd, rs1))
                    result.append(("shli",  rd, 24))
                    result.append(("shri",  rd, 24))
                elif opcode == 'lhu':
                    result.append(('ld', rd, rs1))
                    result.append(("shli",  rd, 16))
                    result.append(("shri",  rd, 16))
                elif opcode == 'lw':
                    result.append(('ld', rd, rs1))
                else:
                    return "unknown"
            if rd_is_R0 == True:
                result.append(("sub", rs1, rs1))
                result.append(("add", rs1, rd))
                result.append(("sub", rd, rd))
            #print(result)
        elif instr_type == "B":
            opcode = instr[0]
            rs1    = int(instr[1])
            rs2    = int(instr[2])
            # grab low 12 bits
            imm12  = int(instr[3]) & 0xFFF
            # sign-extend 12-bit value to Python int
            if imm12 & 0x800:
                immediate = imm12 - 0x1000
            else:
                immediate = imm12
            
            

            if opcode == "beq":
                result.append(("cmps", rs1, rs2))

                result.append(("bie", immediate, None))
            elif opcode =="bge" or opcode == "bgeu":
                if opcode == "bge":
                    result.append(("cmps", rs1, rs2))
                else: 
                    result.append(("cmp", rs1, rs2))

                result.append(("big", immediate, None)) #0 and 1 will be masked to 0
                pc_key   = RiscVConverter.Bitty_PC + len(result) - 1
                pc_target = RiscVConverter.RISCV_PC + (immediate // 4)
                print("Branch PC:", pc_key + 1, "offset:", pc_target)
                RiscVConverter.branch_pc[pc_key] = pc_target
                
                result.append(("bie", immediate, None)) #0 and 1 will be masked to 0
            elif opcode == "bne":
                result.append(("cmps", rs1, rs2))

                result.append(("bil", immediate, None))
                pc_key   = RiscVConverter.Bitty_PC + len(result) - 1
                pc_target = RiscVConverter.RISCV_PC + (immediate // 4)
                print("Branch PC:", pc_key + 1, "offset:", pc_target)
                RiscVConverter.branch_pc[pc_key] = pc_target

                result.append(("big", immediate, None))
            elif opcode == "blt" or opcode == "bltu":
                if opcode == "blt":
                    result.append(("cmps", rs1, rs2))
                else: 
                    result.append(("cmp", rs1, rs2))
                    

                result.append(("bil", immediate, None))


            #to save the current pc value of branch instruction to use it for recalculation
            pc_key   = RiscVConverter.Bitty_PC + len(result) - 1
            # now immediate is signed, so offset calculation will be correct for backwards branches
            pc_target = RiscVConverter.RISCV_PC + (immediate // 4)
            print("Branch PC:", pc_key + 1, "offset:", pc_target)
            RiscVConverter.branch_pc[pc_key] = pc_target

        #U type instruction binary to Bitty assembly conversion
        elif instr_type == "U":
            opcode = instr[0]
            rd     = int(instr[1])
            immediate = int(instr[2]) & 0xFFFFFF # Mask to 20 bits
            # Extract the 6 upper bits (bits 19:14)
            upper_6 = (immediate >> 14) & 0x3F

            # Extract the next 5 bits (bits 13:9)
            next_5_1 = (immediate >> 9) & 0x1F

            # Extract the next 5 bits (bits 8:4)
            next_5_2 = (immediate >> 4) & 0x1F

            # Extract the last 4 bits (bits 3:0)
            last_4 = immediate & 0xF
            result.append(("sub", rd, rd))
            result.append(("addi", rd, upper_6))
            result.append(("shli", rd, 5))
            result.append(("addi", rd, next_5_1))
            result.append(("shli", rd, 5))
            result.append(("addi", rd, next_5_2))
            result.append(("shli", rd, 4))
            result.append(("addi", rd, last_4))
            result.append(("shli", rd, 12)) #fill the last 12 bits with 0s
            if opcode == "auipc":
                result.append(("gtpc", 0, None)) #get pc to R0
                result.append(("add", rd, 0)) #rd = pc + upper 20 bits
                result.append(("sub", 0, 0)) #make R0 = 0
        elif instr_type == "J":
            opcode = instr[0]
            rd     = int(instr[1])
            if opcode == "jal":
                immediate = int(instr[2]) & 0xFFFFFF
                # Extract imm[11:6] (upper 6 bits)
                imm_upper = (immediate >> 6) & 0x3F  # 0x3F = 0b111111

                # Extract imm[5:3] (middle 3 bits)
                imm_mid = (immediate >> 3) & 0x7     # 0x7 = 0b111

                # Extract imm[2:0] (lower 3 bits)j
                imm_lower = immediate & 0x7          # 0x7 = 0b111

                result.append(("gtpc", rd, None)) #get pc to rd
                result.append(("addi", rd, 4)) #rd = pc + 4
                result.append(("addi", 0, imm_upper))
                result.append(("shli", 0, 3))
                result.append(("addi", 0, imm_mid))
                result.append(("shli", 0, 3))
                result.append(("addi", 0, imm_lower))
                result.append(("add", 0, rd)) #R0 = pc + imm + 4
                result.append(("sub", 0, 4)) #R0 = pc + imm
                result.append(("stpc", 0, None)) #pc = R0 = pc + imm
                result.append(("sub", 0, 0)) #make R0 = 0
            elif opcode == "jalr":
                                # Extract imm[11:6] (upper 6 bits)
                imm_upper = (immediate >> 6) & 0x3F  # 0x3F = 0b111111

                # Extract imm[5:3] (middle 3 bits)
                imm_mid = (immediate >> 3) & 0x7     # 0x7 = 0b111

                # Extract imm[2:0] (lower 3 bits)j
                imm_lower = immediate & 0x7          # 0x7 = 0b111

                result.append(("gtpc", rd, None)) #get pc to rd
                result.append(("addi", rd, 4)) #rd = pc + 4
                result.append(("addi", 0, imm_upper))
                result.append(("shli", 0, 3))
                result.append(("addi", 0, imm_mid))
                result.append(("shli", 0, 3))
                result.append(("addi", 0, imm_lower))
                result.append(("add", 0, rs1)) #R0 = imm + rs1
                result.append(("stpc", 0, None)) #pc = R0 = imm + rs1
                result.append(("sub", 0, 0)) #make R0 = 0
                
            else:
                rs1 = int(instr[2])
                # Extract the 12-bit immediate value from the instruction
                immediate = int(instr[3]) & 0xFFF    
        elif instr_type == "S":
            opcode = instr[0]
            rs1    = int(instr[1])
            rs2     = int(instr[2])
            immediate = int(instr[3]) & 0xFFF

            #need to be implemented everywhere
            result.append(("add",   0, rs2)) #R0 = rs2

            #load instructions handler
            if opcode == 'sb':
                result.append(("shli",  0, 24))  
                result.append(("shrsi", 0, 24)) 
            elif opcode == 'sh':
                result.append(("shli",  0, 16))
                result.append(("shrsi", 0, 16))
            elif opcode == 'sw':
                print("everything is up to date")
            else:
                return "unknown"
            #need to be implemented everywhere
            result.append(("st",    0, rs1)) #mem[rs1] = rs2
            result.append(("sub",   0, 0)) #make R0 = 0

        RiscVConverter.map_pc[RiscVConverter.RISCV_PC] = RiscVConverter.Bitty_PC
        RiscVConverter.RISCV_PC += 1
        RiscVConverter.Bitty_PC += len(result)
        print(result)
        #add assembly instructions to the list of instructions
        RiscVConverter.instr_of_bitty_assembly.extend(result)
        return result

    @staticmethod
    def bitty_to_binary(instr):

        opcode, rx, ry = instr

        mapping_value = RiscVConverter.bitty_alu_instr.get(opcode)
        if mapping_value is None:
            raise KeyError(f"Opcode {opcode} not found in bitty_alu_instr mapping.")
        operation, fmt = mapping_value

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
            instruction |= (operation & 0b1111) << 2

            # Place format in bits [1:0]
            instruction |= (fmt & 0b11)
        elif fmt == 1:
            immid = ry
            # Place rx at bits [15:12]
            instruction |= (rx & 0xF) << 12
            # Place immid at bits [11:6]
            instruction |= (immid & 0x3F) << 6
            # Place alu at bits [5:2]
            instruction |= (operation & 0xF) << 2
            # Place format at bits [1:0]
            instruction |= (fmt & 0x3)
        elif fmt == 2:
            cond = operation

            if cond < 3:
                immid = rx

                # Place immid in bits [15:4]
                instruction |= (immid & 0xFFF) << 4  # mask immid to 12 bits
            else:
                #set bits [15:12] to rx and rest are zeros
                instruction |= (rx & 0xF) << 5

            # Place cond in bits [3:2]
            instruction |= (cond) << 2    # mask cond to 2 bits

            # Place the fixed pattern 0b10 in bits [1:0]
            instruction |= 0b10  # decimal 2, binary 10
        elif fmt == 3:
            # We'll assume you have variables:
            #   rx (4-bit), ry (4-bit), reserved (5-bit), ls (1-bit)
            # that you want to place into this instruction.
            reserved = 0
            instruction = 0

            # Place rx in bits [15:12]
            instruction |= (rx & 0xF) << 12

            # Place ry in bits [11:8]
            instruction |= (ry & 0xF) << 8

            # Place reserved in bits [7:3]
            instruction |= (reserved & 0x1F) << 3

            # Place L/S in bit [2]
            instruction |= (operation & 0x1) << 2

            # Place the fixed pattern 0b11 in bits [1:0]
            instruction |= 0b11
            #print("Bitty instruction:", format(instruction, '04X'))



            #print(final_instructions)
        
        return instruction
    
    @staticmethod
    def translator(init_instr):
        # Increment the program counter each time this method is called

        instructions = RiscVConverter.riscV_to_bitty(init_instr)
        print("Bitty to binary START")
        final_instructions = []
        for instr in instructions:
            instruction = RiscVConverter.bitty_to_binary(instr)
            final_instructions.append(instruction)
            #append the instruction to the list of instructionsS
            RiscVConverter.instr_of_bitty_binary.append(instruction)
        
        return final_instructions
        
    
    def print_map(out_filename="pc_map_output.txt"):
        with open(out_filename, "w") as f:

            for pc, bitty_pc in RiscVConverter.map_pc.items():
                line = f"{bitty_pc}"
                print(line)
                f.write(line + "\n")

