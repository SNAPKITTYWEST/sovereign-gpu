# Copyright © 2026 SnapKitty Collective and contributors.
#
# This file is part of a work licensed under the
# SnapKitty Strong Network Copyleft License Version 1.0 (SSNCL-1.0).
#
# You may use, study, modify, copy, and redistribute this work
# only under the terms of SSNCL-1.0.
#
# A copy of SSNCL-1.0 must accompany this work.

"""Tests for QNASM parsing and binary encoding."""
import unittest
from ..qnasm import QNASMParser, QNASMProgram
from ..assembler import Assembler
from ..errors import QNASMError, AssemblyError

class TestQNASM(unittest.TestCase):
    def test_parse_simple_instructions(self):
        parser = QNASMParser()
        source = """
        QALLOC 2
        H q0
        CX q0 q1
        MEASURE q0 c0
        MEASURE q1 c1
        """
        instructions = parser.parse(source)
        self.assertEqual(len(instructions), 4)
        self.assertEqual(instructions[0].opcode, 'QALLOC')
        self.assertEqual(instructions[0].operands, [2])
        self.assertEqual(instructions[1].opcode, 'H')
        self.assertEqual(instructions[1].operands, ['q0'])
        self.assertEqual(instructions[2].opcode, 'CX')
        self.assertEqual(instructions[2].operands, ['q0', 'q1'])
        self.assertEqual(instructions[3].opcode, 'MEASURE')
        self.assertEqual(instructions[3].operands, ['q0', 'c0'])

    def test_parse_rotations(self):
        parser = QNASMParser()
        source = """
        RX q0 1.57
        RY q1 3.14
        RZ q2 0.0
        """
        instructions = parser.parse(source)
        self.assertEqual(len(instructions), 3)
        self.assertEqual(instructions[0].opcode, 'RX')
        self.assertEqual(instructions[0].operands, ['q0', 1.57])
        self.assertEqual(instructions[1].opcode, 'RY')
        self.assertEqual(instructions[1].operands, ['q1', 3.14])
        self.assertEqual(instructions[2].opcode, 'RZ')
        self.assertEqual(instructions[2].operands, ['q2', 0.0])

    def test_parse_array_operations(self):
        parser = QNASMParser()
        source = """
        QALLOC 4
        QARRAY psi 2 2
        QMAP H psi
        QREDUCE sum psi result
        """
        instructions = parser.parse(source)
        self.assertEqual(len(instructions), 4)
        self.assertEqual(instructions[0].opcode, 'QALLOC')
        self.assertEqual(instructions[0].operands, [4])
        self.assertEqual(instructions[1].opcode, 'QARRAY')
        self.assertEqual(instructions[1].operands, ['psi', 2, 2])
        self.assertEqual(instructions[2].opcode, 'QMAP')
        self.assertEqual(instructions[2].operands, ['H', 'psi'])
        self.assertEqual(instructions[3].opcode, 'QREDUCE')
        self.assertEqual(instructions[3].operands, ['sum', 'psi', 'result'])

    def test_validate_valid_program(self):
        parser = QNASMParser()
        source = """
        QALLOC 2
        H q0
        CX q0 q1
        MEASURE q0 c0
        MEASURE q1 c1
        """
        instructions = parser.parse(source)
        program = QNASMProgram(instructions)
        errors = program.validate()
        self.assertEqual(len(errors), 0)

    def test_validate_unallocated_qubit(self):
        parser = QNASMParser()
        source = "H q0"
        instructions = parser.parse(source)
        program = QNASMProgram(instructions)
        errors = program.validate()
        self.assertTrue(any("not allocated" in err for err in errors))

    def test_binary_encoding_decoding(self):
        assembler = Assembler()
        source = """
        QALLOC 2
        H q0
        CX q0 q1
        RZ q0 1.57
        MEASURE q0 c0
        MEASURE q1 c1
        """
        binary = assembler.assemble(source)
        qnasm = assembler.disassemble(binary)
        binary2 = assembler.assemble(qnasm)
        self.assertEqual(binary, binary2)

if __name__ == '__main__':
    unittest.main()
