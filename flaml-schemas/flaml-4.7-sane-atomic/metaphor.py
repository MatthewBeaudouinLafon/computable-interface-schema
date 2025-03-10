overlaps = [] # list of list of matching items
sinister = open(sinister.yaml)
dextera = open(dextera.yaml)

class Reasons(Enum):
	INSTANCE = 0
	RELATION = 1

class match:
	sinister = None
	dextera = None

	def __init__(self, sinister, dextera, reasons):
		self.sinister = sinister['name']
		self.dextera = dextera['name']


def compare_sets()

running_match = []
for s_set in sinister.sets:
	for d_set in dextera.sets:
		for s_set_rel in s_set.relations:
			for d_set_rel in d_set.relations:
				if d_set_rel == s_set_rel:
