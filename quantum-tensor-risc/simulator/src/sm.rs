// Copyright © 2026 SnapKitty Collective and contributors.
//
// This file is part of a work licensed under the
// SnapKitty Strong Network Copyleft License Version 1.0 (SSNCL-1.0).
//
// You may use, study, modify, copy, and redistribute this work
// only under the terms of SSNCL-1.0.
//
// A copy of SSNCL-1.0 must accompany this work.

use serde::{Deserialize, Serialize};

pub const REG_COUNT: usize = 32;
pub const LOCAL_MEM_SIZE: usize = 1024;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SMState {
    pub pc: u32,
    pub regs: [u32; REG_COUNT],
    pub flags_z: bool,
    pub flags_n: bool,
    pub local_mem: [u32; LOCAL_MEM_SIZE],
    pub active: bool,
    pub halted: bool,
    pub sm_id: usize,
}

impl SMState {
    pub fn new(sm_id: usize) -> Self {
        SMState {
            pc: 0,
            regs: [0; REG_COUNT],
            flags_z: false,
            flags_n: false,
            local_mem: [0; LOCAL_MEM_SIZE],
            active: false,
            halted: false,
            sm_id,
        }
    }

    pub fn reset(&mut self) {
        self.pc = 0;
        self.regs = [0; REG_COUNT];
        self.flags_z = false;
        self.flags_n = false;
        self.local_mem = [0; LOCAL_MEM_SIZE];
        self.active = false;
        self.halted = false;
    }
}
