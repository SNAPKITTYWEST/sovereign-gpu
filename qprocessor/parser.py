# Copyright © 2026 SnapKitty Collective and contributors.
#
# This file is part of a work licensed under the
# SnapKitty Strong Network Copyleft License Version 1.0 (SSNCL-1.0).
#
# You may use, study, modify, copy, and redistribute this work
# only under the terms of SSNCL-1.0.
#
# A copy of SSNCL-1.0 must accompany this work.

"""Parser for J-style array expressions and QNASM."""
from typing import List, Optional
from .lexer import Token, Lexer
from .ast import *
from .errors import ParseError

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[0] if tokens else None

    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = None

    def expect(self, type_: str, value: Optional[str] = None) -> Token:
        if not self.current_token:
            raise ParseError("Unexpected end of input", -1, -1)
        if self.current_token.type != type_:
            raise ParseError(f"Expected {type_}, got {self.current_token.type}", 
                           self.current_token.line, self.current_token.column)
        if value is not None and self.current_token.value != value:
            raise ParseError(f"Expected {value}, got {self.current_token.value}", 
                           self.current_token.line, self.current_token.column)
        token = self.current_token
        self.advance()
        return token

    def parse(self) -> Program:
        statements = []
        while self.current_token and self.current_token.type != 'EOF':
            if self.current_token.type == 'NEWLINE':
                self.advance()
                continue
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        return Program(statements)

    def parse_statement(self) -> Optional[Statement]:
        if self.current_token.type == 'IDENT' and self.current_token.value in ['reshape', 'transpose', 'take', 'drop', 'reverse']:
            return self.parse_array_op()
        elif self.current_token.type == 'IDENT':
            return self.parse_assignment()
        elif self.current_token.type == 'QALLOC':
            return self.parse_qalloc()
        elif self.current_token.type == 'H':
            return self.parse_gate('H')
        elif self.current_token.type == 'X':
            return self.parse_gate('X')
        elif self.current_token.type == 'Y':
            return self.parse_gate('Y')
        elif self.current_token.type == 'Z':
            return self.parse_gate('Z')
        elif self.current_token.type == 'S':
            return self.parse_gate('S')
        elif self.current_token.type == 'T':
            return self.parse_gate('T')
        elif self.current_token.type in ['RX', 'RY', 'RZ']:
            return self.parse_rotation()
        elif self.current_token.type == 'CX':
            return self.parse_gate('CX')
        elif self.current_token.type == 'CZ':
            return self.parse_gate('CZ')
        elif self.current_token.type == 'SWAP':
            return self.parse_gate('SWAP')
        elif self.current_token.type == 'RESET':
            return self.parse_gate('RESET')
        elif self.current_token.type == 'MEASURE':
            return self.parse_measure()
        elif self.current_token.type == 'BARRIER':
            return self.parse_barrier()
        elif self.current_token.type == 'MOV':
            return self.parse_mov()
        elif self.current_token.type == 'LOAD':
            return self.parse_load()
        elif self.current_token.type == 'STORE':
            return self.parse_store()
        elif self.current_token.type == 'QARRAY':
            return self.parse_qarray()
        elif self.current_token.type == 'QSLICE':
            return self.parse_qslice()
        elif self.current_token.type == 'QMAP':
            return self.parse_qmap()
        elif self.current_token.type == 'QREDUCE':
            return self.parse_qreduce()
        elif self.current_token.type == 'QDOT':
            return self.parse_qdot()
        elif self.current_token.type == 'QMATMUL':
            return self.parse_qmatmul()
        elif self.current_token.type == 'CALL':
            return self.parse_call()
        elif self.current_token.type == 'RET':
            return self.parse_ret()
        elif self.current_token.type == 'JMP':
            return self.parse_jmp()
        elif self.current_token.type == 'BRANCH':
            return self.parse_branch()
        else:
            self.advance()
            return None

    def parse_assignment(self) -> Assignment:
        var = self.expect('IDENT').value
        self.expect('OP', '=')
        expr = self.parse_expression()
        return Assignment(var, expr)

    def parse_expression(self) -> Expression:
        return self.parse_additive()

    def parse_additive(self) -> Expression:
        expr = self.parse_multiplicative()
        while self.current_token and self.current_token.type == 'OP' and self.current_token.value in ['+', '-']:
            op = self.current_token.value
            self.advance()
            right = self.parse_multiplicative()
            expr = BinaryOp(expr, op, right)
        return expr

    def parse_multiplicative(self) -> Expression:
        expr = self.parse_unary()
        while self.current_token and self.current_token.type == 'OP' and self.current_token.value in ['*', '/', '+.×', '*\/', '+/']:
            op = self.current_token.value
            self.advance()
            right = self.parse_unary()
            expr = BinaryOp(expr, op, right)
        return expr

    def parse_unary(self) -> Expression:
        if self.current_token and self.current_token.type == 'OP' and self.current_token.value in ['-', '<', '>']:
            op = self.current_token.value
            self.advance()
            expr = self.parse_unary()
            return UnaryOp(op, expr)
        return self.parse_postfix()

    def parse_postfix(self) -> Expression:
        expr = self.parse_primary()
        while self.current_token and self.current_token.type == 'LBRACKET':
            self.advance()
            index = self.parse_expression()
            self.expect('RBRACKET')
            expr = Index(expr, index)
        return expr

    def parse_primary(self) -> Expression:
        if self.current_token.type == 'NUMBER':
            value = float(self.current_token.value) if '.' in self.current_token.value else int(self.current_token.value)
            self.advance()
            return Literal(value)
        elif self.current_token.type == 'IDENT':
            name = self.current_token.value
            self.advance()
            return Variable(name)
        elif self.current_token.type == 'LBRACKET':
            self.advance()
            elements = []
            if self.current_token.type != 'RBRACKET':
                while True:
                    elements.append(self.parse_expression())
                    if self.current_token.type == 'COMMA':
                        self.advance()
                    else:
                        break
            self.expect('RBRACKET')
            return ArrayLiteral(elements)
        elif self.current_token.type == 'LPAREN':
            self.advance()
            expr = self.parse_expression()
            self.expect('RPAREN')
            return expr
        else:
            raise ParseError(f"Unexpected token: {self.current_token}", 
                           self.current_token.line, self.current_token.column)

    def parse_array_op(self) -> ArrayOp:
        op = self.expect('IDENT').value
        self.expect('LPAREN')
        array = self.parse_expression()
        self.expect('COMMA')
        if op in ['reshape', 'transpose']:
            arg = self.parse_expression()
            self.expect('RPAREN')
            return ArrayOp(op, array, arg)
        elif op in ['take', 'drop']:
            start = self.parse_expression()
            self.expect('COMMA')
            end = self.parse_expression()
            self.expect('RPAREN')
            return ArrayOp(op, array, [start, end])
        elif op == 'reverse':
            axis = None
            if self.current_token and self.current_token.type == 'COMMA':
                self.advance()
                axis = self.parse_expression()
            self.expect('RPAREN')
            return ArrayOp(op, array, axis)
        else:
            raise ParseError(f"Unknown array operation: {op}", 
                           self.current_token.line, self.current_token.column)

    def parse_qalloc(self) -> QAlloc:
        self.expect('QALLOC')
        count = self.expect('NUMBER')
        return QAlloc(int(count.value))

    def parse_gate(self, gate_type: str) -> Gate:
        self.expect(gate_type)
        qubits = []
        while self.current_token and self.current_token.type == 'IDENT':
            qubits.append(self.expect('IDENT').value)
            if self.current_token and self.current_token.type == 'COMMA':
                self.advance()
        return Gate(gate_type, qubits)

    def parse_rotation(self) -> Rotation:
        gate_type = self.current_token.type
        self.advance()
        qubit = self.expect('IDENT').value
        self.expect('OP', ':')
        angle = self.expect('NUMBER')
        return Rotation(gate_type, qubit, float(angle.value))

    def parse_measure(self) -> Measure:
        self.expect('MEASURE')
        qubit = self.expect('IDENT').value
        self.expect('OP', '->')
        cbit = self.expect('IDENT').value
        return Measure(qubit, cbit)

    def parse_barrier(self) -> Barrier:
        self.expect('BARRIER')
        qubits = []
        while self.current_token and self.current_token.type == 'IDENT':
            qubits.append(self.expect('IDENT').value)
            if self.current_token and self.current_token.type == 'COMMA':
                self.advance()
        return Barrier(qubits)

    def parse_mov(self) -> Mov:
        self.expect('MOV')
        dest = self.expect('IDENT').value
        self.expect('OP', '=')
        src = self.expect('IDENT').value
        return Mov(dest, src)

    def parse_load(self) -> Load:
        self.expect('LOAD')
        dest = self.expect('IDENT').value
        self.expect('OP', '=')
        addr = self.expect('IDENT').value
        return Load(dest, addr)

    def parse_store(self) -> Store:
        self.expect('STORE')
        addr = self.expect('IDENT').value
        self.expect('OP', '=')
        src = self.expect('IDENT').value
        return Store(addr, src)

    def parse_qarray(self) -> QArray:
        self.expect('QARRAY')
        name = self.expect('IDENT').value
        dims = []
        while self.current_token and self.current_token.type == 'NUMBER':
            dims.append(int(self.expect('NUMBER').value))
            if self.current_token and self.current_token.type == 'COMMA':
                self.advance()
        return QArray(name, dims)

    def parse_qslice(self) -> QSlice:
        self.expect('QSLICE')
        name = self.expect('IDENT').value
        self.expect('OP', '[')
        start = self.expect('NUMBER')
        self.expect('OP', ':')
        end = self.expect('NUMBER')
        self.expect('RBRACKET')
        step = 1
        if self.current_token and self.current_token.type == 'COMMA':
            self.advance()
            step = int(self.expect('NUMBER').value)
        return QSlice(name, int(start.value), int(end.value), step)

    def parse_qmap(self) -> QMap:
        self.expect('QMAP')
        gate = self.expect('IDENT').value
        array = self.expect('IDENT').value
        return QMap(gate, array)

    def parse_qreduce(self) -> QReduce:
        self.expect('QREDUCE')
        op = self.expect('IDENT').value
        array = self.expect('IDENT').value
        self.expect('OP', '->')
        result = self.expect('IDENT').value
        return QReduce(op, array, result)

    def parse_qdot(self) -> QDot:
        self.expect('QDOT')
        a = self.expect('IDENT').value
        self.expect('OP', ',')
        b = self.expect('IDENT').value
        self.expect('OP', '->')
        c = self.expect('IDENT').value
        return QDot(a, b, c)

    def parse_qmatmul(self) -> QMatMul:
        self.expect('QMATMUL')
        a = self.expect('IDENT').value
        self.expect('OP', ',')
        b = self.expect('IDENT').value
        self.expect('OP', '->')
        c = self.expect('IDENT').value
        return QMatMul(a, b, c)

    def parse_call(self) -> Call:
        self.expect('CALL')
        name = self.expect('IDENT').value
        args = []
        if self.current_token and self.current_token.type == 'LPAREN':
            self.advance()
            while self.current_token and self.current_token.type != 'RPAREN':
                args.append(self.parse_expression())
                if self.current_token and self.current_token.type == 'COMMA':
                    self.advance()
            self.expect('RPAREN')
        return Call(name, args)

    def parse_ret(self) -> Ret:
        self.expect('RET')
        if self.current_token and self.current_token.type != 'NEWLINE' and self.current_token.type != 'EOF':
            value = self.parse_expression()
            return Ret(value)
        return Ret(None)

    def parse_jmp(self) -> Jmp:
        self.expect('JMP')
        label = self.expect('IDENT').value
        return Jmp(label)

    def parse_branch(self) -> Branch:
        self.expect('BRANCH')
        condition = self.parse_expression()
        self.expect('IDENT', 'if')
        self.expect('OP', ':')
        true_label = self.expect('IDENT').value
        self.expect('IDENT', 'else')
        self.expect('OP', ':')
        false_label = self.expect('IDENT').value
        return Branch(condition, true_label, false_label)
