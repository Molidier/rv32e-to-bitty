import random

def reg5(n):
    """Return a 5-bit binary string for register number n (0–31)."""
    return format(n % 32, '05b')

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

def generate_instruction_i(op, rd, rs1, imm):
    """
    Generate a 32-bit I-type instruction literal as a binary string with underscores.
    
    For I-type instructions, the format is:
      imm[11:0] | rs1 | funct3 | rd | opcode
      
    Supported instructions in RISCV32EM:
      - ALU immediate (non-shift): addi, slti, sltiu, xori, ori, andi (opcode = 0010011)
      - Shift immediate: slli, srli, srai (opcode = 0010011)
        For these, the 12-bit immediate is split:
          imm[11:5] (7 bits) is funct7,
          imm[4:0] (5 bits) is the shift amount.
      - Load instructions: lb, lh, lw, lbu, lhu (opcode = 0000011)
    """
    # Ensure imm is within 12 bits for non-shift instructions
    imm &= 0xfff

    # ALU immediate instructions (non-shift), opcode 0010011.
    if op in ["addi", "slti", "sltiu", "xori", "ori", "andi"]:
        opcode = "0010011"
        if op == "addi":
            funct3 = "000"
        elif op == "slti":
            funct3 = "010"
        elif op == "sltiu":
            funct3 = "011"
        elif op == "xori":
            funct3 = "100"
        elif op == "ori":
            funct3 = "110"
        elif op == "andi":
            funct3 = "111"
        # Format immediate as a 12-bit binary string.
        imm_str = format(imm, '012b')
    
    # Shift immediate instructions, opcode 0010011.
    elif op in ["slli", "srli", "srai"]:
        opcode = "0010011"
        # For shift instructions:
        # - Extract shamt (shift amount): the lower 5 bits of immediate
        # - Set funct7: the upper 7 bits based on instruction type
        shamt = imm & 0x1F  # Extract lower 5 bits for shift amount
        
        if op == "slli":
            funct3 = "001"
            funct7 = "0000000"  # slli uses 0000000 as funct7
        elif op == "srli":
            funct3 = "101"
            funct7 = "0000000"  # srli uses 0000000 as funct7
        elif op == "srai":
            funct3 = "101"
            funct7 = "0100000"  # srai uses 0100000 as funct7
        
        # Build immediate string: funct7 + shamt
        imm_str = funct7 + "_" + format(shamt, '05b')
    
    # Load instructions, opcode 0000011.
    elif op in ["lb", "lh", "lw", "lbu", "lhu"]:
        opcode = "0000011"
        if op == "lb":
            funct3 = "000"
        elif op == "lh":
            funct3 = "001"
        elif op == "lw":
            funct3 = "010"
        elif op == "lbu":
            funct3 = "100"
        elif op == "lhu":
            funct3 = "101"
        # Full 12-bit immediate.
        imm_str = format(imm, '012b')
    
    else:
        raise ValueError("Operation not supported for I-type")
    
    # Build the instruction: imm, rs1, funct3, rd, opcode.
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
    "lb", "lh", "lw", "lbu", "lhu"
]

def generate(number_of_r_instr = 0, number_of_i_instr = 0, number_of_u_instr = 0):

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
        op = i_operations[13]
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


instructions = []
generate(number_of_r_instr=5)

# Save the generated instructions to a file
with open("riscv_instructions.txt", "w") as outfile:
    for instr in instructions:
        outfile.write(instr + "\n")

