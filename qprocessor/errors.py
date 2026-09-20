# Copyright © 2026 SnapKitty Collective and contributors.
#
# This file is part of a work licensed under the
# SnapKitty Strong Network Copyleft License Version 1.0 (SSNCL-1.0).
#
# You may use, study, modify, copy, and redistribute this work
# only under the terms of SSNCL-1.0.
#
# A copy of SSNCL-1.0 must accompany this work.

"""Error classes for the quantum array processor."""
class QuantumError(Exception):
    pass

class LexError(QuantumError):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"Lexical error at line {line}, column {column}: {message}")
        self.line = line
        self.column = column

class ParseError(QuantumError):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"Parse error at line {line}, column {column}: {message}")
        self.line = line
        self.column = column

class CompilerError(QuantumError):
    pass

class RuntimeError(QuantumError):
    pass

class SimulationError(QuantumError):
    pass

class AssemblyError(QuantumError):
    pass

class QNASMError(QuantumError):
    pass

class CircuitError(QuantumError):
    pass

class OptimizationError(QuantumError):
    pass

class QuantumIRValidationError(QuantumError):
    pass
