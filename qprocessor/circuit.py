# Copyright © 2026 SnapKitty Collective and contributors.
#
# This file is part of a work licensed under the
# SnapKitty Strong Network Copyleft License Version 1.0 (SSNCL-1.0).
#
# You may use, study, modify, copy, and redistribute this work
# only under the terms of SSNCL-1.0.
#
# A copy of SSNCL-1.0 must accompany this work.

"""Quantum circuit representation."""
from typing import List, Optional, Union
from .errors import CircuitError

class Qubit:
    def __init__(self, index: int):
        self.index = index

    def __repr__(self):
        return f"q{self.index}"

class ClassicalBit:
    def __init__(self, index: int):
        self.index = index

    def __repr__(self):
        return f"c{self.index}"

class QuantumGate:
    def __init__(self, name: str, qubits: List[Qubit], 
                 classical_bits: List[ClassicalBit] = None,
                 parameters: List[float] = None):
        self.name = name.upper()
        self.qubits = qubits
        self.classical_bits = classical_bits or []
        self.parameters = parameters or []

    def __repr__(self):
        params = f"({','.join(map(str, self.parameters))})" if self.parameters else ""
        qubits = ','.join(str(q) for q in self.qubits)
        cbts = ','.join(str(cb) for cb in self.classical_bits)
        if self.classical_bits:
            return f"{self.name}{params} {qubits} -> {cbts}"
        return f"{self.name}{params} {qubits}"

class Moment:
    def __init__(self, gates: List[QuantumGate]):
        self.gates = gates

    def __repr__(self):
        return f"Moment({len(self.gates)} gates)"

class QuantumCircuit:
    def __init__(self, num_qubits: int = 0, num_cbts: int = 0):
        self.qubits = [Qubit(i) for i in range(num_qubits)]
        self.cbits = [ClassicalBit(i) for i in range(num_cbts)]
        self.moments: List[Moment] = []
        self.next_qubit = num_qubits
        self.next_cbt = num_cbts

    def allocate_qubit(self) -> Qubit:
        qubit = Qubit(self.next_qubit)
        self.qubits.append(qubit)
        self.next_qubit += 1
        return qubit

    def allocate_cbit(self) -> ClassicalBit:
        cbt = ClassicalBit(self.next_cbt)
        self.cbits.append(cbt)
        self.next_cbt += 1
        return cbt

    def release_qubit(self, qubit: Qubit):
        if qubit in self.qubits:
            self.qubits.remove(qubit)

    def release_cbit(self, cbt: ClassicalBit):
        if cbt in self.cbits:
            self.cbits.remove(cbt)

    def add_gate(self, name: str, qubits: List[Qubit], 
                 classical_bits: List[ClassicalBit] = None,
                 parameters: List[float] = None):
        gate = QuantumGate(name, qubits, classical_bits, parameters)
        if not self.moments or len(self.moments[-1].gates) > 0:
            self.moments.append(Moment([]))
        self.moments[-1].gates.append(gate)

    def add_measurement(self, qubit: Qubit, cbit: ClassicalBit):
        self.add_gate('MEASURE', [qubit], [cbit])

    def add_barrier(self, qubits: List[Qubit]):
        if not self.moments or len(self.moments[-1].gates) > 0:
            self.moments.append(Moment([]))
        self.moments[-1].gates.append(QuantumGate('BARRIER', qubits))

    def depth(self) -> int:
        return len(self.moments)

    def width(self) -> int:
        return len(self.qubits)

    def count_gates(self) -> int:
        return sum(len(moment.gates) for moment in self.moments)

    def validate(self) -> List[str]:
        errors = []
        allocated_qubits = set(q.index for q in self.qubits)
        allocated_cbts = set(cb.index for cb in self.cbits)
        for i, moment in enumerate(self.moments):
            for gate in moment.gates:
                for qubit in gate.qubits:
                    if qubit.index not in allocated_qubits:
                        errors.append(f"Qubit {qubit.index} not allocated at moment {i}")
                for cbt in gate.classical_bits:
                    if cbt.index not in allocated_cbts:
                        errors.append(f"Classical bit {cbt.index} not allocated at moment {i}")
                if gate.name in ['RX', 'RY', 'RZ'] and len(gate.parameters) != 1:
                    errors.append(f"Gate {gate.name} requires exactly one parameter at moment {i}")
        return errors

    def to_ascii(self) -> str:
        if not self.qubits:
            return "Empty circuit"
        lines = []
        for i, qubit in enumerate(self.qubits):
            line = f"q{qubit.index} "
            for moment in self.moments:
                gate_in_moment = None
                for gate in moment.gates:
                    if qubit in gate.qubits:
                        gate_in_moment = gate
                        break
                if gate_in_moment:
                    if gate_in_moment.name == 'H':
                        line += "H──"
                    elif gate_in_moment.name == 'X':
                        line += "X──"
                    elif gate_in_moment.name == 'Y':
                        line += "Y──"
                    elif gate_in_moment.name == 'Z':
                        line += "Z──"
                    elif gate_in_moment.name == 'S':
                        line += "S──"
                    elif gate_in_moment.name == 'T':
                        line += "T──"
                    elif gate_in_moment.name == 'RX':
                        line += f"RX({gate_in_moment.parameters[0]:.2f})──"
                    elif gate_in_moment.name == 'RY':
                        line += f"RY({gate_in_moment.parameters[0]:.2f})──"
                    elif gate_in_moment.name == 'RZ':
                        line += f"RZ({gate_in_moment.parameters[0]:.2f})──"
                    elif gate_in_moment.name == 'CX':
                        target = [q for q in gate_in_moment.qubits if q != qubit][0]
                        line += f"●──"
                    elif gate_in_moment.name == 'CZ':
                        target = [q for q in gate_in_moment.qubits if q != qubit][0]
                        line += f"●──"
                    elif gate_in_moment.name == 'SWAP':
                        line += "×──"
                    elif gate_in_moment.name == 'RESET':
                        line += "R──"
                    elif gate_in_moment.name == 'MEASURE':
                        line += "M──"
                    elif gate_in_moment.name == 'BARRIER':
                        line += "│──"
                    else:
                        line += f"{gate_in_moment.name}──"
                else:
                    line += " ──"
            line += "M"
            lines.append(line)
        return '\n'.join(lines)

    @classmethod
    def from_qnasm(cls, binary: bytes) -> 'QuantumCircuit':
        from .qnasm import QNASMProgram
        program = QNASMProgram.from_binary(binary)
        circuit = QuantumCircuit()
        qubit_map: dict[str, Qubit] = {}
        cbt_map: dict[str, ClassicalBit] = {}
        for instr in program.instructions:
            if instr.opcode == 'QALLOC':
                count = instr.operands[0]
                for i in range(count):
                    qubit = circuit.allocate_qubit()
                    qubit_map[f"q{i}"] = qubit
            elif instr.opcode in ['H', 'X', 'Y', 'Z', 'S', 'T']:
                qubits = [qubit_map[op] for op in instr.operands if op in qubit_map]
                circuit.add_gate(instr.opcode, qubits)
            elif instr.opcode in ['RX', 'RY', 'RZ']:
                qubit = qubit_map[instr.operands[0]]
                angle = instr.operands[1]
                circuit.add_gate(instr.opcode, [qubit], parameters=[angle])
            elif instr.opcode in ['CX', 'CZ', 'SWAP']:
                q1 = qubit_map[instr.operands[0]]
                q2 = qubit_map[instr.operands[1]]
                circuit.add_gate(instr.opcode, [q1, q2])
            elif instr.opcode == 'RESET':
                qubit = qubit_map[instr.operands[0]]
                circuit.add_gate('RESET', [qubit])
            elif instr.opcode == 'MEASURE':
                qubit = qubit_map[instr.operands[0]]
                cbit_name = instr.operands[1]
                if cbit_name not in cbt_map:
                    cbt = circuit.allocate_cbit()
                    cbt_map[cbit_name] = cbt
                else:
                    cbt = cbt_map[cbit_name]
                circuit.add_measurement(qubit, cbt)
            elif instr.opcode == 'BARRIER':
                qubits = [qubit_map[op] for op in instr.operands if op in qubit_map]
                circuit.add_barrier(qubits)
            elif instr.opcode == 'MOV':
                pass
            elif instr.opcode in ['LOAD', 'STORE']:
                pass
            elif instr.opcode in ['QARRAY', 'QSLICE', 'QMAP', 'QREDUCE', 'QDOT', 'QMATMUL']:
                pass
            elif instr.opcode in ['CALL', 'RET', 'JMP', 'BRANCH']:
                pass
        return circuit
