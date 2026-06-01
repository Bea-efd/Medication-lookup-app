import sys
sys.path.append("C:/Users/bgiglio/.gemini/antigravity/scratch/medication-lookup/app")

from core.engine import LookupEngine

engine = LookupEngine()
print("Testing Aceclofenac 100 mg:")
res = engine.search_medication("Aceclofenac", "100 mg")
import pprint
pprint.pprint(res)

print("\nTesting Paracetamol 500 mg:")
res2 = engine.search_medication("Paracetamol", "500 mg")
pprint.pprint(res2)
