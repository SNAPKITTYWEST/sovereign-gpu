# Copyright © 2026 SnapKitty Collective and contributors.
#
# This file is part of a work licensed under the
# SnapKitty Strong Network Copyleft License Version 1.0 (SSNCL-1.0).
#
# You may use, study, modify, copy, and redistribute this work
# only under the terms of SSNCL-1.0.
#
# A copy of SSNCL-1.0 must accompany this work.

"""QNASM instruction representation and parsing."""
from typing import List, Optional, Union
from .errors import QNASMError

class QNASMInstruction:
    def __init__(self, opcode: str, operands: List[Union[str, int, float]]):
        self.opcode = opcode.upper()
        self.operands = operands

    def __repr__(self):
        return f"QNASMInstruction({self.opcode}, {self.operands})"

class QNASMParser:
    def __init__(self):
        self.keywords = {
            'QALLOC', 'QFREE', 'H', 'X', 'Y', 'Z', 'S', 'T', 'RX', 'RY', 'RZ',
            'CX', 'CZ', 'SWAP', 'RESET', 'MEASURE', 'BARRIER', 'MOV', 'LOAD',
            'STORE', 'QARRAY', 'QSLICE', 'QMAP', 'QREDUCE', 'QDOT', 'QMATMUL',
            'CALL', 'RET', 'JMP', 'BRANCH'
        }

    def parse_line(self, line: str) -> QNASMInstruction:
        line = line.strip()
        if not line or line.startswith('#'):
            return None
        parts = line.split()
        if not parts:
            return None
        opcode = parts[0].upper()
        if opcode not in self.keywords:
            raise QNASMError(f"Unknown opcode: {opcode}")
        operands = []
        for part in parts[1:]:
            if part.replace('.', '', 1).replace('-', '', 1).isdigit():
                if '.' in part:
                    operands.append(float(part))
                else:
                    operands.append(int(part))
            else:
                operands.append(part)
        return QNASMInstruction(opcode, operands)

    def parse(self, source: str) -> List[QNASMInstruction]:
        instructions = []
        for i, line in enumerate(source.splitlines(), 1):
            try:
                instr = self.parse_line(line)
                if instr:
                    instructions.append(instr)
            except QNASMError as e:
                raise QNASMError(f"Line {i}: {e}")
        return instructions

class QNASMProgram:
    def __init__(self, instructions: List[QNASMInstruction]):
        self.instructions = instructions

    def validate(self) -> List[str]:
        errors = []
        allocated_qubits = set()
        allocated_cbts = set()
        for i, instr in enumerate(self.instructions):
            if instr.opcode == 'QALLOC':
                count = instr.operands[0]
                if not isinstance(count, int) or count <= 0:
                    errors.append(f"QALLOC requires positive integer count at line {i+1}")
                else:
                    for j in range(count):
                        allocated_qubits.add(f"q{j}")
            elif instr.opcode == 'QFREE':
                pass
            elif instr.opcode in ['H', 'X', 'Y', 'Z', 'S', 'T']:
                for qubit in instr.operands:
                    if not isinstance(qubit, str) or not qubit.startswith('q'):
                        errors.append(f"{instr.opcode} requires qubit operand at line {i+1}")
                    elif qubit not in allocated_qubits:
                        errors.append(f"Qubit {qubit} not allocated at line {i+1}")
            elif instr.opcode in ['RX', 'RY', 'RZ']:
                if len(instr.operands) != 2:
                    errors.append(f"{instr.opcode} requires qubit and angle at line {i+1}")
                else:
                    qubit, angle = instr.operands
                    if not isinstance(qubit, str) or not qubit.startswith('q'):
                        errors.append(f"{instr.opcode} requires qubit operand at line {i+1}")
                    elif qubit not in allocated_qubits:
                        errors.append(f"Qubit {qubit} not allocated at line {i+1}")
                    elif not isinstance(angle, (int, float)):
                        errors.append(f"{instr.opcode} requires numeric angle at line {i+1}")
            elif instr.opcode in ['CX', 'CZ', 'SWAP']:
                if len(instr.operands) != 2:
                    errors.append(f"{instr.opcode} requires two qubits at line {i+1}")
                else:
                    q1, q2 = instr.operands
                    if not (isinstance(q1, str) and q1.startswith('q') and 
                            isinstance(q2, str) and q2.startswith('q')):
                        errors.append(f"{instr.opcode} requires qubit operands at line {i+1}")
                    elif q1 not in allocated_qubits or q2 not in allocated_qubits:
                        errors.append(f"Qubit not allocated at line {i+1}")
            elif instr.opcode == 'RESET':
                for qubit in instr.operands:
                    if not isinstance(qubit, str) or not qubit.startswith('q'):
                        errors.append(f"RESET requires qubit operand at line {i+1}")
                    elif qubit not in allocated_qubits:
                        errors.append(f"Qubit {qubit} not allocated at line {i+1}")
            elif instr.opcode == 'MEASURE':
                if len(instr.operands) != 2:
                    errors.append(f"MEASURE requires qubit and classical bit at line {i+1}")
                else:
                    qubit, cbit = instr.operands
                    if not isinstance(qubit, str) or not qubit.startswith('q'):
                        errors.append(f"MEASURE requires qubit operand at line {i+1}")
                    elif qubit not in allocated_qubits:
                        errors.append(f"Qubit {qubit} not allocated at line {i+1}")
                    elif not isinstance(cbit, str) or not cbit.startswith('c'):
                        errors.append(f"MEASURE requires classical bit operand at line {i+1}")
                    else:
                        allocated_cbts.add(cbit)
            elif instr.opcode == 'BARRIER':
                for qubit in instr.operands:
                    if not isinstance(qubit, str) or not qubit.startswith('q'):
                        errors.append(f"BARRIER requires qubit operands at line {i+1}")
                    elif qubit not in allocated_qubits:
                        errors.append(f"Qubit {qubit} not allocated at line {i+1}")
            elif instr.opcode == 'MOV':
                if len(instr.operands) != 2:
                    errors.append(f"MOV requires two operands at line {i+1}")
                else:
                    dest, src = instr.operands
                    if not (isinstance(dest, str) and isinstance(src, str)):
                        errors.append(f"MOV requires string operands at line {i+1}")
            elif instr.opcode in ['LOAD', 'STORE']:
                if len(instr.operands) != 2:
                    errors.append(f"{instr.opcode} requires two operands at line {i+1}")
                else:
                    if not (isinstance(instr.operands[0], str) and isinstance(instr.operands[1], str)):
                        errors.append(f"{instr.opcode} requires string operands at line {i+1}")
            elif instr.opcode == 'QARRAY':
                if len(instr.operands) < 2:
                    errors.append(f"QARRAY requires name and dimensions at line {i+1}")
                else:
                    name = instr.operands[0]
                    if not isinstance(name, str):
                        errors.append(f"QARRAY requires string name at line {i+1}")
                    for dim in instr.operands[1:]:
                        if not isinstance(dim, int) or dim <= 0:
                            errors.append(f"QARRAY dimensions must be positive integers at line {i+1}")
            elif instr.opcode == 'QSLICE':
                if len(instr.operands) != 4:
                    errors.append(f"QSLICE requires name, start, end, step at line {i+1}")
                else:
                    name, start, end, step = instr.operands
                    if not isinstance(name, str):
                        errors.append(f"QSLICE requires string name at line {i+1}")
                    if not all(isinstance(x, int) for x in [start, end, step]):
                        errors.append(f"QSLICE start, end, step must be integers at line {i+1}")
                    if step == 0:
                        errors.append(f"QSLICE step cannot be zero at line {i+1}")
            elif instr.opcode in ['QMAP', 'QREDUCE']:
                if len(instr.operands) != 2:
                    errors.append(f"{instr.opcode} requires gate and array at line {i+1}")
                else:
                    if not all(isinstance(x, str) for x in instr.operands):
                        errors.append(f"{instr.opcode} requires string operands at line {i+1}")
            elif instr.opcode in ['QDOT', 'QMATMUL']:
                if len(instr.operands) != 3:
                    errors.append(f"{instr.opcode} requires three operands at line {i+1}")
                else:
                    if not all(isinstance(x, str) for x in instr.operands):
                        errors.append(f"{instr.opcode} requires string operands at line {i+1}")
            elif instr.opcode == 'CALL':
                if not instr.operands:
                    errors.append(f"CALL requires function name at line {i+1}")
                else:
                    name = instr.operands[0]
                    if not isinstance(name, str):
                        errors.append(f"CALL requires string function name at line {i+1}")
            elif instr.opcode == 'RET':
                pass
            elif instr.opcode == 'JMP':
                if len(instr.operands) != 1:
                    errors.append(f"JMP requires label at line {i+1}")
                else:
                    label = instr.operands[0]
                    if not isinstance(label, str):
                        errors.append(f"JMP requires string label at line {i+1}")
            elif instr.opcode == 'BRANCH':
                if len(instr.operands) != 3:
                    errors.append(f"BRANCH requires condition, true label, false label at line {i+1}")
                else:
                    if not all(isinstance(x, str) for x in instr.operands):
                        errors.append(f"BRANCH requires string operands at line {i+1}")
        return errors

    def to_binary(self) -> bytes:
        opcode_map = {
            'QALLOC': 0, 'QFREE': 1, 'H': 2, 'X': 3, 'Y': 4, 'Z': 5, 'S': 6, 'T': 7,
            'RX': 8, 'RY': 9, 'RZ': 10, 'CX': 11, 'CZ': 12, 'SWAP': 13, 'RESET': 14,
            'MEASURE': 15, 'BARRIER': 16, 'MOV': 17, 'LOAD': 18, 'STORE': 19,
            'QARRAY': 20, 'QSLICE': 21, 'QMAP': 22, 'QREDUCE': 23, 'QDOT': 24,
            'QMATMUL': 25, 'CALL': 26, 'RET': 27, 'JMP': 28, 'BRANCH': 29
        }
        binary = bytearray()
        for instr in self.instructions:
            opcode_byte = opcode_map.get(instr.opcode, 0)
            binary.append(opcode_byte)
            for operand in instr.operands:
                if isinstance(operand, int):
                    binary.extend(operand.to_bytes(4, byteorder='little', signed=True))
                elif isinstance(operand, float):
                    binary.extend(operand.hex().encode('ascii'))
                else:
                    str_bytes = operand.encode('utf-8')
                    binary.extend(len(str_bytes).to_bytes(4, byteorder='little'))
                    binary.extend(str_bytes)
        return bytes(binary)

    @classmethod
    def from_binary(cls, binary: bytes) -> 'QNASMProgram':
        opcode_map = {
            0: 'QALLOC', 1: 'QFREE', 2: 'H', 3: 'X', 4: 'Y', 5: 'Z', 6: 'S', 7: 'T',
            8: 'RX', 9: 'RY', 10: 'RZ', 11: 'CX', 12: 'CZ', 13: 'SWAP', 14: 'RESET',
            15: 'MEASURE', 16: 'BARRIER', 17: 'MOV', 18: 'LOAD', 19: 'STORE',
            20: 'QARRAY', 21: 'QSLICE', 22: 'QMAP', 23: 'QREDUCE', 24: 'QDOT',
            25: 'QMATMUL', 26: 'CALL', 27: 'RET', 28: 'JMP', 29: 'BRANCH'
        }
        instructions = []
        i = 0
        while i < len(binary):
            opcode_byte = binary[i]
            i += 1
            opcode = opcode_map.get(opcode_byte, 'UNKNOWN')
            if opcode == 'UNKNOWN':
                continue
            operands = []
            if opcode in ['QALLOC', 'QFREE']:
                if i + 4 <= len(binary):
                    count = int.from_bytes(binary[i:i+4], byteorder='little', signed=True)
                    operands.append(count)
                    i += 4
            elif opcode in ['H', 'X', 'Y', 'Z', 'S', 'T', 'RESET']:
                if i + 4 <= len(binary):
                    str_len = int.from_bytes(binary[i:i+4], byteorder='little')
                    i += 4
                    if i + str_len <= len(binary):
                        qubit = binary[i:i+str_len].decode('utf-8')
                        operands.append(qubit)
                        i += str_len
            elif opcode in ['RX', 'RY', 'RZ']:
                if i + 4 <= len(binary):
                    str_len = int.from_bytes(binary[i:i+4], byteorder='little')
                    i += 4
                    if i + str_len <= len(binary):
                        qubit = binary[i:i+str_len].decode('utf-8')
                        operands.append(qubit)
                        i += str_len
                if i + 4 <= len(binary):
                    str_len = int.from_bytes(binary[i:i+4], byteorder='little')
                    i += 4
                    if i + str_len <= len(binary):
                        hex_str = binary[i:i+str_len].decode('ascii')
                        operands.append(float.fromhex(hex_str))
                        i += str_len
            elif opcode in ['CX', 'CZ', 'SWAP', 'MEASURE', 'BARRIER', 'MOV', 'LOAD', 'STORE']:
                for _ in range(2):
                    if i + 4 <= len(binary):
                        str_len = int.from_bytes(binary[i:i+4], byteorder='little')
                        i += 4
                        if i + str_len <= len(binary):
                            operand = binary[i:i+str_len].decode('utf-8')
                            operands.append(operand)
                            i += str_len
            elif opcode in ['QARRAY']:
                if i + 4 <= len(binary):
                    str_len = int.from_bytes(binary[i:i+4], byteorder='little')
                    i += 4
                    if i + str_len <= len(binary):
                        name = binary[i:i+str_len].decode('utf-8')
                        operands.append(name)
                        i += str_len
                while i + 4 <= len(binary):
                    dim = int.from_bytes(binary[i:i+4], byteorder='little', signed=True)
                    if dim <= 0:
                        break
                    operands.append(dim)
                    i += 4
            elif opcode in ['QSLICE']:
                for _ in range(4):
                    if i + 4 <= len(binary):
                        val = int.from_bytes(binary[i:i+4], byteorder='little', signed=True)
                        operands.append(val)
                        i += 4
            elif opcode in ['QMAP', 'QREDUCE']:
                for _ in range(2):
                    if i + 4 <= len(binary):
                        str_len = int.from_bytes(binary[i:i+4], byteorder='little')
                        i += 4
                        if i + str_len <= len(binary):
                            operand = binary[i:i+str_len].decode('utf-8')
                            operands.append(operand)
                            i += str_len
            elif opcode in ['QDOT', 'QMATMUL']:
                for _ in range(3):
                    if i + 4 <= len(binary):
                        str_len = int.from_bytes(binary[i:i+4], byteorder='little')
                        i += 4
                        if i + str_len <= len(binary):
                            operand = binary[i:i+str_len].decode('utf-8')
                            operands.append(operand)
                            i += str_len
            elif opcode == 'CALL':
                if i + 4 <= len(binary):
                    str_len = int.from_bytes(binary[i:i+4], byteorder='little')
                    i += 4
                    if i + str_len <= len(binary):
                        name = binary[i:i+str_len].decode('utf-8')
                        operands.append(name)
                        i += str_len
                while i + 4 <= len(binary):
                    if binary[i] == ord('"'):
                        i += 1
                        str_len = 0
                        while i < len(binary) and binary[i] != ord('"'):
                            str_len += 1
                            i += 1
                        if i < len(binary) and binary[i] == ord('"'):
                            i += 1
                        operand = binary[i-str_len:i].decode('utf-8')
                        operands.append(operand)
                    else:
                        if i + 4 <= len(binary):
                            val = int.from_bytes(binary[i:i+4], byteorder='little', signed=True)
                            operands.append(val)
                            i += 4
                        else:
                            break
            elif opcode == 'RET':
                if i + 4 <= len(binary):
                    if binary[i] == ord('"'):
                        i += 1
                        str_len = 0
                        while i < len(binary) and binary[i] != ord('"'):
                            str_len += 1
                            i += 1
                        if i < len(binary) and binary[i] == ord('"'):
                            i += 1
                        operand = binary[i-str_len:i].decode('utf-8')
                        operands.append(operand)
                    else:
                        val = int.from_bytes(binary[i:i+4], byteorder='little', signed=True)
                        operands.append(val)
                        i += 4
            elif opcode == 'JMP':
                if i + 4 <= len(binary):
                    str_len = int.from_bytes(binary[i:i+4], byteorder='little')
                    i += 4
                    if i + str_len <= len(binary):
                        label = binary[i:i+str_len].decode('utf-8')
                        operands.append(label)
                        i += str_len
            elif opcode == 'BRANCH':
                for _ in range(3):
                    if i + 4 <= len(binary):
                        str_len = int.from_bytes(binary[i:i+4], byteorder='little')
                        i += 4
                        if i + str_len <= len(binary):
                            operand = binary[i:i+str_len].decode('utf-8')
                            operands.append(operand)
                            i += str_len
            instructions.append(QNASMInstruction(opcode, operands))
        return QNASMProgram(instructions)
