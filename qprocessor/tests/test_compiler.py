# Copyright © 2026 SnapKitty Collective and contributors.
#
# This file is part of a work licensed under the
# SnapKitty Strong Network Copyleft License Version 1.0 (SSNCL-1.0).
#
# You may use, study, modify, copy, and redistribute this work
# only under the terms of SSNCL-1.0.
#
# A copy of SSNCL-1.0 must accompany this work.

"""Tests for compiler functionality."""
import unittest
from ..lexer import Lexer
from ..parser import Parser
from ..ast import *
from ..compiler import Compiler
from ..quantum_ir import QuantumIR
from ..errors import CompilerError

class TestCompiler(unittest.TestCase):
    def test_compile_qalloc(self):
        source = "QALLOC 2"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        compiler = Compiler()
        ir = compiler.compile(ast)
        self.assertEqual(len(ir.nodes), 1)
        self.assertEqual(ir.nodes[0].op, 'QALLOC')
        self.assertEqual(ir.nodes[0].operands, [2])

    def test_compile_gate(self):
        source = "H q0"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        compiler = Compiler()
        ir = compiler.compile(ast)
        self.assertEqual(len(ir.nodes), 1)
        self.assertEqual(ir.nodes[0].op, 'H')

    def test_compile_measure(self):
        source = "MEASURE q0 c0"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        compiler = Compiler()
        ir = compiler.compile(ast)
        self.assertEqual(len(ir.nodes), 1)
        self.assertEqual(ir.nodes[0].op, 'MEASURE')

    def test_compile_barrier(self):
        source = "BARRIER q0 q1"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        compiler = Compiler()
        ir = compiler.compile(ast)
        self.assertEqual(len(ir.nodes), 1)
        self.assertEqual(ir.nodes[0].op, 'BARRIER')

    def test_compile_qarray(self):
        source = "QARRAY psi 2 2"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        compiler = Compiler()
        ir = compiler.compile(ast)
        self.assertEqual(len(ir.nodes), 1)
        self.assertEqual(ir.nodes[0].op, 'QARRAY')
        self.assertEqual(ir.nodes[0].shape, [2, 2])

    def test_compile_qmap(self):
        source = "QMAP H psi"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        compiler = Compiler()
        ir = compiler.compile(ast)
        self.assertEqual(len(ir.nodes), 1)
        self.assertEqual(ir.nodes[0].op, 'QMAP')

    def test_compile_qreduce(self):
        source = "QREDUCE sum psi result"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        compiler = Compiler()
        ir = compiler.compile(ast)
        self.assertEqual(len(ir.nodes), 1)
        self.assertEqual(ir.nodes[0].op, 'QREDUCE')

    def test_compile_control_flow(self):
        source = """
        CALL myfunc
        RET
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        compiler = Compiler()
        ir = compiler.compile(ast)
        self.assertEqual(len(ir.nodes), 2)
        self.assertEqual(ir.nodes[0].op, 'CALL')
        self.assertEqual(ir.nodes[1].op, 'RET')

if __name__ == '__main__':
    unittest.main()
