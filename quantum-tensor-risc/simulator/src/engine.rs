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
use crate::sm::{SMState, REG_COUNT};
use crate::scheduler::{SchedState, Action, SchedEvt};
use crate::qrng::QRNGState;
use crate::isa;

pub const SHARED_MEM_SIZE: usize = 65536;
pub const TILE_SZ: usize = 64;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Tile {
    pub data: Vec<u32>,
}

impl Tile {
    pub fn new() -> Self {
        Tile { data: vec![0u32; TILE_SZ * TILE_SZ] }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EngineSnapshot {
    pub cycle: usize,
    pub action: Action,
    pub sm_states: Vec<SMState>,
    pub shared_mem: Vec<u32>,
    pub sched: SchedState,
    pub qrng: QRNGState,
}

pub struct Engine {
    pub sms: Vec<SMState>,
    pub shared_mem: Vec<u32>,
    pub sched: SchedState,
    pub qrng: QRNGState,
    pub program: Vec<u32>,
    pub cycle: usize,
}

impl Engine {
    pub fn new(num_sms: usize, program_bytes: Vec<u8>) -> Self {
        let program: Vec<u32> = program_bytes
            .chunks_exact(4)
            .map(|c| u32::from_le_bytes(c.try_into().unwrap()))
            .collect();

        let mut sms: Vec<SMState> = (0..num_sms)
            .map(|i| SMState::new(i))
            .collect();

        sms[0].active = true;

        Engine {
            sms,
            shared_mem: vec![0u32; SHARED_MEM_SIZE],
            sched: SchedState::new(num_sms),
            qrng: QRNGState::new(0),
            program,
            cycle: 0,
        }
    }

    pub fn step(&mut self, entropy_word: u64) -> EngineSnapshot {
        self.qrng.push(entropy_word);

        let seed = QRNGState::qseed(entropy_word, self.qrng.epoch);
        let halted: Vec<bool> = self.sms.iter().map(|sm| sm.halted).collect();
        let action = self.sched.map_action(seed, &halted);

        match action {
            Action::Run(sm_id) => {
                let sm = &mut self.sms[sm_id];
                if sm.halted || !sm.active {
                    return self.snapshot(action);
                }

                let addr = sm.pc as usize;
                if addr * 4 < self.program.len() {
                    let word = self.program[addr / 4];
                    if let Some(instr) = isa::decode(word) {
                        let evt = isa::execute_instr(
                            sm,
                            instr,
                            &mut self.shared_mem,
                            &mut self.qrng.buf,
                        );
                        self.process_evt(evt);
                    }
                }
            }
            Action::Spawn(label) => {
                for sm in &mut self.sms {
                    if sm.halted && !sm.active {
                        sm.reset();
                        sm.active = true;
                        sm.pc = label;
                        break;
                    }
                }
            }
            Action::BarrierRelease(bid) => {
                self.sched.barrier_cnt.insert(bid, 0);
            }
            Action::Sync => {}
            Action::NoOp => {}
            _ => {}
        }

        self.cycle += 1;
        self.snapshot(action)
    }

    fn process_evt(&mut self, evt: Option<SchedEvt>) {
        match evt {
            Some(SchedEvt::Spawn(label)) => {
                *self.sched.barrier_cnt.entry(label).or_insert(0) += 1;
            }
            Some(SchedEvt::Barrier(id)) => {
                *self.sched.barrier_cnt.entry(id).or_insert(0) += 1;
            }
            _ => {}
        }
    }

    pub fn all_halted(&self) -> bool {
        self.sms.iter().all(|sm| sm.halted)
    }

    fn snapshot(&self, action: Action) -> EngineSnapshot {
        EngineSnapshot {
            cycle: self.cycle,
            action,
            sm_states: self.sms.clone(),
            shared_mem: self.shared_mem[..1024].to_vec(),
            sched: self.sched.clone(),
            qrng: self.qrng.clone(),
        }
    }
}
