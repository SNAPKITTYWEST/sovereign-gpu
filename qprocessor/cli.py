"""Command-line interface for the quantum array processor."""
import sys
import os
from typing import List
from .lexer import Lexer
from .parser import Parser
from .ast import Program
from .compiler import Compiler
from .quantum_ir import QuantumIR
from .qnasm import QNASMParser, QNASMProgram
from .assembler import Assembler
from .circuit import QuantumCircuit
from .simulator import QuantumSimulator
from .runtime import Runtime
from .errors import *

def compile_j_file(source_path: str) -> str:
    with open(source_path, 'r') as f:
        source = f.read()
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    compiler = Compiler()
    ir = compiler.compile(ast)
    ir = ir.optimize()
    qnasm = ir.to_qnasm()
    return qnasm

def assemble_qnasm(source_path: str) -> bytes:
    with open(source_path, 'r') as f:
        source = f.read()
    assembler = Assembler()
    binary = assembler.assemble(source)
    return binary

def run_qnasm(binary_path: str) -> List[int]:
    with open(binary_path, 'rb') as f:
        binary = f.read()
    runtime = Runtime()
    runtime.load_program(binary)
    results = runtime.run()
    return results

def simulate_qnasm(binary_path: str) -> List[complex]:
    with open(binary_path, 'rb') as f:
        binary = f.read()
    circuit = QuantumCircuit.from_qnasm(binary)
    simulator = QuantumSimulator()
    results = simulator.run_circuit(circuit)
    statevector = simulator.get_statevector()
    return statevector

def disassemble_binary(binary_path: str) -> str:
    with open(binary_path, 'rb') as f:
        binary = f.read()
    assembler = Assembler()
    qnasm = assembler.disassemble(binary)
    return qnasm

def dump_ir(source_path: str) -> str:
    with open(source_path, 'r') as f:
        source = f.read()
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    compiler = Compiler()
    ir = compiler.compile(ast)
    return str(ir.nodes)

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m qprocessor <command> <args>")
        print("Commands:")
        print(" compile <file.j> - Compile J-style to QNASM")
        print(" assemble <file.qnasm> - Assemble QNASM to binary")
        print(" run <file.qnasm> - Run QNASM program and print measurements")
        print(" simulate <file.qnasm> - Simulate and print statevector")
        print(" disassemble <file.bin> - Disassemble binary to QNASM")
        print(" dump-ir <file.j> - Dump IR from J-style file")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        if command == 'compile':
            if len(sys.argv) < 3:
                print("Error: compile requires <file.j>")
                sys.exit(1)
            qnasm = compile_j_file(sys.argv[2])
            print(qnasm)
        elif command == 'assemble':
            if len(sys.argv) < 3:
                print("Error: assemble requires <file.qnasm>")
                sys.exit(1)
            binary = assemble_qnasm(sys.argv[2])
            bin_file = sys.argv[2].replace('.qnasm', '.bin')
            with open(bin_file, 'wb') as f:
                f.write(binary)
            print(f"Assembled to {bin_file}")
        elif command == 'run':
            if len(sys.argv) < 3:
                print("Error: run requires <file.qnasm>")
                sys.exit(1)
            bin_file = sys.argv[2].replace('.qnasm', '.bin')
            if not os.path.exists(bin_file):
                print(f"Binary file {bin_file} not found. Assembling...")
                binary = assemble_qnasm(sys.argv[2])
                with open(bin_file, 'wb') as f:
                    f.write(binary)
            results = run_qnasm(bin_file)
            print(''.join(str(r) for r in results))
        elif command == 'simulate':
            if len(sys.argv) < 3:
                print("Error: simulate requires <file.qnasm>")
                sys.exit(1)
            bin_file = sys.argv[2].replace('.qnasm', '.bin')
            if not os.path.exists(bin_file):
                print(f"Binary file {bin_file} not found. Assembling...")
                binary = assemble_qnasm(sys.argv[2])
                with open(bin_file, 'wb') as f:
                    f.write(binary)
            statevector = simulate_qnasm(bin_file)
            print(statevector)
        elif command == 'disassemble':
            if len(sys.argv) < 3:
                print("Error: disassemble requires <file.bin>")
                sys.exit(1)
            qnasm = disassemble_binary(sys.argv[2])
            print(qnasm)
        elif command == 'dump-ir':
            if len(sys.argv) < 3:
                print("Error: dump-ir requires <file.j>")
                sys.exit(1)
            ir_str = dump_ir(sys.argv[2])
            print(ir_str)
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
