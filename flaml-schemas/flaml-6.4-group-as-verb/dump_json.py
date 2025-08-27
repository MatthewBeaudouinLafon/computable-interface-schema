import compiler
import metalgo
import json
import parser
import orjson

from test_metalgo import get_specs

specs = get_specs()
for [spec, yaml] in specs.items():
    lookup = parser.make_relations(yaml, False, True)[1]
    specs[spec] = {"yaml": yaml, "lookup": lookup}

# Specs
with open("json/specs.json", "wb") as f:
    f.write(orjson.dumps(specs))

# Analogies
analogies = [
    {"inputs": ["imessage", "slack"]},
    {"inputs": ["calendar", "video-editor"]},
]

for analogy in analogies:
    a = compiler.compile_spec(specs[analogy["inputs"][0]]["yaml"])
    b = compiler.compile_spec(specs[analogy["inputs"][1]]["yaml"])
    cv_metalgo, _ = metalgo.compute_analogy(a, b, timeout=60)
    analogy["analogy"] = cv_metalgo[0]

with open("json/analogies.json", "wb") as f:
    f.write(orjson.dumps(analogies))
