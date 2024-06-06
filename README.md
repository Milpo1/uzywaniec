# Używaniec

  Używaniec zbiera oferty z serwisu OLX i komponuje z nich bazę interesujacych Cię ofert w pliku CSV.
  
# Polecenia

  - help - wyświetl pomoc
  - scrape [n] - pobierz n stron z ofertami (brak=max)
  - process - przetwórz obecnie wczytane oferty
  - analise - analiza wczytanych ofert
  - print [n] - wypisuje n-ty wiersz bazy ofert
  - load_raw - wczytaj plik z surowymi danymi (data_raw.csv)
  - load - wczytaj plik z przetworzonymi danymi (data_processed.csv)
  - info - wypisuje stan obecnych danych
  - config - wypisuje obecną konfigurację przetwarzania
  - 
# Przykład konfiguracji

```python
main_page_url = 'https://www.olx.pl'
page_list_url = 'https://www.olx.pl/elektronika/komputery/podzespoly-i-czesci/karty-graficzne/'

omit_keyword_search = True
model_keyword = ['gpu', 'gtx', 'rtx']
model_names = [
    '1050', '1060', '1070', '1080',
    '1660', '2060', '2070', '2080',
    '3060', '3070', '3080', '3090',
    '4060', '4070', '4080', '4090'
]
model_info = [['ti'], ['super']]
model_extrainfo = [['2gb', '2'], ['3gb', '3'], ['4gb', '4'], ['6gb', '6'], ['8gb', '8'], ['12gb', '12'], ['16gb', '16'], ['32gb', '32']]
```
