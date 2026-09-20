# Copyright © 2026 SnapKitty Collective and contributors.
#
# This file is part of a work licensed under the
# SnapKitty Strong Network Copyleft License Version 1.0 (SSNCL-1.0).
#
# You may use, study, modify, copy, and redistribute this work
# only under the terms of SSNCL-1.0.
#
# A copy of SSNCL-1.0 must accompany this work.

"""Abstract Syntax Tree nodes for J-style array expressions and QNASM."""
from typing import List, Optional, Union

class Node:
    pass

class Program(Node):
    def __init__(self, statements: List[Node]):
        self.statements = statements

class Statement(Node):
    pass

class Assignment(Statement):
    def __init__(self, var: str, expr: 'Expression'):
        self.var = var
        self.expr = expr

class Expression(Node):
    pass

class Literal(Expression):
    def __init__(self, value: Union[int, float]):
        self.value = value

class Variable(Expression):
    def __init__(self, name: str):
        self.name = name

class ArrayLiteral(Expression):
    def __init__(self, elements: List[Expression]):
        self.elements = elements

class BinaryOp(Expression):
    def __init__(self, left: Expression, op: str, right: Expression):
        self.left = left
        self.op = op
        self.right = right

class UnaryOp(Expression):
    def __init__(self, op: str, expr: Expression):
        self.op = op
        self.expr = expr

class Index(Expression):
    def __init__(self, array: Expression, index: Expression):
        self.array = array
        self.index = index

class ArrayOp(Statement):
    def __init__(self, op: str, array: Expression, arg: Union[Expression, List[Expression], Optional[Expression]]):
        self.op = op
        self.array = array
        self.arg = arg

class QAlloc(Statement):
    def __init__(self, count: int):
        self.count = count

class Gate(Statement):
    def __init__(self, gate_type: str, qubits: List[str]):
        self.gate_type = gate_type
        self.qubits = qubits

class Rotation(Statement):
    def __init__(self, gate_type: str, qubit: str, angle: float):
        self.gate_type = gate_type
        self.qubit = qubit
        self.angle = angle

class Measure(Statement):
    def __init__(self, qubit: str, cbit: str):
        self.qubit = qubit
        self.cbit = cbit

class Barrier(Statement):
    def __init__(self, qubits: List[str]):
        self.qubits = qubits

class Mov(Statement):
    def __init__(self, dest: str, src: str):
        self.dest = dest
        self.src = src

class Load(Statement):
    def __init__(self, dest: str, addr: str):
        self.dest = dest
        self.addr = addr

class Store(Statement):
    def __init__(self, addr: str, src: str):
        self.addr = addr
        self.src = src

class QArray(Statement):
    def __init__(self, name: str, dims: List[int]):
        self.name = name
        self.dims = dims

class QSlice(Statement):
    def __init__(self, name: str, start: int, end: int, step: int):
        self.name = name
        self.start = start
        self.end = end
        self.step = step

class QMap(Statement):
    def __init__(self, gate: str, array: str):
        self.gate = gate
        self.array = array

class QReduce(Statement):
    def __init__(self, op: str, array: str, result: str):
        self.op = op
        self.array = array
        self.result = result

class QDot(Statement):
    def __init__(self, a: str, b: str, c: str):
        self.a = a
        self.b = b
        self.c = c

class QMatMul(Statement):
    def __init__(self, a: str, b: str, c: str):
        self.a = a
        self.b = b
        self.c = c

class Call(Statement):
    def __init__(self, name: str, args: List[Expression]):
        self.name = name
        self.args = args

class Ret(Statement):
    def __init__(self, value: Optional[Expression]):
        self.value = value

class Jmp(Statement):
    def __init__(self, label: str):
        self.label = label

class Branch(Statement):
    def __init__(self, condition: Expression, true_label: str, false_label: str):
        self.condition = condition
        self.true_label = true_label
        self.false_label = false_label
