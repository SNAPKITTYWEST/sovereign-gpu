# Copyright © 2026 SnapKitty Collective and contributors.
#
# This file is part of a work licensed under the
# SnapKitty Strong Network Copyleft License Version 1.0 (SSNCL-1.0).
#
# You may use, study, modify, copy, and redistribute this work
# only under the terms of SSNCL-1.0.
#
# A copy of SSNCL-1.0 must accompany this work.

"""QNASM assembler and disassembler."""
from .qnasm import QNASMProgram, QNASMInstruction, QNASMParser
from .errors import AssemblyError

class Assembler:
    def __init__(self):
        pass

    def assemble(self, source: str) -> bytes:
        parser = QNASMParser()
        try:
            instructions = parser.parse(source)
        except Exception as e:
            raise AssemblyError(f"Parsing failed: {e}")
        program = QNASMProgram(instructions)
        errors = program.validate()
        if errors:
            raise AssemblyError(f"Validation errors: {'; '.join(errors)}")
        return program.to_binary()

    def disassemble(self, binary: bytes) -> str:
        program = QNASMProgram.from_binary(binary)
        lines = []
        for instr in program.instructions:
            op_str = instr.opcode
            operands_str = ', '.join(str(op) for op in instr.operands)
            lines.append(f"{op_str} {operands_str}")
        return '\n'.join(lines)
