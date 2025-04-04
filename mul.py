def mulh(rs1: int, rs2: int) -> int:
    # Extract 16-bit halves
    rs1_lo = rs1 & 0xFFFF  # Lower 16 bits of rs1
    rs1_hi = rs1 >> 16      # Upper 16 bits of rs1
    rs2_lo = rs2 & 0xFFFF  # Lower 16 bits of rs2
    rs2_hi = rs2 >> 16      # Upper 16 bits of rs2

    # Perform 16-bit multiplications
    low_low = rs1_lo * rs2_lo  # Least significant part
    low_high = rs1_lo * rs2_hi # Middle part
    high_low = rs1_hi * rs2_lo # Middle part
    high_high = rs1_hi * rs2_hi # Most significant part

    # Compute the carry
    carry = ((low_low >> 16) + (low_high & 0xFFFF) + (high_low & 0xFFFF)) >> 16
    
    # Compute high 32 bits of the result
    high = high_high + (low_high >> 16) + (high_low >> 16) + carry
    
    return high

def reference_high_32_bits(rs1, rs2):
    product = rs1 * rs2
    return (product >> 32) & 0xFFFFFFFF

def test_mulh():
    test_cases = [
        (0, 0),
        (1, 1),
        (0xFFFFFFFF, 0xFFFFFFFF),
        (0x00010000, 0x00010000),
        (0xFFFFFFFF, 1),
        (1, 0xFFFFFFFF),
        (3000000000, 4000000000),
        (123456789, 987654321),
    ]

    for rs1, rs2 in test_cases:
        expected = reference_high_32_bits(rs1, rs2)
        result = mulh(rs1, rs2)
        assert result == expected, f"Failed: mulh({rs1}, {rs2}) = {result}, expected {expected}"
        print(f"Passed: mulh({rs1}, {rs2}) = {result}")


# Example usage
rs1 = 3000000000  # Example large numbers
rs2 = 4000000000
result = mulh(rs1, rs2)
print(f"High 32 bits of product: {result}")
test_mulh()
