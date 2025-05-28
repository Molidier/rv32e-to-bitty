import random

def reg5(n):
    """Return a 5-bit binary string for register number n (0–31)."""
    return format(n % 32, '05b')

def generate_instruction_s(op, rs2, rs1, imm):
    """
    Generate a 32-bit S-type instruction literal as a binary string with underscores.
    Format: imm[11:5] | rs2 | rs1 | funct3 | imm[4:0] | opcode (0100011)
    Supported ops: sb, sh, sw
    """
    opcode = "0100011"
    # mask to 12 bits
    imm12 = imm & 0xfff
    imm_str = format(imm12, '012b')
    imm_hi = imm_str[:7]   # bits 11:5
    imm_lo = imm_str[7:]   # bits 4:0

    if op == "sb":
        funct3 = "000"
    elif op == "sh":
        funct3 = "001"
    elif op == "sw":
        funct3 = "010"
    else:
        raise ValueError(f"Operation {op} not supported for S-type")

    instruction = (
        "0b" +
        imm_hi + "_" +
        reg5(rs2) + "_" +
        reg5(rs1) + "_" +
        funct3 + "_" +
        imm_lo + "_" +
        opcode
    )
    return instruction


def generate_instruction(op, rd, rs1, rs2):
    """
    Generate a 32-bit R-type instruction literal as a binary string with underscores,
    given the operation (e.g., 'add', 'sub', etc.) and registers.
    Encoding: funct7 | rs2 | rs1 | funct3 | rd | opcode (0110011)
    """
    opcode = "0110011"
    if op == "add":
        funct7 = "0000000"
        funct3 = "000"
    elif op == "sub":
        funct7 = "0100000"
        funct3 = "000"
    elif op == "sll":
        funct7 = "0000000"
        funct3 = "001"
    elif op == "srl":
        funct7 = "0000000"
        funct3 = "101"
    elif op == "sra":
        funct7 = "0100000"
        funct3 = "101"
    elif op == "slt":
        funct7 = "0000000"
        funct3 = "010"
    elif op == "sltu":
        funct7 = "0000000"
        funct3 = "011"
    
    # M-extension
    elif op == "mul":
        funct7, funct3 = "0000001", "000"
    elif op == "mulh":
        funct7, funct3 = "0000001", "001"
    elif op == "mulhsu":
        funct7, funct3 = "0000001", "010"
    elif op == "mulhu":
        funct7, funct3 = "0000001", "011"
    elif op == "div":
        funct7, funct3 = "0000001", "100"
    elif op == "divu":
        funct7, funct3 = "0000001", "101"
    elif op == "rem":
        funct7, funct3 = "0000001", "110"
    elif op == "remu":
        funct7, funct3 = "0000001", "111"

    else:
        raise ValueError("Operation not supported for R-type")
    
    # Build the instruction: funct7, rs2, rs1, funct3, rd, opcode.
    instruction = (
        "0b" +
        funct7 + "_" +
        reg5(rs2) + "_" +
        reg5(rs1) + "_" +
        funct3 + "_" +
        reg5(rd) + "_" +
        opcode
    )
    return instruction

# I-type generator, extended to support JALR
def generate_instruction_i(op, rd, rs1, imm):
    # Ensure imm is within 12 bits
    imm12 = imm & 0xfff
    imm_str = format(imm12, '012b')

    if op in ["addi", "slti", "sltiu", "xori", "ori", "andi"]:
        opcode = "0010011"
        funct3_map = {"addi":"000","slti":"010","sltiu":"011",
                      "xori":"100","ori":"110","andi":"111"}
        funct3 = funct3_map[op]

    elif op in ["slli", "srli", "srai"]:
        opcode = "0010011"
        shamt = imm & 0x1F
        if op == "slli": funct3, funct7 = "001", "0000000"
        elif op == "srli": funct3, funct7 = "101", "0000000"
        else:           funct3, funct7 = "101", "0100000"
        imm_str = funct7 + format(shamt, '05b')

    elif op in ["lb","lh","lw","lbu","lhu"]:
        opcode = "0000011"
        funct3_map = {"lb":"000","lh":"001","lw":"010",
                      "lbu":"100","lhu":"101"}
        funct3 = funct3_map[op]

    elif op == "jalr":
        # JALR: opcode=1100111, funct3=000, target = rs1 + imm
        opcode = "1100111"
        funct3 = "000"
        # format imm and register fields as for I-type

    else:
        raise ValueError(f"Unsupported I-type op: {op}")

    instruction = (
        "0b" +
        imm_str + "_" +
        reg5(rs1) + "_" +
        funct3 + "_" +
        reg5(rd) + "_" +
        opcode
    )
    return instruction

def generate_instruction_u(op, rd, imm):
    """
    Generate a 32-bit U-type instruction literal as a binary string with underscores.
    
    For U-type instructions, the format is:
      imm[31:12] | rd | opcode (LUI: 0110111, AUIPC: 0010111)
    
    Supported instructions in RISCV32EM:
      - LUI: Load Upper Immediate (opcode = 0110111)
      - AUIPC: Add Upper Immediate to PC (opcode = 0010111)
    """
    # Ensure imm is within 20 bits for U-type instructions
    imm &= 0xFFFFF

    # U-type instructions
    if op == "lui":
        opcode = "0110111"
    elif op == "auipc":
        opcode = "0010111"
    else:
        raise ValueError("Operation not supported for U-type")
    
    # Build the instruction: imm[31:12], rd, opcode
    imm_str = format(imm, '020b')  # Convert immediate to 20-bit binary string

    instruction = (
        "0b" +
        imm_str + "_" +         # immediate[31:12] (20 bits)
        reg5(rd) + "_" +        # rd (destination register)
        opcode                  # opcode (LUI or AUIPC)
    )
    return instruction
# J-type generator for JAL
def generate_instruction_j(op, rd, imm):
    if op != 'jal':
        raise ValueError(f"Unsupported J-type op: {op}")
    opcode = '1101111'
    # 20-bit immediate for J-type
    imm20 = imm & 0xFFFFF
    bin20 = format(imm20, '020b')  # imm[19]...imm[0]
    # J-format splits: imm[20]=bit19, imm[10:1]=bits9-18, imm[11]=bit8, imm[19:12]=bits0-7
    i20 = bin20[0]               # imm[19]
    i10_1 = bin20[10:20]         # imm[9:0]
    i11 = bin20[9]               # imm[10]
    i19_12 = bin20[1:9]          # imm[18:11]
    instruction = (
        "0b" +
        i20 + "_" + i10_1 + "_" + i11 + "_" + i19_12 + "_" +
        reg5(rd) + "_" + opcode
    )
    return instruction


# Updated list of R-type operations to include M-extension:
r_operations = [
    "add", "sub", "sll", "srl", "sra", "slt", "sltu",
    "mul", "mulh", "mulhsu", "mulhu", "div", "divu", "rem", "remu"
]
# Allowed I-type operations.
i_operations = [
    # ALU immediate (non-shift)
    "addi", "slti", "sltiu", "xori", "ori", "andi",
    # Shift immediate
    "slli", "srli", "srai",
    # Loads
    "lb", "lh", "lw", "lbu", "lhu", "jalr",
]

# add S-type ops
s_operations = ["sb", "sh", "sw"]

def generate(number_of_r_instr = 0, number_of_i_instr = 0, number_of_s_instr = 0, number_of_u_instr = 0, number_of_j_instr = 0):

    # Generate R-type instructions.
    r_instructions = []

    for i in range(number_of_r_instr):
        op = "add"
        #op = r_operations[random.randint(0, len(r_operations)-1)]
        rd = random.randint(3, 15)  # Destination register (avoiding x0, x1, x2)
        rs1 = random.randint(3, 15)
        rs2 = random.randint(3, 15)
        instr_bin = generate_instruction(op, rd, rs1, rs2)
        r_instructions.append(instr_bin)
        instructions.append(instr_bin)

    # Generate I-type instructions.
    i_instructions = []
    for i in range(number_of_i_instr):
        # Use all I-type operations, not just the first one
        #op = i_operations[random.randint(0, len(i_operations)-1)]
        op = i_operations[14]
        rd = random.randint(3, 15)  # Destination register (avoiding x0, x1, x2)

        rs1 = random.randint(0, 15)
        
        # Generate a random immediate within 12 bits
        if op in ["lb", "lh", "lw", "lbu", "lhu"]:
            # For load instructions, immediate is 12 bits
            imm = 0x000
        else:
            imm = random.randint(0, 0xfff)
        instr_bin = generate_instruction_i(op, rd, rs1, imm)
        i_instructions.append(instr_bin)
        instructions.append(instr_bin)

    u_operations = ["lui", "auipc"]

    u_instructions = []
    for i in range(number_of_u_instr):
        #op = random.choice(u_operations)
        op = u_operations[1]
        rd = random.randint(3, 15)  # Destination register (avoiding x0, x1, x2)

        imm = random.randint(0, 0xFFFFF)  # Random 20-bit immediate for U-type
        instr_bin = generate_instruction_u(op, rd, imm)
        u_instructions.append(instr_bin)
        instructions.append(instr_bin)
    
        # S-type (store)
    for _ in range(number_of_s_instr):
        op  = random.choice(s_operations)
        rs1 = random.randint(0, 15)   # base register
        rs2 = random.randint(3, 15)   # source register to store
        imm = random.randint(0, 0xfff)
        instructions.append(generate_instruction_s(op, rs2, rs1, imm))
    
    # Generate J-type (jal)
    for _ in range(number_of_j_instr):
        rd = random.randint(1, 15)        # typically x1..x15 (avoid x0 if you need link)
        imm = random.randint(-0x80000, 0x7FFFF)  # +-1 MiB range in halfwords
        instr = generate_instruction_j('jal', rd, imm)
        instructions.append(instr)

    # Add jalr examples
    # e.g., jalr x1,0(x5)
    instr = generate_instruction_i('jalr', rd=1, rs1=5, imm=0)
    instructions.append(instr)


instructions = []
generate(number_of_i_instr = 5, number_of_j_instr=5)

# Save the generated instructions to a file
with open("riscv_instructions.txt", "w") as outfile:
    for instr in instructions:
        outfile.write(instr + "\n")

# +4 -> stack pointer

# +4 -> orig code
# -4 -> value
# +4 -> bitty buffer 

# reg2 -> addr: 20 -> orig code
# 24 -> orig
# -4 -> 20 -> get value 

# SP -> reg2 -> 

# x0 -> addr: 150 -> custom SP ->

#buffer -> можно ли ограничить память ->  <2^32

#ошибка -> script -> ld/st -> mem[rs1] -> value of ther rs1
