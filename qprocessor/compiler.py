"""Compiler from J-style array expressions to Quantum IR."""
from typing import List, Optional, Dict, Any
from .ast import *
from .quantum_ir import QuantumIR, IRNode
from .arrays import QuantumArray, QuantumShape
from .circuit import Qubit, ClassicalBit
from .errors import CompilerError

class Compiler:
    def __init__(self):
        self.ir = QuantumIR()
        self.array_counter = 0
        self.qubit_counter = 0
        self.cbit_counter = 0
        self.array_vars: Dict[str, QuantumArray] = {}
        self.qubit_vars: Dict[str, List[Qubit]] = {}
        self.cbit_vars: Dict[str, ClassicalBit] = {}

    def compile(self, program: Program) -> QuantumIR:
        self.ir = QuantumIR()
        self.array_counter = 0
        self.qubit_counter = 0
        self.cbit_counter = 0
        self.array_vars.clear()
        self.qubit_vars.clear()
        self.cbit_vars.clear()
        for statement in program.statements:
            self.compile_statement(statement)
        return self.ir

    def compile_statement(self, statement: Statement):
        if isinstance(statement, Assignment):
            self.compile_assignment(statement)
        elif isinstance(statement, ArrayOp):
            self.compile_array_op(statement)
        elif isinstance(statement, QAlloc):
            self.compile_qalloc(statement)
        elif isinstance(statement, Gate):
            self.compile_gate(statement)
        elif isinstance(statement, Rotation):
            self.compile_rotation(statement)
        elif isinstance(statement, Measure):
            self.compile_measure(statement)
        elif isinstance(statement, Barrier):
            self.compile_barrier(statement)
        elif isinstance(statement, Mov):
            self.compile_mov(statement)
        elif isinstance(statement, Load):
            self.compile_load(statement)
        elif isinstance(statement, Store):
            self.compile_store(statement)
        elif isinstance(statement, QArray):
            self.compile_qarray(statement)
        elif isinstance(statement, QSlice):
            self.compile_qslice(statement)
        elif isinstance(statement, QMap):
            self.compile_qmap(statement)
        elif isinstance(statement, QReduce):
            self.compile_qreduce(statement)
        elif isinstance(statement, QDot):
            self.compile_qdot(statement)
        elif isinstance(statement, QMatMul):
            self.compile_qmatmul(statement)
        elif isinstance(statement, Call):
            self.compile_call(statement)
        elif isinstance(statement, Ret):
            self.compile_ret(statement)
        elif isinstance(statement, Jmp):
            self.compile_jmp(statement)
        elif isinstance(statement, Branch):
            self.compile_branch(statement)
        else:
            raise CompilerError(f"Unsupported statement type: {type(statement)}")

    def compile_assignment(self, stmt: Assignment):
        value = self.compile_expression(stmt.expr)
        pass

    def compile_expression(self, expr: Expression) -> Any:
        if isinstance(expr, Literal):
            return expr.value
        elif isinstance(expr, Variable):
            if expr.name in self.array_vars:
                return self.array_vars[expr.name]
            elif expr.name in self.qubit_vars:
                return self.qubit_vars[expr.name]
            elif expr.name in self.cbit_vars:
                return self.cbit_vars[expr.name]
            else:
                raise CompilerError(f"Undefined variable: {expr.name}")
        elif isinstance(expr, ArrayLiteral):
            elements = [self.compile_expression(e) for e in expr.elements]
            return QuantumArray(f"arr_{self.array_counter}", QuantumShape([len(elements)]), 
                               [complex(e) if isinstance(e, (int, float)) else e for e in elements])
        elif isinstance(expr, BinaryOp):
            left = self.compile_expression(expr.left)
            right = self.compile_expression(expr.right)
            if expr.op == '+':
                return left + right
            elif expr.op == '-':
                return left - right
            elif expr.op == '*':
                return left * right
            elif expr.op == '/':
                return left / right
            elif expr.op == '+.×':
                if hasattr(left, 'shape') and hasattr(right, 'shape'):
                    return left * right
                else:
                    return left * right
            elif expr.op == '*\/':
                if hasattr(left, 'dot') and hasattr(right, 'dot'):
                    return left.dot(right)
                else:
                    raise CompilerError("Dot product requires arrays")
            elif expr.op == '+/':
                if hasattr(left, 'reduce'):
                    return left.reduce('sum')
                else:
                    raise CompilerError("Reduction requires array")
            else:
                raise CompilerError(f"Unsupported binary op: {expr.op}")
        elif isinstance(expr, UnaryOp):
            operand = self.compile_expression(expr.expr)
            if expr.op == '-':
                return -operand
            elif expr.op == '<':
                return operand < 0
            elif expr.op == '>':
                return operand > 0
            else:
                raise CompilerError(f"Unsupported unary op: {expr.op}")
        elif isinstance(expr, Index):
            array = self.compile_expression(expr.array)
            index = self.compile_expression(expr.index)
            if hasattr(array, '__getitem__'):
                return array[index]
            else:
                raise CompilerError("Cannot index non-array")
        else:
            raise CompilerError(f"Unsupported expression type: {type(expr)}")

    def compile_array_op(self, stmt: ArrayOp):
        array = self.compile_expression(stmt.array)
        pass

    def compile_qalloc(self, stmt: QAlloc):
        self.ir.add_node('QALLOC', [stmt.count])

    def compile_gate(self, stmt: Gate):
        qubits = [f"q{i}" for i in range(len(stmt.qubits))]
        self.ir.add_node(stmt.gate_type, [], qubits=qubits)

    def compile_rotation(self, stmt: Rotation):
        qubit = f"q{self.qubit_counter}"
        self.qubit_counter += 1
        self.ir.add_node(stmt.gate_type, [], qubits=[qubit], metadata={'angle': stmt.angle})

    def compile_measure(self, stmt: Measure):
        qubit = f"q{self.qubit_counter}"
        cbit = f"c{self.cbit_counter}"
        self.qubit_counter += 1
        self.cbit_counter += 1
        self.ir.add_node('MEASURE', [], qubits=[qubit], classical_bits=[cbit])

    def compile_barrier(self, stmt: Barrier):
        qubits = [f"q{i}" for i in range(len(stmt.qubits))]
        self.ir.add_node('BARRIER', [], qubits=qubits)

    def compile_mov(self, stmt: Mov):
        self.ir.add_node('MOV', [stmt.dest, stmt.src])

    def compile_load(self, stmt: Load):
        self.ir.add_node('LOAD', [stmt.dest, stmt.addr])

    def compile_store(self, stmt: Store):
        self.ir.add_node('STORE', [stmt.addr, stmt.src])

    def compile_qarray(self, stmt: QArray):
        self.ir.add_node('QARRAY', [stmt.name], shape=stmt.dims)

    def compile_qslice(self, stmt: QSlice):
        self.ir.add_node('QSLICE', [stmt.name, stmt.start, stmt.end, stmt.step])

    def compile_qmap(self, stmt: QMap):
        self.ir.add_node('QMAP', [stmt.gate, stmt.array])

    def compile_qreduce(self, stmt: QReduce):
        self.ir.add_node('QREDUCE', [stmt.op, stmt.array, stmt.result])

    def compile_qdot(self, stmt: QDot):
        self.ir.add_node('QDOT', [stmt.a, stmt.b, stmt.c])

    def compile_qmatmul(self, stmt: QMatMul):
        self.ir.add_node('QMATMUL', [stmt.a, stmt.b, stmt.c])

    def compile_call(self, stmt: Call):
        args = [self.compile_expression(arg) for arg in stmt.args]
        self.ir.add_node('CALL', [stmt.name] + args)

    def compile_ret(self, stmt: Ret):
        if stmt.value:
            value = self.compile_expression(stmt.value)
            self.ir.add_node('RET', [value])
        else:
            self.ir.add_node('RET', [])

    def compile_jmp(self, stmt: Jmp):
        self.ir.add_node('JMP', [stmt.label])

    def compile_branch(self, stmt: Branch):
        condition = self.compile_expression(stmt.condition)
        self.ir.add_node('BRANCH', [condition, stmt.true_label, stmt.false_label])
