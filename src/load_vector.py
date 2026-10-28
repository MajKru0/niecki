import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
#__file__ - ściezka pliku która się wykouje - tu load_vector
#resolve zamienia ją na ściezkę bezwzględną a parents[1] przechodzi o dwa poziomy w górę
#parents[0]- folder /src, parents[1] - system niecki
#sys path append pozwala szukać modółów w innych miejscach czyli w tym przypadku w korzeniu projektu
from ..app.backend.db import engine
from config import Config

TARGET_CRS = 3035
