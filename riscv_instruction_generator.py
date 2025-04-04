def reg5(n):
    """Return a 5-bit binary string for register number n (0–31)."""
    return format(n % 32, '05b')

def generate_instruction(op, rd, rs1, rs2):
    """
    Generate a 32-bit instruction literal as a binary string with underscores,
    given the operation (a string: 'add', 'sub', 'srl', or 'sll') and registers.
    
    The encoding is as follows:
      - funct7 (7 bits): for ADD, SLL, SRL = "0000000"; for SUB = "0100000"
      - rs2 (5 bits): source register 2
      - rs1 (5 bits): source register 1
      - funct3 (3 bits): for ADD/SUB = "000", for SLL = "001", for SRL = "101"
      - rd   (5 bits): destination register
      - opcode (7 bits): "0110011"
    """
    opcode = "0110011"
    if op == "add":
        funct7 = "0000000"
        funct3 = "000"
    elif op == "sub":
        funct7 = "0100000"
        funct3 = "000"
    elif op == "srl":
        funct7 = "0000000"
        funct3 = "101"
    elif op == "sll":
        funct7 = "0000000"
        funct3 = "001"
    else:
        raise ValueError("Operation not supported")
    
    # Build the instruction using underscore separators between fields.
    # Order: funct7, rs2, rs1, funct3, rd, opcode
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

# Allowed operations.
#operations = ["add", "sub", "srl", "sll"]
operations = ["add"]


# Generate 50 instructions.
instructions = []
for i in range(30):
    op = operations[i % 4]  # Cycle through the operations.
    rd = i % 16           # Destination register (x0 to x15).
    if rd==0:
        rd = 1
    rs1 = (i + 1) % 16    # Source register 1.
    rs2 = (i + 2) % 16    # Source register 2.
    instr_bin = generate_instruction(op, rd, rs1, rs2)
    instructions.append(instr_bin)

# Save the generated instructions to the file "riscv_instructions.txt".
with open("riscv_instructions.txt", "w") as outfile:
    for instr in instructions:
        outfile.write(instr + "\n")

print("50 instructions have been generated and saved to riscv_instructions.txt")
