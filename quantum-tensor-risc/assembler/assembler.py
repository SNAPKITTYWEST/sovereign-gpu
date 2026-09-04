#!/usr/bin/env python3
"""sovereign-gpu assembler — Python 3.11+ macro assembler for 32-bit RISC ISA.
 Sovereign Source License v1.0 + BSL-1.1 + AGPL-3.0
 Copyright (C) 2026 Ahmad Ali Parr / SNAPKITTYWEST
"""

from __future__ import annotations
import json
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional

OPCODES: Dict[str, int] = {
    "ADD": 0x00, "SUB": 0x01, "MUL": 0x02, "DIV": 0x03,
    "AND": 0x04, "OR": 0x05, "XOR": 0x06, "NOT": 0x07,
    "CMP": 0x08, "SLT": 0x09, "SEQ": 0x0A, "SNE": 0x0B,
    "ADDI": 0x0C, "ANDI": 0x0D, "ORI": 0x0E, "XORI": 0x0F,
    "LD": 0x10, "ST": 0x11, "LDI": 0x12,
    "JMP": 0x13, "BEQ": 0x14, "BNE": 0x15, "BLT": 0x16, "BGE": 0x17,
    "CALL": 0x18, "RET": 0x19, "HALT": 0x1A,
    "SPAWN": 0x1B, "JOIN": 0x1C, "SYNC": 0x1D, "BARRIER": 0x1E,
    "ATOM_ADD": 0x1F, "ATOM_SUB": 0x20, "ATOM_AND": 0x21,
    "ATOM_OR": 0x22, "ATOM_XOR": 0x23, "ATOM_CAS": 0x24,
    "SMID": 0x25, "LANEID": 0x26, "COREID": 0x27,
    "QRNG_READ": 0x28, "QRNG_SEED": 0x29,
    "TMOV": 0x7D, "TLOAD": 0x7E, "TSTORE": 0x7F,
    "TZERO": 0x80, "TSYNC": 0x81, "TILEID": 0x82, "TILESZ": 0x83,
    "TREDUCE": 0x84, "TZERO_PROD": 0x85, "TREDUCE_SYNC": 0x86,
}

R_TYPE_OPCODES = {"ADD", "SUB", "MUL", "DIV", "AND", "OR", "XOR", "NOT",
                  "CMP", "SLT", "SEQ", "SNE", "RET", "HALT", "SYNC"}
I_TYPE_OPCODES = {"ADDI", "ANDI", "ORI", "XORI", "LD", "LDI",
                  "SMID", "LANEID", "COREID", "QRNG_READ",
                  "SPAWN", "JOIN", "BARRIER"}
S_TYPE_OPCODES = {"ST"}
B_TYPE_OPCODES = {"BEQ", "BNE", "BLT", "BGE"}
J_TYPE_OPCODES = {"JMP", "CALL"}
A_TYPE_OPCODES = {"ATOM_ADD", "ATOM_SUB", "ATOM_AND", "ATOM_OR", "ATOM_XOR", "ATOM_CAS"}
T_TYPE_OPCODES = {"TMOV", "TLOAD", "TSTORE", "TZERO", "TSYNC", "TILEID", "TILESZ",
                  "TREDUCE", "TZERO_PROD", "TREDUCE_SYNC"}

DOMAIN = 0x5A5A5A5A
PROC_ID = 0x01
PROG_HASH = 0xDEADBEEF
TENSOR_M = 256
TENSOR_K = 256
TENSOR_N = 256


@dataclass
class Instr:
    op: str
    rd: Optional[int] = None
    rs1: Optional[int] = None
    rs2: Optional[int] = None
    imm: Optional[int] = None
    f3: int = 0
    f7: int = 0
    label: Optional[str] = None


@dataclass
class AssemblyState:
    labels: Dict[str, int] = field(default_factory=dict)
    instructions: List[Instr] = field(default_factory=list)
    constants: Dict[str, int] = field(default_factory=dict)
    pc: int = 0


def parse_reg(token: str) -> int:
    token = token.strip().lower()
    if token.startswith("x"):
        return int(token[1:])
    reg_map = {"a0": 10, "a1": 11, "a2": 12, "a3": 13,
               "t0": 5, "t1": 6, "t2": 7,
               "s0": 8, "s1": 9, "ra": 31, "sp": 2, "zero": 0, "one": 1}
    return reg_map.get(token, 0)


def parse_imm(token: str, constants: Dict[str, int]) -> int:
    token = token.strip()
    if token in constants:
        return constants[token]
    if token.startswith("0x"):
        return int(token, 16)
    if token.startswith("0b"):
        return int(token, 2)
    return int(token)


def qseed(entropy: int, epoch: int) -> int:
    combined = entropy + DOMAIN + PROC_ID + PROG_HASH + TENSOR_M + TENSOR_K + TENSOR_N + epoch
    return combined & 0xFFFFFFFFFFFFFFFF


def assemble_file(path: Path) -> bytes:
    state = AssemblyState()
    lines = path.read_text().splitlines()

    for line in lines:
        line = line.split(";")[0].strip()
        if not line:
            continue

        if line.startswith(".const"):
            parts = line.split()
            if len(parts) == 3:
                state.constants[parts[1]] = parse_imm(parts[2], {})
            continue

        if ":" in line and not line.startswith("."):
            label, rest = line.split(":", 1)
            state.labels[label.strip()] = state.pc
            line = rest.strip()
            if not line:
                continue

        parts = line.replace(",", " ").split()
        if not parts:
            continue

        op = parts[0].upper()
        tokens = parts[1:]

        instr = Instr(op=op)

        if op in R_TYPE_OPCODES:
            if len(tokens) >= 3:
                instr.rd = parse_reg(tokens[0])
                instr.rs1 = parse_reg(tokens[1])
                instr.rs2 = parse_reg(tokens[2])
            elif len(tokens) == 1:
                instr.rd = parse_reg(tokens[0])

        elif op in I_TYPE_OPCODES:
            if len(tokens) >= 3:
                instr.rd = parse_reg(tokens[0])
                instr.rs1 = parse_reg(tokens[1])
                instr.imm = parse_imm(tokens[2], state.constants)
            elif len(tokens) == 2:
                instr.rd = parse_reg(tokens[0])
                instr.imm = parse_imm(tokens[1], state.constants)

        elif op in S_TYPE_OPCODES:
            if len(tokens) >= 3:
                instr.rs1 = parse_reg(tokens[0])
                instr.rs2 = parse_reg(tokens[1])
                instr.imm = parse_imm(tokens[2], state.constants)

        elif op in B_TYPE_OPCODES:
            if len(tokens) >= 3:
                instr.rs1 = parse_reg(tokens[0])
                instr.rs2 = parse_reg(tokens[1])
                instr.label = tokens[2]

        elif op in J_TYPE_OPCODES:
            if len(tokens) >= 2:
                instr.rd = parse_reg(tokens[0])
                instr.label = tokens[1]
            elif len(tokens) == 1:
                instr.label = tokens[0]

        elif op in A_TYPE_OPCODES:
            if len(tokens) >= 4:
                instr.rd = parse_reg(tokens[0])
                instr.rs1 = parse_reg(tokens[1])
                instr.rs2 = parse_reg(tokens[2])
                instr.imm = parse_imm(tokens[3], state.constants)

        elif op in T_TYPE_OPCODES:
            if len(tokens) >= 4:
                instr.rd = parse_reg(tokens[0])
                instr.rs1 = parse_reg(tokens[1])
                instr.rs2 = parse_reg(tokens[2])
                instr.imm = parse_imm(tokens[3], state.constants)

        state.instructions.append(instr)
        state.pc += 4

    encoding = []
    for instr in state.instructions:
        opcode = OPCODES.get(instr.op, 0)
        word = opcode

        if instr.op in R_TYPE_OPCODES and instr.rd is not None:
            rd = instr.rd or 0
            rs1 = instr.rs1 or 0
            rs2 = instr.rs2 or 0
            word |= (rd << 7) | (instr.f3 << 12) | (rs1 << 15) | (rs2 << 20) | (instr.f7 << 25)

        elif instr.op in I_TYPE_OPCODES and instr.rd is not None:
            rd = instr.rd or 0
            rs1 = instr.rs1 or 0
            imm = instr.imm or 0
            word |= (rd << 7) | (instr.f3 << 12) | (rs1 << 15) | ((imm & 0xFFF) << 20)

        elif instr.op in S_TYPE_OPCODES:
            rs1 = instr.rs1 or 0
            rs2 = instr.rs2 or 0
            imm = instr.imm or 0
            word |= (rs1 << 15) | (rs2 << 20) | (instr.f3 << 12)
            word |= ((imm & 0x1F) << 7) | (((imm >> 5) & 0x7F) << 25)

        elif instr.op in B_TYPE_OPCODES:
            rs1 = instr.rs1 or 0
            rs2 = instr.rs2 or 0
            if instr.label and instr.label in state.labels:
                imm = state.labels[instr.label] - state.pc
            else:
                imm = instr.imm or 0
            word |= (rs1 << 15) | (rs2 << 20) | (instr.f3 << 12)
            word |= (((imm >> 1) & 0xF) << 8) | (((imm >> 5) & 0x3F) << 25) | (((imm >> 11) & 1) << 7)

        elif instr.op in J_TYPE_OPCODES:
            rd = instr.rd or 0
            if instr.label and instr.label in state.labels:
                imm = state.labels[instr.label] - state.pc
            else:
                imm = instr.imm or 0
            word |= (rd << 7) | ((imm & 0x1F) << 12) | (((imm >> 5) & 0xFF) << 12) | (((imm >> 13) & 1) << 20)

        elif instr.op in A_TYPE_OPCODES:
            rd = instr.rd or 0
            rs1 = instr.rs1 or 0
            rs2 = instr.rs2 or 0
            addr = instr.imm or 0
            word |= (rd << 7) | (rs1 << 10) | (rs2 << 15) | ((addr & 0x1F) << 20)

        elif instr.op in T_TYPE_OPCODES:
            rd = instr.rd or 0
            rs1 = instr.rs1 or 0
            rs2 = instr.rs2 or 0
            tid = instr.imm or 0
            word |= (rd << 7) | (rs1 << 10) | (rs2 << 15) | ((tid & 0x1F) << 20)

        encoding.append(word)

    return b"".join(w.to_bytes(4, "little") for w in encoding)


def main():
    if len(sys.argv) < 2:
        print("Usage: python assembler.py <input.s> [output.bin]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path.with_suffix(".bin")

    machine_code = assemble_file(input_path)
    output_path.write_bytes(machine_code)
    print(f"Assembled {len(machine_code)} bytes -> {output_path}")

    bytecode = list(machine_code)
    print(f"Bytecode: {json.dumps(bytecode)}")


if __name__ == "__main__":
    main()
