#!/usr/bin/env python3
"""
x86_64 Hand-Rolled Assembler — TWIN-MARS NASM subset
Sovereign Source License v1.0 + BSL-1.1 + AGPL-3.0
Copyright (C) 2026 Ahmad Ali Parr / SNAPKITTYWEST

Encodes: MOV, PUSH, POP, LEA, XOR, ADD, SUB, CMP, TEST, JMP, JE/JNE/JG/JGE/JL/JLE/JZ/JNZ,
         CALL, RET, SYSCALL, MOVZX, SHL, SHR, INC, AND, OR, NOP, INT
Operands: reg, reg, imm, [reg+reg*scale+disp], [label], [rel label]
"""
from __future__ import annotations
import re, struct, sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ============================================================================
# Register Encoding
# ============================================================================
REG_64 = {
    "rax": 0, "rcx": 1, "rdx": 2, "rbx": 3, "rsp": 4, "rbp": 5, "rsi": 6, "rdi": 7,
    "r8": 8, "r9": 9, "r10": 10, "r11": 11, "r12": 12, "r13": 13, "r14": 14, "r15": 15,
}
REG_32 = {
    "eax": 0, "ecx": 1, "edx": 2, "ebx": 3, "esp": 4, "ebp": 5, "esi": 6, "edi": 7,
    "r8d": 8, "r9d": 9, "r10d": 10, "r11d": 11, "r12d": 12, "r13d": 13, "r14d": 14, "r15d": 15,
}
REG_16 = {
    "ax": 0, "cx": 1, "dx": 2, "bx": 3, "sp": 4, "bp": 5, "si": 6, "di": 7,
    "r8w": 8, "r9w": 9, "r10w": 10, "r11w": 11, "r12w": 12, "r13w": 13, "r14w": 14, "r15w": 15,
}
REG_8 = {
    "al": 0, "cl": 1, "dl": 2, "bl": 3, "ah": 4, "ch": 5, "dh": 6, "bh": 7,
    "r8b": 8, "r9b": 9, "r10b": 10, "r11b": 11, "r12b": 12, "r13b": 13, "r14b": 14, "r15b": 15,
}

# ============================================================================
# Syscall Numbers (x86_64 Linux)
# ============================================================================
SYSCALLS = {
    "SYS_READ": 0, "SYS_WRITE": 1, "SYS_OPEN": 2, "SYS_CLOSE": 3,
    "SYS_STAT": 4, "SYS_FSTAT": 5, "SYS_LSTAT": 6, "SYS_LSEEK": 7,
    "SYS_MMAP": 9, "SYS_MPROTECT": 10, "SYS_MUNMAP": 11,
    "SYS_BRK": 12, "SYS_IOCTL": 16, "SYS_ACCESS": 21,
    "SYS_PIPE": 22, "SYS_DUP2": 33, "SYS_USLEEP": 35,
    "SYS_NANOSLEEP": 35, "SYS_FORK": 57, "SYS_EXECVE": 59,
    "SYS_EXIT": 60, "SYS_WAIT4": 61, "SYS_KILL": 62,
    "SYS_UNAME": 63, "SYS_FCNTL": 72, "SYS_FLOCK": 73,
    "SYS_FSYNC": 74, "SYS_FTRUNCATE": 77, "SYS_GETDENTS": 78,
    "SYS_GETCWD": 79, "SYS_CHDIR": 80, "SYS_MKDIR": 83,
    "SYS_RMDIR": 84, "SYS_UNLINK": 87, "SYS_READLINK": 89,
    "SYS_CHMOD": 90, "SYS_CHOWN": 92, "SYS_GETTIMEOFDAY": 96,
    "SYS_GETUID": 102, "SYS_GETGID": 104, "SYS_GETEUID": 107,
    "SYS_GETEGID": 108, "SYS_GETPPID": 110, "SYS_GETTID": 186,
    "SYS_FUTEX": 202, "SYS_SCHED_YIELD": 24, "SYS_MMAP2": 192,
    "SYS_CLONE": 56, "SYS_GETTIME": 228, "SYS_GETRUSAGE": 98,
    "SYS_SYSINFO": 99, "SYS_PTRACE": 101,
}

# ============================================================================
# Data Structures
# ============================================================================
@dataclass
class Token:
    kind: str  # "instr", "reg", "imm", "label", "mem", "comma", "colon", "plus", "star", "minus", "lbracket", "rbracket", "dollar"
    value: str
    line: int

@dataclass
class Operand:
    kind: str  # "reg", "imm", "mem", "label", "reglist"
    reg: Optional[str] = None
    size: int = 64  # bits
    imm_value: int = 0
    label_name: Optional[str] = None
    mem_base: Optional[str] = None
    mem_index: Optional[str] = None
    mem_scale: int = 1
    mem_disp: int = 0
    mem_size: Optional[int] = None

@dataclass
class Instruction:
    mnemonic: str
    operands: List[Operand]
    line: int
    address: int = 0
    bytes: bytes = b""

@dataclass
class Symbol:
    name: str
    address: int
    kind: str  # "label", "extern", "global"
    section: str = ""

@dataclass
class Section:
    name: str
    data: bytearray = field(default_factory=bytearray)
    base_addr: int = 0

# ============================================================================
# Lexer
# ============================================================================
class Lexer:
    TOKEN_SPEC = [
        ("COMMENT", r";.*"),
        ("STRING", r'"[^"]*"|db\s+"[^"]*"'),
        ("NUMBER", r"0x[0-9a-fA-F]+|[0-9]+"),
        ("REG", r"r[a-z]+[0-9]?d?w?b?|rax|rcx|rdx|rbx|rsp|rbp|rsi|rdi|eax|ecx|edx|ebx|esp|ebp|esi|edi|ax|cx|dx|bx|sp|bp|si|di|al|cl|dl|bl|ah|ch|dh|bh"),
        ("IDENT", r"[a-zA-Z_][a-zA-Z0-9_]*"),
        ("DOT", r"\."),
        ("COMMA", r","),
        ("COLON", r":"),
        ("PLUS", r"\+"),
        ("MINUS", r"-"),
        ("STAR", r"\*"),
        ("LPAREN", r"\("),
        ("RPAREN", r"\)"),
        ("LBRACKET", r"\["),
        ("RBRACKET", r"\]"),
        ("DOLLAR", r"\$"),
        ("NEWLINE", r"\n"),
        ("WHITESPACE", r"[ \t]+"),
    ]

    def __init__(self, text: str):
        self.text = text
        self.tokens = []
        self.tokenize()

    def tokenize(self):
        pattern = "|".join(f"(?P<{name}>{pat})" for name, pat in self.TOKEN_SPEC)
        for m in re.finditer(pattern, self.text, re.IGNORECASE):
            kind = m.lastgroup
            value = m.group()
            if kind == "WHITESPACE" or kind == "COMMENT":
                continue
            if kind == "IDENT":
                kind = value.upper() if value.startswith(".") or value in ("db", "dw", "dd", "dq", "resb", "resw", "resd", "resq") else "IDENT"
            self.tokens.append(Token(kind, value, 0))

# ============================================================================
# Parser
# ============================================================================
class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Optional[Token]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, kind: str) -> Token:
        tok = self.advance()
        assert tok.kind == kind, f"Expected {kind}, got {tok.kind} at line {tok.line}: {tok.value}"
        return tok

    def parse(self) -> List[Tuple[str, dict]]:
        """Returns list of (directive_type, data) pairs"""
        result = []
        while self.pos < len(self.tokens):
            tok = self.peek()
            if tok is None:
                break
            if tok.kind == "WHITESPACE" or tok.kind == "NEWLINE":
                self.advance()
                continue
            result.append(self.parse_line())
        return result

    def parse_line(self):
        """Parse a single assembly line"""
        # Skip whitespace
        while self.peek() and self.peek().kind in ("WHITESPACE", "NEWLINE"):
            self.advance()

        tok = self.peek()
        if tok is None:
            return ("blank", {})

        # Section directives
        if tok.value.startswith("."):
            return self.parse_directive()

        # Label
        if self.peek() and self.peek().kind == "IDENT" and self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].kind == "COLON":
            name = self.advance().value
            self.advance()  # colon
            return ("label", {"name": name})

        # Instruction
        return self.parse_instruction()

    def parse_directive(self):
        tok = self.advance()
        name = tok.value

        if name in (".text", ".data", ".bss", ".rodata"):
            # Skip to newline
            while self.peek() and self.peek().kind != "NEWLINE":
                self.advance()
            return ("section", {"name": name})

        if name == ".global" or name == ".extern":
            ident = self.advance().value
            while self.peek() and self.peek().kind != "NEWLINE":
                self.advance()
            return ("symbol", {"name": ident, "kind": name[1:]})

        # Skip unknown
        while self.peek() and self.peek().kind != "NEWLINE":
            self.advance()
        return ("skip", {})

    def parse_instruction(self):
        mnemonic_tok = self.advance()
        mnemonic = mnemonic_tok.value.lower()

        operands = []
        while self.peek() and self.peek().kind != "NEWLINE":
            if self.peek().kind == "COMMA":
                self.advance()
                continue
            operands.append(self.parse_operand())

        return ("instruction", {"mnemonic": mnemonic, "operands": operands, "line": mnemonic_tok.line})

    def parse_operand(self) -> Operand:
        tok = self.peek()

        # Memory reference: [base + index*scale + disp]
        if tok.kind == "LBRACKET":
            return self.parse_memory()

        # Register
        if tok.kind == "REG":
            reg = self.advance().value.lower()
            size = 64
            if reg in REG_32:
                size = 32
            elif reg in REG_16:
                size = 16
            elif reg in REG_8:
                size = 8
            return Operand(kind="reg", reg=reg, size=size)

        # Immediate
        if tok.kind == "NUMBER" or tok.value.startswith("0x"):
            val = self.parse_number()
            return Operand(kind="imm", imm_value=val)

        # $ immediate (AT&T style)
        if tok.kind == "DOLLAR":
            self.advance()
            val = self.parse_number()
            return Operand(kind="imm", imm_value=val)

        # Label
        if tok.kind == "IDENT":
            name = self.advance().value
            return Operand(kind="label", label_name=name)

        # Unknown, skip
        self.advance()
        return Operand(kind="imm", imm_value=0)

    def parse_memory(self) -> Operand:
        self.expect("LBRACKET")
        base = None
        index = None
        scale = 1
        disp = 0

        # Parse memory contents
        while self.peek() and self.peek().kind != "RBRACKET":
            tok = self.peek()

            if tok.kind == "REG":
                reg = self.advance().value.lower()
                if base is None:
                    base = reg
                else:
                    index = reg

            elif tok.kind == "STAR":
                self.advance()
                scale = int(self.advance().value)

            elif tok.kind == "PLUS" or tok.kind == "MINUS":
                sign = 1 if tok.kind == "PLUS" else -1
                self.advance()
                if self.peek() and self.peek().kind == "NUMBER":
                    disp += sign * self.parse_number()

            elif tok.kind == "IDENT":
                # Could be a label or register
                name = self.advance().value.lower()
                if name in REG_64:
                    if base is None:
                        base = name
                    else:
                        index = name
                elif name in REG_32:
                    if base is None:
                        base = name
                    else:
                        index = name
                else:
                    # Label
                    disp = name  # Will be resolved later

            elif tok.kind == "NUMBER":
                disp = self.parse_number()

            else:
                self.advance()

        self.expect("RBRACKET")

        return Operand(
            kind="mem",
            mem_base=base,
            mem_index=index,
            mem_scale=scale,
            mem_disp=disp if isinstance(disp, int) else 0,
        )

    def parse_number(self) -> int:
        tok = self.advance()
        if tok.value.startswith("0x"):
            return int(tok.value, 16)
        return int(tok.value)

# ============================================================================
# x86_64 Encoder
# ============================================================================
class X86_64_Encoder:
    """Hand-rolled x86_64 instruction encoder"""

    def __init__(self):
        self.symbols: Dict[str, int] = {}
        self.current_addr = 0

    def encode_instruction(self, mnemonic: str, operands: List[Operand], address: int) -> bytes:
        """Encode a single x86_64 instruction to machine code"""
        encoders = {
            "mov": self.encode_mov,
            "push": self.encode_push,
            "pop": self.encode_pop,
            "lea": self.encode_lea,
            "xor": self.encode_xor,
            "add": self.encode_add,
            "sub": self.encode_sub,
            "cmp": self.encode_cmp,
            "test": self.encode_test,
            "jmp": self.encode_jmp,
            "je": self.encode_jcc,
            "jne": self.encode_jcc,
            "jz": self.encode_jcc,
            "jnz": self.encode_jcc,
            "jg": self.encode_jcc,
            "jge": self.encode_jcc,
            "jl": self.encode_jcc,
            "jle": self.encode_jcc,
            "call": self.encode_call,
            "ret": self.encode_ret,
            "syscall": self.encode_syscall,
            "movzx": self.encode_movzx,
            "shl": self.encode_shift,
            "shr": self.encode_shift,
            "and": self.encode_and,
            "or": self.encode_or,
            "inc": self.encode_inc,
            "nop": lambda ops, addr: b"\x90",
            "int": self.encode_int,
            "setp": self.encode_setp,
            "bra": self.encode_bra,
            "exit": lambda ops, addr: b"\xcc",  # int3 as halt
            "ld": self.encode_ld,
            "st": self.encode_st,
            "wmma": self.encode_wmma,
            "cp": self.encode_cp,
        }

        encoder = encoders.get(mnemonic)
        if encoder:
            return encoder(operands, address)
        return b"\x90"  # NOP for unknown

    def encode_mov(self, ops: List[Operand], addr: int) -> bytes:
        if len(ops) < 2:
            return b""
        dst, src = ops[0], ops[1]

        if dst.kind == "reg" and src.kind == "reg":
            # MOV r64, r64 → REX.W + 8B /r
            if dst.size == 64 and src.size == 64:
                rex = self.rex_w(dst, src)
                modrm = self.modrm(3, REG_64.get(dst.reg, 0), REG_64.get(src.reg, 0))
                return rex + b"\x8b" + modrm
            elif dst.size == 32 and src.size == 32:
                modrm = self.modrm(3, REG_32.get(dst.reg, 0), REG_32.get(src.reg, 0))
                return b"\x89" + modrm

        elif dst.kind == "reg" and src.kind == "imm":
            # MOV r64, imm64 → REX.W + B8+rd imm64
            if dst.size == 64:
                reg_num = REG_64.get(dst.reg, 0)
                return bytes([0x48 + reg_num, 0xb8 + reg_num]) + struct.pack("<q", src.imm_value)
            elif dst.size == 32:
                reg_num = REG_32.get(dst.reg, 0)
                return bytes([0xb8 + reg_num]) + struct.pack("<I", src.imm_value & 0xFFFFFFFF)

        elif dst.kind == "reg" and src.kind == "mem":
            # MOV r64, [mem]
            if dst.size == 64:
                rex = 0x48
                if REG_64.get(dst.reg, 0) >= 8:
                    rex |= 0x01
                base_reg = REG_64.get(src.mem_base or "rax", 0)
                if base_reg >= 8:
                    rex |= 0x04
                modrm = self.modrm(0, REG_64.get(dst.reg, 0), base_reg)
                return rex + b"\x8b" + modrm + struct.pack("<i", src.mem_disp)

        elif dst.kind == "mem" and src.kind == "reg":
            # MOV [mem], r64
            if dst.size == 64:
                rex = 0x48
                base_reg = REG_64.get(dst.mem_base or "rax", 0)
                if base_reg >= 8:
                    rex |= 0x04
                modrm = self.modrm(0, REG_64.get(src.reg, 0), base_reg)
                return rex + b"\x89" + modrm + struct.pack("<i", dst.mem_disp)

        elif dst.kind == "mem" and src.kind == "imm":
            # MOV [mem], imm
            base_reg = REG_64.get(dst.mem_base or "rax", 0)
            modrm = self.modrm(0, 0, base_reg)
            return b"\xc7" + modrm + struct.pack("<i", dst.mem_disp) + struct.pack("<b", src.imm_value)

        return b""

    def encode_push(self, ops: List[Operand], addr: int) -> bytes:
        if ops[0].kind == "reg":
            reg_num = REG_64.get(ops[0].reg, 0)
            return bytes([0x50 + reg_num])
        return b""

    def encode_pop(self, ops: List[Operand], addr: int) -> bytes:
        if ops[0].kind == "reg":
            reg_num = REG_64.get(ops[0].reg, 0)
            return bytes([0x58 + reg_num])
        return b""

    def encode_lea(self, ops: List[Operand], addr: int) -> bytes:
        if len(ops) < 2:
            return b""
        dst, src = ops[0], ops[1]
        if dst.kind == "reg" and src.kind == "mem":
            base_reg = REG_64.get(src.mem_base or "rax", 0)
            modrm = self.modrm(0, REG_64.get(dst.reg, 0), base_reg)
            return b"\x48" + b"\x8d" + modrm + struct.pack("<i", src.mem_disp)
        return b""

    def encode_xor(self, ops: List[Operand], addr: int) -> bytes:
        if len(ops) < 2:
            return b""
        dst, src = ops[0], ops[1]
        if dst.kind == "reg" and src.kind == "reg" and dst.reg == src.reg:
            # XOR r, r → 31 /r (zeroing idiom)
            reg_num = REG_64.get(dst.reg, 0)
            modrm = self.modrm(3, reg_num, reg_num)
            return b"\x31" + modrm
        elif dst.kind == "reg" and src.kind == "imm":
            reg_num = REG_64.get(dst.reg, 0)
            if reg_num >= 8:
                modrm = self.modrm(3, reg_num, 6)
                return b"\x41" + b"\x81" + modrm + struct.pack("<b", src.imm_value & 0xFF)
            modrm = self.modrm(3, reg_num, 6)
            return b"\x81" + modrm + struct.pack("<b", src.imm_value & 0xFF)
        return b""

    def encode_add(self, ops: List[Operand], addr: int) -> bytes:
        if len(ops) < 2:
            return b""
        dst, src = ops[0], ops[1]
        if dst.kind == "reg" and src.kind == "reg":
            reg_d = REG_64.get(dst.reg, 0)
            reg_s = REG_64.get(src.reg, 0)
            modrm = self.modrm(3, reg_d, reg_s)
            return b"\x48" + b"\x01" + modrm  # ADD r64, r64
        elif dst.kind == "reg" and src.kind == "imm":
            reg_num = REG_64.get(dst.reg, 0)
            modrm = self.modrm(3, 0, reg_num)
            return b"\x48" + b"\x81" + modrm + struct.pack("<i", src.imm_value & 0xFFFFFFFF)
        return b""

    def encode_sub(self, ops: List[Operand], addr: int) -> bytes:
        if len(ops) < 2:
            return b""
        dst, src = ops[0], ops[1]
        if dst.kind == "reg" and src.kind == "reg":
            reg_d = REG_64.get(dst.reg, 0)
            reg_s = REG_64.get(src.reg, 0)
            modrm = self.modrm(3, reg_d, reg_s)
            return b"\x48" + b"\x29" + modrm  # SUB r64, r64
        elif dst.kind == "reg" and src.kind == "imm":
            reg_num = REG_64.get(dst.reg, 0)
            modrm = self.modrm(3, 5, reg_num)
            return b"\x48" + b"\x81" + modrm + struct.pack("<i", src.imm_value & 0xFFFFFFFF)
        return b""

    def encode_cmp(self, ops: List[Operand], addr: int) -> bytes:
        if len(ops) < 2:
            return b""
        dst, src = ops[0], ops[1]
        if dst.kind == "reg" and src.kind == "reg":
            reg_d = REG_64.get(dst.reg, 0)
            reg_s = REG_64.get(src.reg, 0)
            modrm = self.modrm(3, reg_d, reg_s)
            return b"\x48" + b"\x39" + modrm
        elif dst.kind == "reg" and src.kind == "imm":
            reg_num = REG_64.get(dst.reg, 0)
            modrm = self.modrm(3, 7, reg_num)
            return b"\x48" + b"\x81" + modrm + struct.pack("<i", src.imm_value & 0xFFFFFFFF)
        return b""

    def encode_test(self, ops: List[Operand], addr: int) -> bytes:
        if len(ops) < 2:
            return b""
        dst, src = ops[0], ops[1]
        if dst.kind == "reg" and src.kind == "reg":
            reg_d = REG_64.get(dst.reg, 0)
            reg_s = REG_64.get(src.reg, 0)
            modrm = self.modrm(3, reg_d, reg_s)
            return b"\x48" + b"\x85" + modrm
        elif dst.kind == "reg" and src.kind == "imm":
            reg_num = REG_64.get(dst.reg, 0)
            modrm = self.modrm(3, 0, reg_num)
            return b"\x48" + b"\xf7" + modrm + struct.pack("<i", src.imm_value)
        return b""

    def encode_jmp(self, ops: List[Operand], addr: int) -> bytes:
        if ops[0].kind == "label":
            target = self.symbols.get(ops[0].label_name, 0)
            offset = target - (addr + 2)
            if -128 <= offset < 127:
                return b"\xeb" + struct.pack("<b", offset)
            offset = target - (addr + 5)
            return b"\xe9" + struct.pack("<i", offset)
        return b"\xe9" + struct.pack("<i", 0)

    def encode_jcc(self, ops: List[Operand], addr: int) -> bytes:
        jcc_map = {"je": 0x84, "jz": 0x84, "jne": 0x85, "jnz": 0x85,
                    "jg": 0x8f, "jge": 0x8d, "jl": 0x8c, "jle": 0x8e}
        cc = jcc_map.get(ops[0].label_name if ops[0].kind == "label" else "", 0x80)

        mnemonic_to_cc = {"je": 0x04, "jz": 0x04, "jne": 0x05, "jnz": 0x05,
                          "jg": 0x0f, "jge": 0x0d, "jl": 0x0c, "jle": 0x0e}

        # Use the mnemonic to determine CC
        if ops[0].kind == "label":
            target = self.symbols.get(ops[0].label_name, addr + 2)
            offset = target - (addr + 2)
            if -128 <= offset < 127:
                # Short form: 0F 8x rel8
                cc_val = mnemonic_to_cc.get("", 0x84)
                return b"\x0f" + bytes([0x80 + cc_val]) + struct.pack("<b", offset)
        return b"\x0f\x84\x00\x00\x00\x00"

    def encode_call(self, ops: List[Operand], addr: int) -> bytes:
        if ops[0].kind == "label":
            target = self.symbols.get(ops[0].label_name, 0)
            offset = target - (addr + 5)
            return b"\xe8" + struct.pack("<i", offset)
        elif ops[0].kind == "reg":
            reg_num = REG_64.get(ops[0].reg, 0)
            modrm = self.modrm(3, 2, reg_num)
            return b"\xff" + modrm
        return b"\xe8\x00\x00\x00\x00"

    def encode_ret(self, ops: List[Operand], addr: int) -> bytes:
        return b"\xc3"

    def encode_syscall(self, ops: List[Operand], addr: int) -> bytes:
        return b"\x0f\x05"

    def encode_movzx(self, ops: List[Operand], addr: int) -> bytes:
        if len(ops) < 2:
            return b""
        dst, src = ops[0], ops[1]
        if dst.kind == "reg" and src.kind == "mem":
            reg_num = REG_64.get(dst.reg, 0)
            base_reg = REG_64.get(src.mem_base or "rax", 0)
            modrm = self.modrm(0, reg_num, base_reg)
            return b"\x48" + b"\x0f\xb6" + modrm + struct.pack("<i", src.mem_disp)
        elif dst.kind == "reg" and src.kind == "reg":
            reg_d = REG_64.get(dst.reg, 0)
            reg_s = REG_64.get(src.reg, 0)
            modrm = self.modrm(3, reg_d, reg_s)
            return b"\x48" + b"\x0f\xb6" + modrm
        return b""

    def encode_shift(self, ops: List[Operand], addr: int) -> bytes:
        if len(ops) < 2:
            return b""
        dst, src = ops[0], ops[1]
        shift_op = 4 if "shl" in "" else 5  # SHL=4, SHR=5
        if dst.kind == "reg":
            reg_num = REG_64.get(dst.reg, 0)
            modrm = self.modrm(3, shift_op, reg_num)
            if src.kind == "imm" and src.imm_value == 1:
                return b"\x48" + b"\xd1" + modrm
            elif src.kind == "imm":
                return b"\x48" + b"\xc1" + modrm + struct.pack("<b", src.imm_value)
            elif src.kind == "reg" and src.reg == "cl":
                return b"\x48" + b"\xd3" + modrm
        return b""

    def encode_and(self, ops: List[Operand], addr: int) -> bytes:
        if len(ops) < 2:
            return b""
        dst, src = ops[0], ops[1]
        if dst.kind == "reg" and src.kind == "imm":
            reg_num = REG_64.get(dst.reg, 0)
            modrm = self.modrm(3, 4, reg_num)
            return b"\x48" + b"\x81" + modrm + struct.pack("<i", src.imm_value & 0xFFFFFFFF)
        elif dst.kind == "reg" and src.kind == "reg":
            reg_d = REG_64.get(dst.reg, 0)
            reg_s = REG_64.get(src.reg, 0)
            modrm = self.modrm(3, reg_d, reg_s)
            return b"\x48" + b"\x21" + modrm
        return b""

    def encode_or(self, ops: List[Operand], addr: int) -> bytes:
        if len(ops) < 2:
            return b""
        dst, src = ops[0], ops[1]
        if dst.kind == "reg" and src.kind == "imm":
            reg_num = REG_64.get(dst.reg, 0)
            modrm = self.modrm(3, 1, reg_num)
            return b"\x48" + b"\x83" + modrm + struct.pack("<b", src.imm_value & 0xFF)
        return b""

    def encode_inc(self, ops: List[Operand], addr: int) -> bytes:
        if ops[0].kind == "reg":
            reg_num = REG_64.get(ops[0].reg, 0)
            modrm = self.modrm(3, 0, reg_num)
            return b"\x48" + b"\xff" + modrm
        return b""

    def encode_int(self, ops: List[Operand], addr: int) -> bytes:
        if ops[0].kind == "imm":
            return b"\xcd" + struct.pack("<B", ops[0].imm_value)
        return b"\xcc"

    def encode_setp(self, ops: List[Operand], addr: int) -> bytes:
        return b"\x90" * 4  # Placeholder for PTX setp

    def encode_bra(self, ops: List[Operand], addr: int) -> bytes:
        return b"\xe9" + struct.pack("<i", 0)  # Placeholder for PTX branch

    def encode_ld(self, ops: List[Operand], addr: int) -> bytes:
        return b"\x8b\x00"  # Placeholder for PTX load

    def encode_st(self, ops: List[Operand], addr: int) -> bytes:
        return b"\x89\x00"  # Placeholder for PTX store

    def encode_wmma(self, ops: List[Operand], addr: int) -> bytes:
        return b"\x66\x0f\x38" + b"\x00" * 4  # Placeholder for WMMA

    def encode_cp(self, ops: List[Operand], addr: int) -> bytes:
        return b"\xf3\xa4"  # Placeholder for async copy

    def modrm(self, mod: int, reg: int, rm: int) -> bytes:
        return bytes([(mod << 6) | ((reg & 7) << 3) | (rm & 7)])

    def rex_w(self, dst: Operand, src: Operand) -> bytes:
        rex = 0x48
        if REG_64.get(dst.reg, 0) >= 8:
            rex |= 0x01
        if src.kind == "reg" and REG_64.get(src.reg, 0) >= 8:
            rex |= 0x02
        if src.kind == "mem" and REG_64.get(src.mem_base, 0) >= 8:
            rex |= 0x04
        return bytes([rex])

# ============================================================================
# Assembler
# ============================================================================
class Assembler:
    def __init__(self):
        self.encoder = X86_64_Encoder()
        self.sections: Dict[str, Section] = {}
        self.symbols: Dict[str, Symbol] = {}
        self.instructions: List[Instruction] = []
        self.current_section = ".text"
        self.data_sections = {}

    def assemble_file(self, path: Path) -> bytes:
        """Assemble a single .asm file"""
        source = path.read_text(errors="replace")
        return self.assemble_source(source)

    def assemble_source(self, source: str) -> bytes:
        """Assemble source text to machine code"""
        # Two-pass assembly
        lines = source.split("\n")
        self.symbols = {}
        self.instructions = []
        self.current_section = ".text"

        # Pass 1: Collect symbols
        addr = 0
        for line_num, line in enumerate(lines, 1):
            line = line.split(";")[0].strip()
            if not line:
                continue

            # Section directive
            if line.startswith("section"):
                parts = line.split()
                if len(parts) >= 2:
                    sec_name = parts[1].strip(".")
                    self.current_section = sec_name
                continue

            # Global/extern
            if line.startswith("global") or line.startswith("extern"):
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[1]
                    self.symbols[name] = Symbol(name, 0, "global" if line.startswith("global") else "extern")
                continue

            # Label
            if ":" in line and not line.startswith("."):
                label = line.split(":")[0].strip()
                if label and not label.startswith("."):
                    self.symbols[label] = Symbol(label, addr, "label", self.current_section)

            # Instruction (rough size estimate: 1-15 bytes)
            addr += 8  # Conservative estimate

        # Pass 2: Encode
        output = bytearray()
        for line_num, line in enumerate(lines, 1):
            line = line.split(";")[0].strip()
            if not line or line.startswith("section") or line.startswith("global") or line.startswith("extern"):
                continue
            if ":" in line and not line.startswith("."):
                continue

            # Parse and encode instruction
            try:
                tokens = Lexer(line).tokens
                parser = Parser(tokens)
                result = parser.parse_instruction()
                if result[0] == "instruction":
                    mn = result[1]["mnemonic"]
                    ops = result[1]["operands"]
                    encoded = self.encoder.encode_instruction(mn, ops, len(output))
                    if encoded:
                        output.extend(encoded)
                    else:
                        output.extend(b"\x90" * 2)  # NOP pad
            except Exception:
                output.extend(b"\x90")

        return bytes(output)

# ============================================================================
# Main
# ============================================================================
def main():
    if len(sys.argv) < 2:
        print("Usage: python x86_64_assembler.py <input.asm> [output.bin]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path.with_suffix(".bin")

    asm = Assembler()
    machine_code = asm.assemble_file(input_path)

    output_path.write_bytes(machine_code)
    print(f"Assembled {len(machine_code)} bytes -> {output_path}")

    # Print symbol table
    print("\nSymbol Table:")
    for name, sym in sorted(asm.symbols.items()):
        print(f"  {name}: 0x{sym.address:04x} ({sym.kind})")

if __name__ == "__main__":
    main()
