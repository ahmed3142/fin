import os
import sys

# make `import src...` work when pytest runs from the project dir
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
