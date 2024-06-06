import time
import requests
import re
from bs4 import BeautifulSoup
import csv
import pandas as pd

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

curse_words = []
offer_list = []
models = []
model_recognised = 0
model_unrecognised = []
model_unmatched = []
start = time.time()
df_offers = pd.DataFrame(offer_list)


def help():
    help_text = """
---------------------------POMOC---------------------------
Uzywaniec pozwoli Ci zebrac dane ofert z serwisu OLX
i skomponowac na ich podstawie baze danych interesujacych Cie ofert.
Obsluguje pliki csv.

help - jestes tutaj
scrape [n] - scrapuj n stron z ofertami (jesli brak, max) (zapyta o przetworzenie)
process - przetworz obecnie wczytane oferty
analise - analiza wczytanych ofert
print [n] - wypisuje n-ty wiersz bazy ofert
    print unmatched
    print unrec
load_raw - wczytaj plik z surowymi danymi (data_raw.csv)
load - wczytaj plik z przetworzonymi danymi (data_processed.csv)
info - wypisuje stan obecnych danych
config - wypisuje obecna konfiguracje przetwarzania
"""
    print(help_text)


def ask_prompt(text) -> bool:
    return input(text + " Y/n ").lower() == 'y'


def read_olx(page_max_count):
    global offer_list
    offer_list.clear()
    for page_count in range(1, page_max_count + 1):
        print(f'Przechodze do strony {page_count}. Pobrano razem {len(offer_list)} ofert.')
        page_url = f'{page_list_url}?page={page_count}&search[order]=created_at%3Adesc'
        page = requests.get(page_url)

        if not re.search(f'page={page_count}', page.url) and page_count > 1:
            break

        soup = BeautifulSoup(page.content, 'html.parser')
        div_list = soup.find_all('div', attrs={'data-cy':'ad-card-title'})
        for d in div_list:
            a = d.find('a')
            if a['href'].startswith('/d/oferta'):
                try:
                    if a.find('div', attrs={'data-testid': 'adCard-featured'}):
                        continue

                    offer_title = a.find('h6').text
                    offer_url = a['href']
                    offer_price_text = re.sub('[ zł,]', '', d.find('p').text).replace(' ', '')
                    offer_price = float(re.split(r'[a-zA-Z]', offer_price_text)[0])
                    offer_delivery = 1 if d.find('p').find('svg') else 0

                    item_condition = 'NA'
                    if a.find('span', attrs={'title': 'Używane'}):
                        item_condition = 'used'
                    elif a.find('span', attrs={'title': 'Nowe'}):
                        item_condition = 'new'
                    elif a.find('span', attrs={'title': 'Uszkodzone'}):
                        item_condition = 'broken'

                    offer = {
                        'id': len(offer_list) + 1, 'offer_title': offer_title,
                        'offer_url': main_page_url + offer_url, 'offer_price': offer_price,
                        'offer_price_info': re.split(r'[a-zA-Z]', offer_price_text)[1] if len(re.split(r'[a-zA-Z]', offer_price_text)) > 1 else 'NA',
                        'offer_status': 'active', 'model_name': 'NA', 'model_details': 'NA',
                        'olx_delivery': offer_delivery, 'creation_date': 'NA', 'item_condition': item_condition,
                        'offer_location': 'NA', 'seller_type': 'NA', 'seller_name': 'NA',
                        'view_count': 'NA', 'offer_id': 'NA', 'uzywaniec_count': '0'
                    }
                    offer_list.append(offer)
                except Exception as e:
                    print(f'Error processing offer: {e}')
                    continue

    print(f'Zakonczono pobieranie. Pobrałem {len(offer_list)} ofert w ciągu {round(time.time()-start, 1)} sekund')
    if ask_prompt("Zapisac surowe dane?"):
        save_csv('data_raw.csv', offer_list)
    if ask_prompt("Przetworzyc dane?"):
        process(offer_list)


def process(offer_list_requested):
    global model_unmatched, model_unrecognised, model_recognised, models
    model_unmatched.clear()
    model_unrecognised.clear()
    model_recognised = 0
    models.clear()
    pattern = re.compile(' ')
    to_whitespace = re.compile('[\',-/]')
    to_remove = re.compile('[^\w\s]')

    for offer in offer_list_requested:
        offer_title = offer['offer_title'].lower()
        offer_title = to_whitespace.sub(' ', offer_title)
        offer_title = to_remove.sub('', offer_title)
        
        offer_title = re.sub(model_keyword[0], f' {model_keyword[0]} ', offer_title)
        for info in model_info:
            offer_title = re.sub(info[0], f' {info[0]} ', offer_title)
        
        found_str = pattern.split(offer_title)
        model_name = ''
        model_details = ''
        
        for keyword in model_keyword:
            if keyword in found_str or omit_keyword_search:
                model_name = model_keyword[0]
                break

        if model_name:
            for model in model_names:
                if model in found_str:
                    model_name += f' {model}'
                    break

            if model_name != model_keyword[0]:
                for info in model_info:
                    if info[0] in found_str:
                        model_name += f' {info[0]}'
                        break

                for details in model_extrainfo:
                    if any(detail in found_str for detail in details):
                        model_details += f' {details[0]}'
                        break

        found_curse_words = any(re.search(curse_word, offer_title) for curse_word in curse_words)
        
        if not model_name or found_curse_words:
            model_name = 'NA'
            model_unrecognised.append(offer)
        elif model_name == model_keyword[0]:
            model_name = 'NA'
            model_unmatched.append(offer)
        else:
            model_recognised += 1

        if not model_details:
            model_details = ' NA'
        
        models.append((model_name, model_details.strip()))

    if len(models) == len(offer_list):
        join_offers_with_models()
        compile_data_frame()
        print_info()
        if ask_prompt("Zapisac dane?"):
            save_csv('data_processed.csv', offer_list)


def compile_data_frame():
    global df_offers
    df_offers = pd.DataFrame(offer_list)
    df_offers['offer_price'] = df_offers['offer_price'].astype(float).astype(int)


def join_offers_with_models():
    for i, model in enumerate(models):
        offer_list[i]['model_name'] = model[0]
        offer_list[i]['model_details'] = model[1]


def save_csv(filename, dict_list):
    try:
        keys = dict_list[0].keys()
        with open(filename, 'w', encoding='UTF8', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(dict_list)
            print(f'Zapisano dane do pliku {filename}')
    except Exception as e:
        print(f'File error: {filename}\n\t{e}')


def load_csv(filename):
    try:
        with open(filename, 'r', encoding='UTF8') as input_file:
            dict_reader = csv.DictReader(input_file)
            current_list = list(dict_reader)
            print(f'Zaladowano plik {filename}')
            return current_list
    except Exception as e:
        print(f'File error: {filename}\n\t{e}')
        return []


def analise():
    if df_offers.empty:
        compile_data_frame()
    while True:
        response = input('Podaj model (exit to quit): ').lower()
        if response == 'exit':
            break
        model_data = df_offers[df_offers.model_name == response]
        if not model_data.empty:
            print(model_data.describe())
        else:
            print(f'Brak danych dla modelu: {response}')


def print_info(update=False):
    if update:
        process(offer_list)
    print(f"Podsumowanie:\n\t{len(offer_list)} zaladowanych ofert\n\t{model_recognised} rozpoznanych ofert\n\t{len(model_unmatched)} ofert bez modelu\n\t{len(model_unrecognised)} ofert nierozpoznanych")


def config_info():
    print(f"main_page_url: {main_page_url}\npage_list_url: {page_list_url}")
    print(f"model_keyword: {model_keyword}\nmodel_names: {model_names}\nmodel_info: {model_info}\nmodel_extrainfo: {model_extrainfo}")


def print_row(offers):
    for offer in offers:
        print(f'{offer}\n')


def main():
    global offer_list
    offer_list = load_csv('data_processed.csv')
    while True:
        response = input("$ Uzywaniec > ").strip()
        if response == 'exit':
            break
        if response == 'help':
            help()
        elif response.startswith('print'):
            if response == 'print unmatched':
                print_row(model_unmatched)
            elif response == 'print unrec':
                print_row(model_unrecognised)
            else:
                try:
                    index = int(response.split()[1]) - 1
                    print_row([offer_list[index]])
                except (IndexError, ValueError) as e:
                    print(e)
        elif response == 'config':
            config_info()
        elif response == 'info':
            print_info()
        elif response == 'info update':
            print_info(update=True)
        elif response.startswith('scrap'):
            try:
                pages = int(response.split()[1])
            except (IndexError, ValueError):
                pages = 999
            read_olx(pages)
        elif response == 'load_raw':
            offer_list = load_csv('data_raw.csv')
        elif response == 'load':
            offer_list = load_csv('data_processed.csv')
        elif response == 'save':
            save_csv('data_processed.csv', offer_list)
        elif response == 'process':
            process(offer_list)
        elif response == 'analise':
            analise()


if __name__ == "__main__":
    main()
