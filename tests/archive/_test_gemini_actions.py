"""Quick test of gemini file action parsing + security."""
from pathlib import Path
from pigeon_brain.gemini_chat import parse_file_actions, execute_file_action, strip_action_blocks

# Test 1: Parse action blocks
response = """Here's the fix:

```action
{"action": "write_file", "path": "docs/test_write.txt", "content": "hello from gemini"}
```

Done!"""

actions = parse_file_actions(response)
assert len(actions) == 1, f"Expected 1 action, got {len(actions)}"
assert actions[0]["path"] == "docs/test_write.txt"
print("PASS: parsed 1 action block")

# Test 2: Execute write
root = Path(".")
result = execute_file_action(root, actions[0])
assert result["ok"] is True
assert Path("docs/test_write.txt").read_text() == "hello from gemini"
Path("docs/test_write.txt").unlink()
print("PASS: file written and cleaned up")

# Test 3: Traversal blocked
r = execute_file_action(root, {"action": "write_file", "path": "../evil.py", "content": "bad"})
assert r["ok"] is False
print(f"PASS: traversal blocked: {r['error']}")

# Test 4: Bad prefix blocked
r = execute_file_action(root, {"action": "write_file", "path": ".github/evil.md", "content": "bad"})
assert r["ok"] is False
print(f"PASS: prefix blocked: {r['error']}")

# Test 5: Absolute path blocked
r = execute_file_action(root, {"action": "write_file", "path": "/etc/passwd", "content": "bad"})
assert r["ok"] is False
print(f"PASS: absolute path blocked: {r['error']}")

# Test 6: Strip action blocks
cleaned = strip_action_blocks(response)
assert "```action" not in cleaned
assert "Here's the fix:" in cleaned
assert "Done!" in cleaned
print("PASS: action blocks stripped from display text")

# Test 7: Prompt history injection
from pigeon_brain.gemini_chat import _build_system_context
ctx = _build_system_context(root)
assert "Operator Prompt History" in ctx
print("PASS: operator prompt history included in context")

print("\nALL TESTS PASSED")
