import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.chat.deepseek import test

if __name__ == "__main__":
    test() 