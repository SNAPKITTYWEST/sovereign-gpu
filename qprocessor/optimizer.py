# Copyright © 2026 SnapKitty Collective and contributors.
#
# This file is part of a work licensed under the
# SnapKitty Strong Network Copyleft License Version 1.0 (SSNCL-1.0).
#
# You may use, study, modify, copy, and redistribute this work
# only under the terms of SSNCL-1.0.
#
# A copy of SSNCL-1.0 must accompany this work.

"""Optimization passes for Quantum IR and circuits."""
from typing import List
from .quantum_ir import QuantumIR, IRNode
from .circuit import QuantumCircuit, QuantumGate, Moment
from .errors import OptimizationError

class IROptimizer:
    def __init__(self):
        pass

    def optimize(self, ir: QuantumIR) -> QuantumIR:
        optimized = QuantumIR()
        i = 0
        while i < len(ir.nodes):
            node = ir.nodes[i]
            if node.op == 'BARRIER':
                if optimized.nodes and optimized.nodes[-1].op == 'BARRIER':
                    i += 1
                    continue
            optimized.nodes.append(node)
            i += 1
        optimized.next_id = len(optimized.nodes)
        return optimized

    def remove_consecutive_barriers(self, ir: QuantumIR) -> QuantumIR:
        optimized = QuantumIR()
        for node in ir.nodes:
            if node.op == 'BARRIER':
                if optimized.nodes and optimized.nodes[-1].op == 'BARRIER':
                    continue
            optimized.nodes.append(node)
        optimized.next_id = len(optimized.nodes)
        return optimized

    def remove_identities(self, ir: QuantumIR) -> QuantumIR:
        optimized = QuantumIR()
        for node in ir.nodes:
            is_identity = False
            if node.op in ['RX', 'RY', 'RZ']:
                angle = node.metadata.get('angle', 0.0)
                if abs(angle % (2 * 3.141592653589793)) < 1e-10:
                    is_identity = True
            if not is_identity:
                optimized.nodes.append(node)
        optimized.next_id = len(optimized.nodes)
        return optimized

class CircuitOptimizer:
    def __init__(self):
        pass

    def optimize(self, circuit: QuantumCircuit) -> QuantumCircuit:
        optimized = QuantumCircuit(circuit.width(), len(circuit.cbits))
        optimized.qubits = circuit.qubits.copy()
        optimized.cbits = circuit.cbits.copy()
        for moment in circuit.moments:
            barrier_gates = [g for g in moment.gates if g.name == 'BARRIER']
            non_barrier_gates = [g for g in moment.gates if g.name != 'BARRIER']
            if non_barrier_gates or not (optimized.moments and 
                                        any(g.name == 'BARRIER' for g in optimized.moments[-1].gates)):
                new_moment = Moment(non_barrier_gates + barrier_gates)
                optimized.moments.append(new_moment)
            else:
                optimized.moments.append(Moment(barrier_gates))
        return optimized

    def merge_adjacent_gates(self, circuit: QuantumCircuit) -> QuantumCircuit:
        optimized = QuantumCircuit(circuit.width(), len(circuit.cbits))
        optimized.qubits = circuit.qubits.copy()
        optimized.cbits = circuit.cbits.copy()
        i = 0
        while i < len(circuit.moments):
            moment = circuit.moments[i]
            if i + 1 < len(circuit.moments):
                next_moment = circuit.moments[i+1]
                merged = True
                temp_gates = []
                moment_single = [g for g in moment.gates if len(g.qubits) == 1 and g.name in ['RX', 'RY', 'RZ']]
                next_single = [g for g in next_moment.gates if len(g.qubits) == 1 and g.name in ['RX', 'RY', 'RZ']]
                if len(moment_single) == len(next_single) and len(moment.gates) == len(moment_single) and len(next_moment.gates) == len(next_single):
                    moment_qubits = [g.qubits[0].index for g in moment_single]
                    next_qubits = [g.qubits[0].index for g in next_single]
                    if moment_qubits == next_qubits:
                        for j in range(len(moment_single)):
                            g1 = moment_single[j]
                            g2 = next_single[j]
                            if g1.name == g2.name:
                                angle1 = g1.parameters[0] if g1.parameters else 0.0
                                angle2 = g2.parameters[0] if g2.parameters else 0.0
                                merged_angle = angle1 + angle2
                                merged_gate = QuantumGate(g1.name, [g1.qubits[0]], parameters=[merged_angle])
                                temp_gates.append(merged_gate)
                            else:
                                merged = False
                                break
                        if merged:
                            other_moment = [g for g in moment.gates if g not in moment_single]
                            other_next = [g for g in next_moment.gates if g not in next_single]
                            new_moment = Moment(other_moment + temp_gates + other_next)
                            optimized.moments.append(new_moment)
                            i += 2
                            continue
            optimized.moments.append(moment)
            i += 1
        return optimized
