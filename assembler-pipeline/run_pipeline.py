#!/usr/bin/env python3
"""
Unified Assembler Pipeline — x86_64 + PTX → SASS → Gate Level
Sovereign Source License v1.0 + BSL-1.1 + AGPL-3.0
Copyright (C) 2026 Ahmad Ali Parr / SNAPKITTYWEST

Runs the full pipeline:
1. x86_64 assembly → machine code
2. PTX assembly → SASS binary
3. SASS binary → gate-level netlist (JSON)
"""
import sys, json
from pathlib import Path

# Add assembler-pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from x86_64_assembler import Assembler as X86Assembler
from ptx_assembler import PTXParser, PTXToSASS, GateLevelMapper


def run_x86_pipeline(asm_path: Path, output_dir: Path):
    """Assemble x86_64 NASM assembly"""
    print(f"\n{'='*60}")
    print(f"  x86_64 ASSEMBLY PIPELINE")
    print(f"{'='*60}")
    print(f"  Input: {asm_path}")

    asm = X86Assembler()
    machine_code = asm.assemble_file(asm_path)

    output_bin = output_dir / asm_path.with_suffix(".bin").name
    output_bin.write_bytes(machine_code)

    print(f"  Output: {output_bin} ({len(machine_code)} bytes)")
    print(f"  Symbols: {len(asm.symbols)}")
    for name, sym in sorted(asm.symbols.items()):
        print(f"    {name}: 0x{sym.address:04x} ({sym.kind})")

    return machine_code


def run_ptx_pipeline(ptx_path: Path, output_dir: Path):
    """Assemble PTX to SASS and generate gate-level netlist"""
    print(f"\n{'='*60}")
    print(f"  PTX ASSEMBLY PIPELINE")
    print(f"{'='*60}")
    print(f"  Input: {ptx_path}")

    ptx_source = ptx_path.read_text(errors="replace")

    # Parse PTX
    parser = PTXParser(ptx_source)
    parsed = parser.parse()
    print(f"  Parsed {len(parsed)} PTX directives/instructions")

    # Map to SASS
    mapper = PTXToSASS("sm_89")
    sass_binary = mapper.assemble(parsed)

    output_sass = output_dir / ptx_path.with_suffix(".sass.bin").name
    output_sass.write_bytes(sass_binary)
    print(f"  SASS binary: {output_sass} ({len(sass_binary)} bytes)")

    # Generate gate-level netlist
    gate_mapper = GateLevelMapper(sass_binary)
    gate_netlist = gate_mapper.map()

    output_json = output_dir / ptx_path.with_suffix(".gates.json").name
    output_json.write_text(json.dumps(gate_netlist, indent=2))
    print(f"  Gate netlist: {output_json}")
    print(f"  Estimated gate count: {gate_netlist['metadata']['estimated_gate_count']}")
    print(f"  SASS instruction count: {gate_netlist['metadata']['sass_instruction_count']}")

    return sass_binary, gate_netlist


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_pipeline.py <input.asm|input.ptx> [output_dir]")
        print("  or:  python run_pipeline.py --all <dir_with_all_files> [output_dir]")
        sys.exit(1)

    if sys.argv[1] == "--all":
        # Process all files in directory
        input_dir = Path(sys.argv[2])
        output_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)

        x86_files = list(input_dir.glob("*.asm"))
        ptx_files = list(input_dir.glob("*.ptx"))

        print(f"Found {len(x86_files)} x86_64 assembly files")
        print(f"Found {len(ptx_files)} PTX files")

        for f in x86_files:
            run_x86_pipeline(f, output_dir)

        for f in ptx_files:
            run_ptx_pipeline(f, output_dir)

        print(f"\n{'='*60}")
        print(f"  PIPELINE COMPLETE")
        print(f"  Output directory: {output_dir}")
        print(f"{'='*60}")

    else:
        input_path = Path(sys.argv[1])
        output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)

        if input_path.suffix == ".asm":
            run_x86_pipeline(input_path, output_dir)
        elif input_path.suffix == ".ptx":
            run_ptx_pipeline(input_path, output_dir)
        else:
            print(f"Unknown file type: {input_path.suffix}")
            sys.exit(1)


if __name__ == "__main__":
    main()
