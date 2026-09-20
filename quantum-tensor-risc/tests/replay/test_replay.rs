// Copyright © 2026 SnapKitty Collective and contributors.
//
// This file is part of a work licensed under the
// SnapKitty Strong Network Copyleft License Version 1.0 (SSNCL-1.0).
//
// You may use, study, modify, copy, and redistribute this work
// only under the terms of SSNCL-1.0.
//
// A copy of SSNCL-1.0 must accompany this work.

fn test_replay_deterministic() {
    // PO10: ReplayDeterministic — same seed -> same behavior
    let seed1 = qrng::QRNGState::qseed(0xDEADBEEF, 0);
    let seed2 = qrng::QRNGState::qseed(0xDEADBEEF, 0);
    assert_eq!(seed1, seed2);
}

fn test_replay_different_entropy() {
    let seed1 = qrng::QRNGState::qseed(0xAAAAAAAA, 0);
    let seed2 = qrng::QRNGState::qseed(0xBBBBBBBB, 0);
    assert_ne!(seed1, seed2);
}

fn test_replay_different_epoch() {
    let seed1 = qrng::QRNGState::qseed(0xDEADBEEF, 0);
    let seed2 = qrng::QRNGState::qseed(0xDEADBEEF, 1);
    assert_ne!(seed1, seed2);
}

fn test_fluctuation_sample_deterministic() {
    let s1 = qrng::QRNGState::fluctuation_sample(42, 7);
    let s2 = qrng::QRNGState::fluctuation_sample(42, 7);
    assert_eq!(s1, s2);
}

fn test_fluctuation_sample_varies() {
    let s1 = qrng::QRNGState::fluctuation_sample(42, 0);
    let s2 = qrng::QRNGState::fluctuation_sample(42, 1);
    assert_ne!(s1, s2);
}

fn test_qrng_read_refill() {
    let mut qrng = qrng::QRNGState::new(42);
    let w1 = qrng.read();
    let w2 = qrng.read();
    assert_ne!(w1, 0); // Should generate something
    assert_ne!(w2, 0);
}

fn test_qrng_push_read() {
    let mut qrng = qrng::QRNGState::new(0);
    qrng.push(0xCAFEBABE);
    let w = qrng.read();
    assert_eq!(w, 0xCAFEBABE);
}

fn test_domain_separation() {
    // QSEED includes DOMAIN, PROC_ID, PROG_HASH, TENSOR_SHAPE
    let seed = qrng::QRNGState::qseed(0, 0);
    assert!(seed != 0); // Non-trivial
}

fn main() {
    test_replay_deterministic();
    test_replay_different_entropy();
    test_replay_different_epoch();
    test_fluctuation_sample_deterministic();
    test_fluctuation_sample_varies();
    test_qrng_read_refill();
    test_qrng_push_read();
    test_domain_separation();
    println!("All replay tests passed!");
}
