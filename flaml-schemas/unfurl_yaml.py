import yaml
import copy

path = 'flaml-schemas/messages.yaml'
path = 'flaml-schemas/video-editor.yaml'

path = 'flaml-schemas/test.yaml'

# Hack to make sure that anchors resolve. dump doesn't take a flag to do this
# so I guess this overrides the function that resolves aliases. pretty dumb!
# https://github.com/yaml/pyyaml/issues/103
yaml.Dumper.ignore_aliases = lambda *args: True

with open(path, 'r') as file:
    data = yaml.safe_load(file)

# TODO(mattbl): add a `used_in` field for structures to track views and actions

print(yaml.dump(data))
