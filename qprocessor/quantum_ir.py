# Copyright © 2026 SnapKitty Collective and contributors.
#
# This file is part of a work licensed under the
# SnapKitty Strong Network Copyleft License Version 1.0 (SSNCL-1.0).
#
# You may use, study, modify, copy, and redistribute this work
# only under the terms of SSNCL-1.0.
#
# A copy of SSNCL-1.0 must accompany this work.

"""Quantum Intermediate Representation."""
from typing import List, Optional, Dict, Any
from .arrays import QuantumArray
from .errors import QuantumIRValidationError

class IRNode:
    def __init__(self, node_id: int, op: str, operands: List[Any], 
                 shape: Optional[List[int]] = None, qubits: Optional[List[str]] = None,
                 classical_bits: Optional[List[str]] = None, 
                 metadata: Optional[Dict[str, Any]] = None):
        self.node_id = node_id
        self.op = op
        self.operands = operands
        self.shape = shape
        self.qubits = qubits or []
        self.classical_bits = classical_bits or []
        self.metadata = metadata or {}

    def __repr__(self):
        return f"IRNode({self.node_id}, {self.op}, {self.operands})"

class QuantumIR:
    def __init__(self):
        self.nodes: List[IRNode] = []
        self.next_id = 0
        self.variables: Dict[str, Any] = {}
        self.arrays: Dict[str, QuantumArray] = {}

    def add_node(self, op: str, operands: List[Any], 
                 shape: Optional[List[int]] = None, 
                 qubits: Optional[List[str]] = None,
                 classical_bits: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> IRNode:
        node = IRNode(self.next_id, op, operands, shape, qubits, classical_bits, metadata)
        self.nodes.append(node)
        self.next_id += 1
        return node

    def get_node(self, node_id: int) -> Optional[IRNode]:
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        return None

    def validate(self) -> List[str]:
        errors = []
        defined_vars = set()
        for node in self.nodes:
            if node.op in ['QALLOC', 'QARRAY', 'QSLICE', 'QMAP', 'QREDUCE', 'QDOT', 'QMATMUL']:
                if node.operands:
                    var_name = node.operands[0]
                    defined_vars.add(var_name)
            elif node.op in ['LOAD', 'STORE', 'MOV']:
                if len(node.operands) >= 2:
                    defined_vars.add(node.operands[0])
            elif node.op in ['H', 'X', 'Y', 'Z', 'S', 'T', 'RX', 'RY', 'RZ', 'CX', 'CZ', 'SWAP']:
                for qubit in node.qubits:
                    if qubit not in defined_vars and not qubit.startswith('q'):
                        errors.append(f"Undefined qubit: {qubit} at node {node.node_id}")
            elif node.op == 'MEASURE':
                if len(node.operands) >= 2:
                    qubit, cbit = node.operands[0], node.operands[1]
                    if qubit not in defined_vars and not qubit.startswith('q'):
                        errors.append(f"Undefined qubit: {qubit} at node {node.node_id}")
                    if cbit not in defined_vars and not cbit.startswith('c'):
                        errors.append(f"Undefined classical bit: {cbit} at node {node.node_id}")
        return errors

    def optimize(self) -> 'QuantumIR':
        optimized = QuantumIR()
        for node in self.nodes:
            if node.op == 'BARRIER':
                if optimized.nodes and optimized.nodes[-1].op == 'BARRIER':
                    continue
            optimized.nodes.append(node)
        optimized.next_id = len(optimized.nodes)
        return optimized

    def to_qnasm(self) -> str:
        lines = []
        for node in self.nodes:
            if node.op == 'QALLOC':
                lines.append(f"QALLOC {node.operands[0]}")
            elif node.op == 'QFREE':
                lines.append(f"QFREE {node.operands[0]}")
            elif node.op in ['H', 'X', 'Y', 'Z', 'S', 'T']:
                lines.append(f"{node.op} {' '.join(node.qubits)}")
            elif node.op in ['RX', 'RY', 'RZ']:
                angle = node.metadata.get('angle', 0.0)
                lines.append(f"{node.op} {node.qubits[0]} {angle}")
            elif node.op in ['CX', 'CZ', 'SWAP']:
                lines.append(f"{node.op} {' '.join(node.qubits)}")
            elif node.op == 'RESET':
                lines.append(f"RESET {' '.join(node.qubits)}")
            elif node.op == 'MEASURE':
                lines.append(f"MEASURE {node.qubits[0]} {node.classical_bits[0]}")
            elif node.op == 'BARRIER':
                lines.append(f"BARRIER {' '.join(node.qubits)}")
            elif node.op == 'MOV':
                lines.append(f"MOV {node.operands[0]} {node.operands[1]}")
            elif node.op == 'LOAD':
                lines.append(f"LOAD {node.operands[0]} {node.operands[1]}")
            elif node.op == 'STORE':
                lines.append(f"STORE {node.operands[0]} {node.operands[1]}")
            elif node.op == 'QARRAY':
                dims = ' '.join(str(d) for d in node.shape)
                lines.append(f"QARRAY {node.operands[0]} {dims}")
            elif node.op == 'QSLICE':
                lines.append(f"QSLICE {node.operands[0]} {node.operands[1]} {node.operands[2]} {node.operands[3]}")
            elif node.op == 'QMAP':
                lines.append(f"QMAP {node.operands[0]} {node.operands[1]}")
            elif node.op == 'QREDUCE':
                lines.append(f"QREDUCE {node.operands[0]} {node.operands[1]} {node.operands[2]}")
            elif node.op == 'QDOT':
                lines.append(f"QDOT {node.operands[0]} {node.operands[1]} {node.operands[2]}")
            elif node.op == 'QMATMUL':
                lines.append(f"QMATMUL {node.operands[0]} {node.operands[1]} {node.operands[2]}")
            elif node.op == 'CALL':
                args = ', '.join(str(arg) for arg in node.operands)
                lines.append(f"CALL {node.operands[0]} ({args})")
            elif node.op == 'RET':
                if node.operands:
                    lines.append(f"RET {node.operands[0]}")
                else:
                    lines.append("RET")
            elif node.op == 'JMP':
                lines.append(f"JMP {node.operands[0]}")
            elif node.op == 'BRANCH':
                lines.append(f"BRANCH {node.operands[0]} if {node.operands[1]} else {node.operands[2]}")
        return '\n'.join(lines)
