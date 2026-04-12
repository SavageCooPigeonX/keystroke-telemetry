import json, re

test = "```json\n{\"intent\":\"Manages a registry\",\"critical_path\":true,\"what_to_fix\":[\"reduce size\"],\"break_risk\":[\"rename breaks\"],\"autonomous_directive\":\"Split the file\",\"reasoning\":\"overcap\"}\n```"

text = test.strip()
text = re.sub(r"^```[a-z]*\s*", "", text)
text = re.sub(r"\s*```\s*$", "", text)
text = text.strip()
print("Cleaned repr:", repr(text[:100]))
parsed = json.loads(text)
print("Parsed OK, keys:", list(parsed.keys()))
print("intent:", parsed["intent"])
