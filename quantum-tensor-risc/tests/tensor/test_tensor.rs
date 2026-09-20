// Copyright © 2026 SnapKitty Collective and contributors.
//
// This file is part of a work licensed under the
// SnapKitty Strong Network Copyleft License Version 1.0 (SSNCL-1.0).
//
// You may use, study, modify, copy, and redistribute this work
// only under the terms of SSNCL-1.0.
//
// A copy of SSNCL-1.0 must accompany this work.

fn test_tile_mul_identity() {
    let mut a = tensor::tile_zero();
    let mut b = tensor::tile_zero();
    for i in 0..tensor::TILE_SZ {
        a[i][i] = 1;
        b[i][i] = 1;
    }
    let c = tensor::tile_mul(&a, &b);
    for i in 0..tensor::TILE_SZ {
        for j in 0..tensor::TILE_SZ {
            if i == j {
                assert_eq!(c[i][j], 1);
            } else {
                assert_eq!(c[i][j], 0);
            }
        }
    }
}

fn test_tile_zero() {
    let t = tensor::tile_zero();
    for i in 0..tensor::TILE_SZ {
        for j in 0..tensor::TILE_SZ {
            assert_eq!(t[i][j], 0);
        }
    }
}

fn test_tile_of() {
    let m = tensor::Matrix::new(tensor::MATRIX_M, tensor::MATRIX_N);
    let tile = tensor::tile_of(&m, 0, 0, tensor::MATRIX_N);
    for i in 0..tensor::TILE_SZ {
        for j in 0..tensor::TILE_SZ {
            assert_eq!(tile[i][j], m[i][j]);
        }
    }
}

fn test_write_tile() {
    let mut m = tensor::Matrix::new(tensor::MATRIX_M, tensor::MATRIX_N);
    let mut t = tensor::tile_zero();
    t[0][0] = 42;
    m = tensor::write_tile(&m, 0, 0, &t);
    assert_eq!(m[0][0], 42);
}

fn test_tile_valid() {
    assert!(tensor::tile_valid(0, 0));
    assert!(tensor::tile_valid(3, 3));
    assert!(!tensor::tile_valid(4, 4));
}

fn main() {
    test_tile_mul_identity();
    test_tile_zero();
    test_tile_of();
    test_write_tile();
    test_tile_valid();
    println!("All tensor tests passed!");
}
