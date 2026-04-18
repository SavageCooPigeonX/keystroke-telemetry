"""codebase_transmuter_seq001_v001_numerifier_class_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 66 lines | ~549 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import ast
import json
import re
import time

class _Numerifier(ast.NodeTransformer):
    def __init__(self):
        self._map = {}
        self._counter = 0
        # preserve builtins and keywords
        self._preserve = {
            'True', 'False', 'None', 'self', 'cls', 'super',
            'print', 'len', 'range', 'enumerate', 'zip', 'map', 'filter',
            'isinstance', 'issubclass', 'hasattr', 'getattr', 'setattr',
            'dict', 'list', 'set', 'tuple', 'str', 'int', 'float', 'bool',
            'open', 'Path', 'json', 'os', 're', 'ast', 'sys', 'time',
            'Exception', 'ValueError', 'TypeError', 'KeyError', 'IndexError',
            'ImportError', 'FileNotFoundError', 'AttributeError', 'RuntimeError',
            '__init__', '__main__', '__name__', '__file__', '__all__',
            '__enter__', '__exit__', '__str__', '__repr__', '__iter__',
        }

    def _num(self, name):
        if name in self._preserve:
            return name
        if name.startswith('_') and name.endswith('_'):
            return name
        if name not in self._map:
            self._counter += 1
            self._map[name] = f'n{self._counter}'
        return self._map[name]

    def visit_Name(self, node):
        node.id = self._num(node.id)
        return node

    def visit_FunctionDef(self, node):
        node.name = self._num(node.name)
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node):
        return self.visit_FunctionDef(node)

    def visit_ClassDef(self, node):
        node.name = self._num(node.name)
        self.generic_visit(node)
        return node

    def visit_arg(self, node):
        node.arg = self._num(node.arg)
        node.annotation = None
        return node

    def visit_alias(self, node):
        # keep module names but numerify aliases
        if node.asname:
            node.asname = self._num(node.asname)
        return node

    def visit_Attribute(self, node):
        self.generic_visit(node)
        node.attr = self._num(node.attr)
        return node
