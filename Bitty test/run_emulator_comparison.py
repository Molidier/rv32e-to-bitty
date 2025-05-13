"""
run_emulator_comparison.py - Script to run the emulator comparison with proper error handling
"""
import os
import sys

def check_file_exists(filename):
    """Check if a file exists and print informative message"""
    if not os.path.exists(filename):
        print(f"ERROR: Required file '{filename}' not found!")
        return False
    return True

def main():
    """Main function to run the emulator comparison with proper error handling"""
    print("Emulator Comparison Tool")
    print("=======================")
    
    # Check required files
    required_files = [
        "RISCV32EMEmulator.py",
        "BittyEmulator.py",
        "shared_memory.py",
        "EmulatorComparison.py",
        "riscv_instructions.txt",
        "bitty_binary.txt"
    ]
    
    missing_files = False
    for filename in required_files:
        if not check_file_exists(filename):
            missing_files = True
    
    if missing_files:
        print("\nSome required files are missing. Please ensure all files are present.")
        print("Required files:")
        for filename in required_files:
            status = "✓" if os.path.exists(filename) else "✗"
            print(f"  {status} {filename}")
        return 1
    
    # All required files exist, run the comparison
    print("\nRunning emulator comparison...")
    try:
        from EmulatorComparison import main as run_comparison
        run_comparison()
        print("\nComparison completed successfully!")
        print("Results saved to 'comparison_output.txt'")
        return 0
    except Exception as e:
        print(f"\nError during comparison: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())