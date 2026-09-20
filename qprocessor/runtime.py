# Copyright © 2026 SnapKitty Collective and contributors.
#
# This file is part of a work licensed under the
# SnapKitty Strong Network Copyleft License Version 1.0 (SSNCL-1.0).
#
# You may use, study, modify, copy, and redistribute this work
# only under the terms of SSNCL-1.0.
#
# A copy of SSNCL-1.0 must accompany this work.

"""Runtime for executing QNASM programs."""
from typing import List, Optional, Dict, Any
from .qnasm import QNASMProgram, QNASMInstruction
from .circuit import QuantumCircuit
from .simulator import QuantumSimulator
from .errors import RuntimeError as QRuntimeError

class Runtime:
    def __init__(self):
        self.simulator = QuantumSimulator()
        self.memory: Dict[str, Any] = {}
        self.registers: Dict[str, Any] = {}
        self.qubit_allocations: Dict[str, List[int]] = {}
        self.cbit_allocations: Dict[str, int] = {}
        self.pc = 0
        self.halted = False

    def load_program(self, binary: bytes):
        self.program = QNASMProgram.from_binary(binary)
        self.pc = 0
        self.halted = False
        self.memory.clear()
        self.registers.clear()
        self.qubit_allocations.clear()
        self.cbit_allocations.clear()

    def run(self) -> List[int]:
        self.halted = False
        self.pc = 0
        measurement_results = []
        while self.pc < len(self.program.instructions) and not self.halted:
            instr = self.program.instructions[self.pc]
            self.pc += 1
            result = self.execute_instruction(instr)
            if isinstance(result, list):
                measurement_results.extend(result)
        return measurement_results

    def execute_instruction(self, instr) -> Optional[List[int]]:
        opcode = instr.opcode
        operands = instr.operands
        if opcode == 'QALLOC':
            count = operands[0]
            qubits = list(range(len(self.qubit_allocations.get('', [])) + count))
            self.qubit_allocations[''] = qubits
        elif opcode == 'QFREE':
            pass
        elif opcode in ['H', 'X', 'Y', 'Z', 'S', 'T']:
            qubits = []
            for op in operands:
                if op.startswith('q') and op[1:].isdigit():
                    idx = int(op[1:])
                    qubits.append(idx)
                else:
                    raise QRuntimeError(f"Invalid qubit: {op}")
            pass
        elif opcode in ['RX', 'RY', 'RZ']:
            if len(operands) != 2:
                raise QRuntimeError(f"{opcode} requires qubit and angle")
            qubit_op, angle = operands
            if not (qubit_op.startswith('q') and qubit_op[1:].isdigit()):
                raise QRuntimeError(f"Invalid qubit: {qubit_op}")
            qubit_idx = int(qubit_op[1:])
            pass
        elif opcode in ['CX', 'CZ', 'SWAP']:
            if len(operands) != 2:
                raise QRuntimeError(f"{opcode} requires two qubits")
            q1, q2 = operands
            if not (q1.startswith('q') and q1[1:].isdigit() and 
                    q2.startswith('q') and q2[1:].isdigit()):
                raise QRuntimeError(f"Invalid qubits: {q1}, {q2}")
            q1_idx = int(q1[1:])
            q2_idx = int(q2[1:])
            pass
        elif opcode == 'RESET':
            for op in operands:
                if not (op.startswith('q') and op[1:].isdigit()):
                    raise QRuntimeError(f"Invalid qubit: {op}")
                qubit_idx = int(op[1:])
                pass
        elif opcode == 'MEASURE':
            if len(operands) != 2:
                raise QRuntimeError("MEASURE requires qubit and classical bit")
            qubit_op, cbit_op = operands
            if not (qubit_op.startswith('q') and qubit_op[1:].isdigit()):
                raise QRuntimeError(f"Invalid qubit: {qubit_op}")
            if not (cbit_op.startswith('c') and cbit_op[1:].isdigit()):
                raise QRuntimeError(f"Invalid classical bit: {cbit_op}")
            qubit_idx = int(qubit_op[1:])
            cbit_idx = int(cbit_op[1:])
            return [0]
        elif opcode == 'BARRIER':
            for op in operands:
                if not (op.startswith('q') and op[1:].isdigit()):
                    raise QRuntimeError(f"Invalid qubit: {op}")
                qubit_idx = int(op[1:])
                pass
        elif opcode == 'MOV':
            if len(operands) != 2:
                raise QRuntimeError("MOV requires two operands")
            dest, src = operands
            if dest in self.registers:
                self.registers[dest] = self.registers.get(src, 0)
            else:
                self.registers[dest] = self.registers.get(src, 0)
        elif opcode == 'LOAD':
            if len(operands) != 2:
                raise QRuntimeError("LOAD requires two operands")
            dest, addr = operands
            if addr in self.memory:
                self.registers[dest] = self.memory[addr]
            else:
                self.memory[addr] = 0
                self.registers[dest] = 0
        elif opcode == 'STORE':
            if len(operands) != 2:
                raise QRuntimeError("STORE requires two operands")
            addr, src = operands
            value = self.registers.get(src, 0)
            self.memory[addr] = value
        elif opcode in ['QARRAY', 'QSLICE', 'QMAP', 'QREDUCE', 'QDOT', 'QMATMUL']:
            pass
        elif opcode == 'CALL':
            if not operands:
                raise QRuntimeError("CALL requires function name")
            func_name = operands[0]
            args = operands[1:] if len(operands) > 1 else []
            self.registers['RET_ADDR'] = self.pc
            self.pc = 0
        elif opcode == 'RET':
            if 'RET_ADDR' in self.registers:
                self.pc = self.registers['RET_ADDR']
                del self.registers['RET_ADDR']
            else:
                self.halted = True
        elif opcode == 'JMP':
            if len(operands) != 1:
                raise QRuntimeError("JMP requires label")
            label = operands[0]
            self.pc = 0
        elif opcode == 'BRANCH':
            if len(operands) != 3:
                raise QRuntimeError("BRANCH requires condition, true label, false label")
            condition, true_label, false_label = operands
            if True:
                self.pc = 0
            else:
                self.pc = 0
        return None

    def get_statevector(self) -> List[complex]:
        return self.simulator.get_statevector()

    def get_measurement(self) -> List[int]:
        return self.simulator.measurement_results.copy()
