from enum import Enum

overlaps = [] # list of list of matching items
sinister = open('sinister.yaml')
dextera = open('dextera.yaml')

# overlap = {
#     'sets': [
#         {
#             'id': int,
#             'name': (sinister_name, dexter_name),
#             'type': comp
#             'mapto': id
#             'contains':  # need to think about how to match. Maybe interpret them as mapfrom?
#               - id
#         }
#     ]
# }








# 1. Preprocess yaml
#    - mapfrom -> mapto in the right location
#    - contains -> mapto superset


# 2. Find overlaps


# 3. Suggest transfers
