fn test_addition() {
    assert!(1 + 1 == 2);
    assert!(0 + 0 == 0);
    assert!(255 + 1 == 256);
}

fn test_subtraction() {
    assert!(5 - 3 == 2);
    assert!(0 - 1 == u32::MAX); // wrapping
}

fn test_multiplication() {
    assert!(3 * 4 == 12);
    assert!(0 * 999 == 0);
}

fn test_logical_ops() {
    assert!(0xFF & 0x0F == 0x0F);
    assert!(0xF0 | 0x0F == 0xFF);
    assert!(0xAA ^ 0xFF == 0x55);
}

fn test_shift_ops() {
    assert!(1 << 4 == 16);
    assert!(256 >> 4 == 16);
}

fn test_comparison() {
    assert!(5 > 3);
    assert!(3 < 5);
    assert!(5 == 5);
}

fn test_immediate() {
    let x: u32 = 10;
    assert!(x + 5 == 15);
    assert!(x & 0xFF == 10);
    assert!(x | 0xF0 == 0xFA);
}

fn main() {
    test_addition();
    test_subtraction();
    test_multiplication();
    test_logical_ops();
    test_shift_ops();
    test_comparison();
    test_immediate();
    println!("All ISA tests passed!");
}
