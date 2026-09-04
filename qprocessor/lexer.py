"""Lexer for J-style array expressions and QNASM."""
import re
from typing import List, Tuple, Optional
from .errors import LexError

class Token:
    def __init__(self, type_: str, value: str, line: int, column: int):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, {self.line}, {self.column})"

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.tokens: List[Token] = []
        self.line = 1
        self.column = 0
        self.pos = 0
        self.keywords = {
            'QALLOC', 'QFREE', 'H', 'X', 'Y', 'Z', 'S', 'T', 'RX', 'RY', 'RZ',
            'CX', 'CZ', 'SWAP', 'RESET', 'MEASURE', 'BARRIER', 'MOV', 'LOAD',
            'STORE', 'QARRAY', 'QSLICE', 'QMAP', 'QREDUCE', 'QDOT', 'QMATMUL',
            'CALL', 'RET', 'JMP', 'BRANCH', 'reshape', 'transpose', 'take',
            'drop', 'reverse', '+', '-', '*', '+.×', '*/', '+/', '<', '>',
            'if', 'else', 'while', 'return'
        }
        self.token_specs = [
            ('NUMBER', r'\d+(\.\d*)?'),
            ('IDENT', r'[A-Za-z_][A-Za-z0-9_]*'),
            ('OP', r'\+|\-|\*|\/|\+.\×|\*\/|\+\/|<|>|=|==|!=|<=|>=|\&\||\|\|'),
            ('LBRACKET', r'\['),
            ('RBRACKET', r'\]'),
            ('LPAREN', r'\('),
            ('RPAREN', r'\)'),
            ('LBRACE', r'\{'),
            ('RBRACE', r'\}'),
            ('COMMA', r','),
            ('COLON', r':'),
            ('SEMICOLON',r';'),
            ('NEWLINE', r'\n'),
            ('SKIP', r'[ \t]+'),
            ('MISMATCH', r'.'),
        ]
        self.token_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in self.token_specs)

    def tokenize(self) -> List[Token]:
        self.tokens = []
        self.line = 1
        self.column = 0
        self.pos = 0
        while self.pos < len(self.source):
            match = re.match(self.token_regex, self.source[self.pos:])
            if not match:
                raise LexError(f"Unexpected character: {self.source[self.pos]}", self.line, self.column)
            kind = match.lastgroup
            value = match.group()
            if kind == 'NUMBER':
                self.tokens.append(Token('NUMBER', value, self.line, self.column))
            elif kind == 'IDENT':
                if value in self.keywords:
                    self.tokens.append(Token(value, value, self.line, self.column))
                else:
                    self.tokens.append(Token('IDENT', value, self.line, self.column))
            elif kind == 'OP':
                self.tokens.append(Token('OP', value, self.line, self.column))
            elif kind == 'LBRACKET':
                self.tokens.append(Token('LBRACKET', value, self.line, self.column))
            elif kind == 'RBRACKET':
                self.tokens.append(Token('RBRACKET', value, self.line, self.column))
            elif kind == 'LPAREN':
                self.tokens.append(Token('LPAREN', value, self.line, self.column))
            elif kind == 'RPAREN':
                self.tokens.append(Token('RPAREN', value, self.line, self.column))
            elif kind == 'LBRACE':
                self.tokens.append(Token('LBRACE', value, self.line, self.column))
            elif kind == 'RBRACE':
                self.tokens.append(Token('RBRACE', value, self.line, self.column))
            elif kind == 'COMMA':
                self.tokens.append(Token('COMMA', value, self.line, self.column))
            elif kind == 'COLON':
                self.tokens.append(Token('COLON', value, self.line, self.column))
            elif kind == 'SEMICOLON':
                self.tokens.append(Token('SEMICOLON', value, self.line, self.column))
            elif kind == 'NEWLINE':
                self.tokens.append(Token('NEWLINE', value, self.line, self.column))
                self.line += 1
                self.column = -1
            elif kind == 'SKIP':
                pass
            elif kind == 'MISMATCH':
                raise LexError(f"Unexpected character: {value}", self.line, self.column)
            self.pos += len(value)
            self.column += len(value)
        return self.tokens
