use serde::{Deserialize, Serialize};

pub type Reg = u8;
pub type Word = u32;
pub type Addr = u32;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Opcode {
    Add, Sub, Mul, Div,
    And, Or, Xor, Not,
    Cmp, Slt, Seq, Sne,
    Addi, Andi, Ori, Xori,
    Ld, St, Ldi,
    Jmp, Beq, Bne, Blt, Bge,
    Call, Ret, Halt,
    Spawn, Join, Sync, Barrier,
    Smid, Laneid, Coreid,
    QrngRead, QrngSeed,
    AtomAdd, AtomSub, AtomAnd, AtomOr, AtomXor, AtomCas,
    Tmov, Tload, Tstore, Tzero, Tsync, Tileid, Tilesz,
    Treduce, TzeroProd, TreduceSync,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum Instr {
    R { op: Opcode, rd: Reg, rs1: Reg, rs2: Reg, f3: u8, f7: u8 },
    I { op: Opcode, rd: Reg, rs1: Reg, imm: i32, f3: u8 },
    S { op: Opcode, rs1: Reg, rs2: Reg, imm: i32, f3: u8 },
    B { op: Opcode, rs1: Reg, rs2: Reg, imm: i32, f3: u8 },
    J { op: Opcode, rd: Reg, imm: i32 },
    A { op: Opcode, rd: Reg, rs1: Reg, rs2: Reg, addr: i32 },
    T { op: Opcode, rd: Reg, rs1: Reg, rs2: Reg, tile_id: i32 },
    Halt,
}

pub const HALT_ADDR: u32 = 0xFFFFFFFF;

pub fn decode(word: u32) -> Option<Instr> {
    let opcode = (word & 0x7F) as u8;
    let rd = ((word >> 7) & 0x1F) as u8;
    let f3 = ((word >> 12) & 0x7) as u8;
    let rs1 = ((word >> 15) & 0x1F) as u8;
    let rs2 = ((word >> 20) & 0x1F) as u8;
    let f7 = ((word >> 25) & 0x7F) as u8;
    let imm12 = ((word as i32) >> 20) & 0xFFF;

    match opcode {
        0x00 => Some(Instr::R { op: Opcode::Add, rd, rs1, rs2, f3, f7 }),
        0x01 => Some(Instr::R { op: Opcode::Sub, rd, rs1, rs2, f3, f7 }),
        0x02 => Some(Instr::R { op: Opcode::Mul, rd, rs1, rs2, f3, f7 }),
        0x03 => Some(Instr::R { op: Opcode::Div, rd, rs1, rs2, f3, f7 }),
        0x04 => Some(Instr::R { op: Opcode::And, rd, rs1, rs2, f3, f7 }),
        0x05 => Some(Instr::R { op: Opcode::Or, rd, rs1, rs2, f3, f7 }),
        0x06 => Some(Instr::R { op: Opcode::Xor, rd, rs1, rs2, f3, f7 }),
        0x07 => Some(Instr::I { op: Opcode::Not, rd, rs1, imm: 0, f3 }),
        0x08 => Some(Instr::R { op: Opcode::Cmp, rd: 0, rs1, rs2, f3, f7 }),
        0x09 => Some(Instr::R { op: Opcode::Slt, rd, rs1, rs2, f3, f7 }),
        0x0A => Some(Instr::R { op: Opcode::Seq, rd, rs1, rs2, f3, f7 }),
        0x0B => Some(Instr::R { op: Opcode::Sne, rd, rs1, rs2, f3, f7 }),
        0x0C => Some(Instr::I { op: Opcode::Addi, rd, rs1, imm: imm12, f3 }),
        0x0D => Some(Instr::I { op: Opcode::Andi, rd, rs1, imm: imm12, f3 }),
        0x0E => Some(Instr::I { op: Opcode::Ori, rd, rs1, imm: imm12, f3 }),
        0x0F => Some(Instr::I { op: Opcode::Xori, rd, rs1, imm: imm12, f3 }),
        0x10 => Some(Instr::I { op: Opcode::Ld, rd, rs1, imm: imm12, f3 }),
        0x11 => Some(Instr::S { op: Opcode::St, rs1, rs2, imm: imm12, f3 }),
        0x12 => Some(Instr::I { op: Opcode::Ldi, rd, rs1: 0, imm: imm12, f3: 0 }),
        0x13 => Some(Instr::J { op: Opcode::Jmp, rd: 0, imm: ((word as i32) >> 12) & 0xFFFFF }),
        0x14 => Some(Instr::B { op: Opcode::Beq, rs1, rs2, imm: imm12, f3 }),
        0x15 => Some(Instr::B { op: Opcode::Bne, rs1, rs2, imm: imm12, f3 }),
        0x16 => Some(Instr::B { op: Opcode::Blt, rs1, rs2, imm: imm12, f3 }),
        0x17 => Some(Instr::B { op: Opcode::Bge, rs1, rs2, imm: imm12, f3 }),
        0x18 => Some(Instr::J { op: Opcode::Call, rd: 0, imm: ((word as i32) >> 12) & 0xFFFFF }),
        0x19 => Some(Instr::R { op: Opcode::Ret, rd: 0, rs1: 0, rs2: 0, f3: 0, f7: 0 }),
        0x1A => Some(Instr::Halt),
        0x1B => Some(Instr::I { op: Opcode::Spawn, rd, rs1: 0, imm: imm12, f3: 0 }),
        0x1C => Some(Instr::I { op: Opcode::Join, rd, rs1: 0, imm: imm12, f3: 0 }),
        0x1D => Some(Instr::R { op: Opcode::Sync, rd: 0, rs1: 0, rs2: 0, f3: 0, f7: 0 }),
        0x1E => Some(Instr::I { op: Opcode::Barrier, rd, rs1: 0, imm: imm12, f3: 0 }),
        0x1F => Some(Instr::A { op: Opcode::AtomAdd, rd, rs1, rs2, addr: imm12 }),
        0x20 => Some(Instr::A { op: Opcode::AtomSub, rd, rs1, rs2, addr: imm12 }),
        0x21 => Some(Instr::A { op: Opcode::AtomAnd, rd, rs1, rs2, addr: imm12 }),
        0x22 => Some(Instr::A { op: Opcode::AtomOr, rd, rs1, rs2, addr: imm12 }),
        0x23 => Some(Instr::A { op: Opcode::AtomXor, rd, rs1, rs2, addr: imm12 }),
        0x24 => Some(Instr::A { op: Opcode::AtomCas, rd, rs1, rs2, addr: imm12 }),
        0x25 => Some(Instr::I { op: Opcode::Smid, rd, rs1: 0, imm: 0, f3: 0 }),
        0x26 => Some(Instr::I { op: Opcode::Laneid, rd, rs1: 0, imm: 0, f3: 0 }),
        0x27 => Some(Instr::I { op: Opcode::Coreid, rd, rs1: 0, imm: 0, f3: 0 }),
        0x28 => Some(Instr::I { op: Opcode::QrngRead, rd, rs1: 0, imm: 0, f3: 0 }),
        0x29 => Some(Instr::I { op: Opcode::QrngSeed, rd: 0, rs1: 0, imm: imm12, f3: 0 }),
        0x7D => Some(Instr::T { op: Opcode::Tmov, rd, rs1, rs2, tile_id: imm12 }),
        0x7E => Some(Instr::T { op: Opcode::Tload, rd, rs1, rs2, tile_id: imm12 }),
        0x7F => Some(Instr::T { op: Opcode::Tstore, rd, rs1, rs2, tile_id: imm12 }),
        _ => None,
    }
}

pub fn execute_instr(
    sm: &mut sm::SMState,
    instr: Instr,
    shared_mem: &mut [u32],
    qrng_buf: &mut Vec<u64>,
) -> Option<scheduler::SchedEvt> {
    match instr {
        Instr::R { op: Opcode::Add, rd, rs1, rs2, .. } => {
            let v1 = sm.regs[rs1 as usize];
            let v2 = sm.regs[rs2 as usize];
            sm.regs[rd as usize] = v1.wrapping_add(v2);
            sm.pc = sm.pc.wrapping_add(4);
            None
        }
        Instr::R { op: Opcode::Sub, rd, rs1, rs2, .. } => {
            let v1 = sm.regs[rs1 as usize];
            let v2 = sm.regs[rs2 as usize];
            sm.regs[rd as usize] = v1.wrapping_sub(v2);
            sm.pc = sm.pc.wrapping_add(4);
            None
        }
        Instr::R { op: Opcode::Mul, rd, rs1, rs2, .. } => {
            let v1 = sm.regs[rs1 as usize];
            let v2 = sm.regs[rs2 as usize];
            sm.regs[rd as usize] = v1.wrapping_mul(v2);
            sm.pc = sm.pc.wrapping_add(4);
            None
        }
        Instr::I { op: Opcode::Ldi, rd, imm, .. } => {
            sm.regs[rd as usize] = imm as u32;
            sm.pc = sm.pc.wrapping_add(4);
            None
        }
        Instr::I { op: Opcode::Addi, rd, rs1, imm, .. } => {
            let v = sm.regs[rs1 as usize];
            sm.regs[rd as usize] = v.wrapping_add(imm as u32);
            sm.pc = sm.pc.wrapping_add(4);
            None
        }
        Instr::I { op: Opcode::Smid, rd, .. } => {
            sm.regs[rd as usize] = sm.sm_id as u32;
            sm.pc = sm.pc.wrapping_add(4);
            None
        }
        Instr::J { op: Opcode::Jmp, imm, .. } => {
            sm.pc = imm as u32;
            None
        }
        Instr::J { op: Opcode::Call, imm, .. } => {
            sm.regs[31] = sm.pc.wrapping_add(4);
            sm.pc = imm as u32;
            None
        }
        Instr::R { op: Opcode::Ret, .. } => {
            sm.pc = sm.regs[31];
            None
        }
        Instr::Halt => {
            sm.halted = true;
            sm.active = false;
            sm.pc = HALT_ADDR;
            None
        }
        Instr::I { op: Opcode::Spawn, imm, .. } => {
            sm.pc = sm.pc.wrapping_add(4);
            Some(scheduler::SchedEvt::Spawn(imm as u32))
        }
        Instr::I { op: Opcode::Barrier, imm, .. } => {
            sm.pc = sm.pc.wrapping_add(4);
            Some(scheduler::SchedEvt::Barrier(imm as u32))
        }
        Instr::I { op: Opcode::Ld, rd, rs1, imm, .. } => {
            let addr = sm.regs[rs1 as usize].wrapping_add(imm as u32) as usize;
            if addr < shared_mem.len() {
                sm.regs[rd as usize] = shared_mem[addr];
            }
            sm.pc = sm.pc.wrapping_add(4);
            None
        }
        Instr::S { op: Opcode::St, rs1, rs2, imm, .. } => {
            let addr = sm.regs[rs1 as usize].wrapping_add(imm as u32) as usize;
            if addr < shared_mem.len() {
                shared_mem[addr] = sm.regs[rs2 as usize];
            }
            sm.pc = sm.pc.wrapping_add(4);
            None
        }
        Instr::I { op: Opcode::QrngRead, rd, .. } => {
            if let Some(word) = qrng_buf.first() {
                sm.regs[rd as usize] = *word as u32;
                qrng_buf.remove(0);
            } else {
                sm.halted = true;
            }
            sm.pc = sm.pc.wrapping_add(4);
            None
        }
        _ => {
            sm.pc = sm.pc.wrapping_add(4);
            None
        }
    }
}
