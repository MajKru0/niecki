@"
# System analizy terenów zagrożonych osiadaniem

Praca magisterska
temat:


## Struktura repozytorium
- data/raw — dane surowe (nieśledzone w Git)
- data/processed — dane po przetworzeniu
- notebooks — eksperymenty, PoC (Jupyter)
- src — kod źródłowy pipeline'u analitycznego
- app/backend — Flask API
- app/frontend — interfejs webowy
- docs — dokumentacja, materiały do pracy pisemnej
"@ | Out-File -FilePath README.md -Encoding utf8


### Zakres
Projekt i implementacja systemu do analizy obszarów zagrożonych
osiadaniem terenu z wykorzystaniem interferometrii radarowej oraz
danych o pokryciu i użytkowaniu terenu

Zakres pracy:
Praca obejmuje projekt i implementację systemu do analizy obszarów
zagrożonych osiadaniem terenu. Głównym założeniem systemu jest
integracja zobrazowań SAR oraz danych o pokryciu i użytkowaniu terenu.

Część implementacyjna zakłada opracowanie aplikacji stanowiącej 
narzędzie wspomagające analizę i wizualizację wyników — w formie
aplikacji desktopowej lub webowej — umożliwiającej interaktywną
prezentację map przemieszczeń, nakładanie warstw tematycznych oraz
generowanie podstawowych raportów. Efektem pracy będzie funkcjonalny
system pozwalający na identyfikację oraz wstępną ocenę obszarów
zagrożonych osiadaniem terenu na analizowanym obszarze.

Praca będzie również obejmować pozyskanie i przetworzenie zobrazowań
radarowych w celu wyznaczenia map przemieszczeń terenu, a następnie
integrację uzyskanych wyników z danymi o pokryciu terenu z
wykorzystaniem stworzonego systemu oraz analizę i wizualizację wyników
na przykładzie wybranego obszaru badawczego.