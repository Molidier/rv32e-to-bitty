# EmulatorComparison.py
from Bitty_test.BittyEmulator import BittyEmulator
from Bitty_test.RISCV32EMEmulator import RISCV32EMEmulator
from Bitty_test.shared_memory import generate_shared_memory  # Import shared memory generator
from run_parralel import EmulatorComparison

def load_instructions_from_file(filename, base=0):
    """
    Reads instructions from a text file, one per line.
    If base is 0, int() will auto-detect the base from the prefix.
    """
    instructions = []
    try:
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue
                try:
                    instructions.append(int(line, base))
                except ValueError as e:
                    print(f"Error converting line '{line}': {e}")
    except FileNotFoundError:
        print(f"Warning: File {filename} not found.")
    return instructions


def write_to_file(message, filename="comparison_output.txt", mode="a"):
    """
    Write a message to the output file.
    """
    with open(filename, mode) as file:
        file.write(message + "\n")


def run_riscv(riscv, instructions, max_instructions=1000):
    riscv.instruction_array = instructions
    riscv.pc = 0
    count = 0
    while count < max_instructions and riscv.pc < len(riscv.instruction_array):
        instr = riscv.fetch_instruction()
        riscv.pc = riscv.decode_and_execute(instr)
        count += 1
    return count


def run_bitty(bitty, instructions):
    bitty.pc = 0
    return bitty.evaluate_instructions_array(instructions)


def main():
    #to get the the PC mapping of RV to Bitty
    comparer = EmulatorComparison(max_instr=1000,
                                  output_file="comparison_output.txt")
    comparer.run()


    map_pc = comparer.run_parallel
    

    # Reset output
    write_to_file("=== Emulator Comparison ===", mode="w")

    # Generate two independent memory arrays
    mem_riscv = generate_shared_memory()
    mem_bitty = generate_shared_memory()

    # Instantiate emulators on their own memories
    riscv = RISCV32EMEmulator(memory_array=mem_riscv)
    bitty = BittyEmulator(memory=mem_bitty)

    # 1. Load & run RISC-V
    rv_insts = load_instructions_from_file("riscv_instructions.txt", base=0)
    write_to_file(f"\n-- Running RISC-V [{len(rv_insts)} instructions] --")
    rv_count = run_riscv(riscv, rv_insts)
    write_to_file(f"RISC-V executed {rv_count} instructions")

    # 2. Load & run Bitty
    bt_insts = load_instructions_from_file("bitty_binary.txt", base=0)
    write_to_file(f"\n-- Running Bitty [{len(bt_insts)} instructions] --")
    bt_count = run_bitty(bitty, bt_insts)
    write_to_file(f"Bitty executed {bt_count} instructions")

    # 3. Compare registers
    write_to_file("\n-- Register Comparison --")
    write_to_file(f"{'Reg':<6}{'RISC-V':^12}{'Bitty':^12}{'Match':^8}")
    write_to_file("-"*40)
    # assume both have 16 regs; adjust if needed
    for reg in range(len(riscv.registers)):
        rv_val = riscv.registers[reg] & 0xFFFFFFFF
        bt_val = bitty.registers[reg] & 0xFFFFFFFF
        match = "✓" if rv_val == bt_val else "✗"
        write_to_file(f"x{reg:<5} 0x{rv_val:08X}  0x{bt_val:08X}   {match}")

    # 4. Compare full memory
    write_to_file("\n-- Memory Comparison --")
    write_to_file(f"{'Addr':<6}{'RISC-V':^12}{'Bitty':^12}{'Match':^8}")
    write_to_file("-"*40)
    # compare entire memory array (or limit to a range of interest)
    for addr in range(len(mem_riscv)):
        rv_word = mem_riscv[addr] & 0xFFFFFFFF
        bt_word = mem_bitty[addr] & 0xFFFFFFFF
        if rv_word != bt_word:
            m = "✗"
        else:
            m = "✓"
        write_to_file(f"{addr:<6} 0x{rv_word:08X}  0x{bt_word:08X}   {m}")

    write_to_file("\n=== Comparison Complete ===")
    write_to_file(f"RISC-V ran {rv_count} instrs; Bitty ran {bt_count} instrs")


if __name__ == "__main__":
    main()
