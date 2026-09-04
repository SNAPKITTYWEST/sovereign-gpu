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
