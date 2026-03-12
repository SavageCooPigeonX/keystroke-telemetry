"""cut_executor — Layer 3: Execute DeepSeek cut plans into real files.

Takes JSON cut plans, slices source by AST, writes Pigeon-compliant files,
fixes imports, writes manifests. The refactoring engine.
"""
from pigeon_compiler.cut_executor.plan_parser_seq001_v001 import parse_plan
from pigeon_compiler.cut_executor.source_slicer_seq002_v001 import slice_source
from pigeon_compiler.cut_executor.file_writer_seq003_v001 import write_cut_files
from pigeon_compiler.cut_executor.import_fixer_seq004_v001 import fix_imports
from pigeon_compiler.cut_executor.manifest_writer_seq005_v001 import write_manifest
from pigeon_compiler.cut_executor.plan_validator_seq006_v001 import validate_plan
