from BittyEmulator import BittyEmulator
from RISCV32EMEmulator import RISCV32EMEmulator
from translator import RiscVConverter
from shared_memory import generate_shared_memory  # Import shared memory generator

class EmulatorComparison:
    def __init__(self, max_instr=100, output_file="comparison_output.txt"):
        # Configuration
        self.max_instr = max_instr
        self.output_file = output_file

        # Shared memory for both emulators
        self.memory = generate_shared_memory()

        # Initialize emulators
        self.bitty = BittyEmulator(memory=self.memory)
        self.riscv = RISCV32EMEmulator(memory_array=self.memory)
        self.translator = RiscVConverter()

        # Expose translator's map_pc via run_parallel reference
        self.run_parallel = self.translator.map_pc

        # 1:1 register mapping (RV x0–x15 to Bitty regs)
        self.register_map = {i: i for i in range(16)}

    def load_instructions_from_file(self, filename, base=0):
        instructions = []
        try:
            with open(filename, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    try:
                        instructions.append(int(line, base))
                    except ValueError as e:
                        print(f"Error converting line '{line}': {e}")
        except FileNotFoundError:
            print(f"Warning: File {filename} not found. Using sample instructions.")
            if "riscv" in filename.lower():
                instructions = [0x003100B3]  # sample ADD x1, x2, x3
        return instructions

    def write_to_file(self, message):
        with open(self.output_file, "a") as f:
            f.write(message + "\n")

    def run(self):
        # Clear output file
        with open(self.output_file, "w") as f:
            f.write("=== Starting Emulator Comparison ===\n")

        # Load instructions
        self.riscv.instruction_array = self.load_instructions_from_file(
            "riscv_instructions.txt", base=0
        )

        riscv_count = 0
        bitty_count = 0

        # Main comparison loop
        while (
            riscv_count < self.max_instr and
            self.riscv.pc < len(self.riscv.instruction_array)
        ):
            self.write_to_file(f"\n=== RISC-V Instr {riscv_count} @ PC {self.riscv.pc} ===")

            instr = self.riscv.fetch_instruction()
            self.write_to_file(f"Instruction: 0x{instr:08X}")
            self.riscv.pc = self.riscv.decode_and_execute(instr)
            riscv_count += 1

            # Translate and execute in Bitty
            try:
                bitty_bins = self.translator.translator(instr)
            except Exception as e:
                self.write_to_file(f"Error in translation: {e}")
                bitty_bins = []

            self.write_to_file(f"--- Executing {len(bitty_bins)} Bitty Instrs ---")
            for idx, b in enumerate(bitty_bins):
                self.write_to_file(f"Bitty #{idx}: 0x{b:04X}")

            if bitty_bins:
                self.bitty.pc = 0
                end_pc = self.bitty.evaluate_instructions_array(bitty_bins, riscv_count)
                if end_pc != len(bitty_bins):
                    self.write_to_file(f"Branch taken in Bitty, ended at PC {end_pc}")
                bitty_count += len(bitty_bins)

            # Register comparison
            self.write_to_file("\n=== Register Comparison ===")
            self.write_to_file(f"{'Reg':<6}{'RISC-V':<12}{'Bitty':<12}{'Match'}")
            self.write_to_file("-" * 40)
            for rv_reg, bt_reg in self.register_map.items():
                rv_val = self.riscv.registers[rv_reg] & 0xFFFFFFFF
                bt_val = self.bitty.registers[bt_reg] & 0xFFFFFFFF
                ok = '✓' if rv_val == bt_val else '✗'
                self.write_to_file(f"x{rv_reg:<5}0x{rv_val:08X}  0x{bt_val:08X}   {ok}")

            # Increment static PC tracker
            BittyEmulator.STATIC_PC_VALUE += 1
            self.write_to_file(f"STATIC_PC_VALUE -> {BittyEmulator.STATIC_PC_VALUE}")

        # Final summary
        self.write_to_file("\n=== Comparison Complete ===")
        self.write_to_file(f"RISC-V instrs: {riscv_count}, Bitty instrs: {bitty_count}")
        self.write_to_file(f"Final STATIC_PC_VALUE: {BittyEmulator.STATIC_PC_VALUE}")

        # Dump translator internals via class methods (avoid passing 'self')
        RiscVConverter.print_map()
        RiscVConverter.change_branch_offsets()
        RiscVConverter.print_assembly()
        RiscVConverter.print_binary()


if __name__ == "__main__":
    comparer = EmulatorComparison(max_instr=100)
    print("map_pc before run:", comparer.run_parallel)
    comparer.run()
    print("map_pc after run:", comparer.run_parallel)
