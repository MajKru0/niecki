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