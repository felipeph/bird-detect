import sys
import os

# Adiciona o diretório 'src' ao sys.path para permitir os imports como estão atualmente
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from main import main

if __name__ == "__main__":
    main()
