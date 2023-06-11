import time
import requests
import re
from bs4 import BeautifulSoup
import csv
import pandas as pd

main_page_url = 'https://www.olx.pl'
# page_list_url = 'https://www.olx.pl/elektronika/telefony/smartfony-telefony-komorkowe/iphone/'
page_list_url = 'https://www.olx.pl/elektronika/komputery/podzespoly-i-czesci/karty-graficzne/'

# omit_keyword_search = False
# model_keyword = ['iphone','iphon','iphony','phone','ip']
# model_names = ['3','3g','4','4s','5','5s','5c','6','6s','se2020','se2','se','7','8','x','xr','xs','11','12','13','14']
# model_info = [['pro'],['max'],['plus'],['mini']]
# model_extrainfo = [['16gb','16'], ['32gb','32'], ['64gb','64'], ['128gb','128'], ['256gb','256'], ['512gb','512'], ['1tb']]

omit_keyword_search = True
model_keyword = ['gpu','gtx','rtx']
model_names = ['1050','1060','1070','1080',
               '1660','2060','2070','2080',
               '3060','3070','3080','3090',
               '4060','4070','4080','4090'
                ]
model_info = [['ti'],['super']]
model_extrainfo = [['2gb','2'], ['3gb','3'], ['4gb','4'], ['6gb','6'], ['8gb','8'], ['12gb','12'], ['16gb','16'], ['32gb','32']]

curse_words = []
offer_list = []
models = []
model_recognised = 0
model_unrecognised = []
model_unmatched = []
start = time.time()
df_offers = pd.DataFrame(offer_list)

def help():
    print("\n---------------------------POMOC---------------------------")
    print("Uzywaniec pozwoli Ci zebrac dane ofert z serwisu OLX")
    print("i skomponowac na ich podstawie baze danych interesujacych Cie ofert.\nObsluguje pliki csv.\n")
    print("help - jestes tutaj")
    print("scrape [n] - scrapuj n stron z ofertami (jesli brak, max) (zapyta o przetworzenie)")
    print("process - przetworz obecnie wczytane oferty")
    print("analise - analiza wczytanych ofert")
    print("print [n] - wypisuje n-ty wiersz bazy ofert")
    print("\tprint unmatched\n\tprint unrec")
    print("load_raw - wczytaj plik z surowymi danymi (data_raw.csv)")
    print("load - wczytaj plik z przetworzonymi danymi (data_processed.csv)")
    print("info - wypisuje stan obecnych danych")
    print("config - wypisuje obecna konfiguracje przetwarzania\n")
    
def ask_prompt(text) -> bool:
    if input(text + " Y/n ").lower() == 'y':  
        return True
    return False

def read_olx(page_max_count):
    offer_list.clear()
    for page_count in range(1,page_max_count+1):
        print(f'Przechodze do strony {page_count}. Pobrano razem {len(offer_list)} ofert.')
        page_prompt = f'page={page_count}'
        page_url = page_list_url+f'?'+page_prompt+'&search[order]=created_at%3Adesc'
        page = requests.get(page_url)
        
        if not re.search(page_prompt,page.url) and page_count > 1:
            break
        soup = BeautifulSoup(page.content, 'html.parser')
    
        for a in soup.find_all('a', href=True):
            if a['href'][0:9]=='/d/oferta':
                try:
                    # Omit featured offers
                    if a.find('div', attrs={'data-testid':'adCard-featured'}):
                        continue
                    
                    # Offer title
                    offer_title_h6 = a.find('h6')
                    offer_title = offer_title_h6.text
                    
                    # Offer url
                    offer_url = a['href']
                    
                    # Offer price scrapin
                    offer_price_p = a.find('p')
                    offer_price_text = re.sub(' zł','',offer_price_p.text)
                    offer_price_text = re.sub(' ','',offer_price_text)
                    offer_price_text = re.sub(',','.',offer_price_text)
                    offer_price_text = re.split(r'[a-zA-Z]', offer_price_text, maxsplit=1)
                    offer_price = float(offer_price_text[0])
                    
                    # Detect OLX delivery
                    offer_delivery = 0
                    if offer_price_p.find('svg'):
                        offer_delivery = 1
                    
                    item_condition = 'NA'
                    if a.find('span', attrs={'title':'Używane'}):
                        item_condition = 'used'
                    elif a.find('span', attrs={'title':'Nowe'}):
                        item_condition = 'new'
                    elif a.find('span', attrs={'title':'Uszkodzone'}):
                        item_condition = 'broken'
                    
                    # Offer completing
                    offer = {   'id' : len(offer_list)+1, 'offer_title':offer_title, 'offer_url': main_page_url + offer_url, 
                                'offer_price':offer_price, 'offer_price_info' : offer_price_text[1] if len(offer_price_text) > 1 else 'NA',
                                'offer_status' : 'active', 'model_name' : 'NA', 'model_details' : 'NA',
                                'olx_delivery' : offer_delivery, 'creation_date' : 'NA', 'item_condition' : item_condition,
                                'offer_location' : 'NA', 'seller_type' : 'NA', 'seller_name' : 'NA',
                                'view_count' : 'NA', 'offer_id' : 'NA', 'uzywaniec_count' : '0'
                            }
                    
                    # Append offer to offer list
                    offer_list.append(offer)
                except:
                    pass
    
    print(f'Zakonczono pobieranie. Pobrałem {len(offer_list)} ofert w ciągu {round(time.time()-start,1)} sekund')
    if ask_prompt("Zapisac surowe dane?"):
        filename = 'data_raw.csv'
        save_csv(filename,offer_list) 
    if ask_prompt("Przetworzyc dane?"):
        process(offer_list)

def refresh_offer(offer):
    offer_url = offer['offer_url']
    offer = requests.get(offer_url)
    
def process(offer_list_requested):
    global model_unmatched
    global model_unrecognised
    global model_recognised
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
        
        # Separate keyword and model detail phrases (ex. "iiphone7promax" -> "i iphone 7 pro max ")
        offer_title = re.sub(model_keyword[0],f' {model_keyword[0]} ',offer_title)
        for info in model_info:
            offer_title = re.sub(info[0],f' {info[0]} ',offer_title)
        found_str = pattern.split(offer_title)
        model_name = ''
        model_details = ''
        
        # Look for keyword
        for i in range(len(found_str)):
            for keyword in model_keyword:
                if found_str[i] == keyword or omit_keyword_search:
                    model_name += model_keyword[0]
                    break
            if model_name != '': 
                break
        
        # Proceed if keyword phrase is found
        if model_name != '':
            # Look for model name
            for model in model_names:
                if model in found_str:
                    model_name += ' ' + model
                    break
            # Proceed if model name found:
            if model_name != model_keyword[0]:
                # Look for model info 
                for info in model_info:
                    for synonim in info:
                        if synonim in found_str:
                            model_name += ' ' + info[0]
                            break
                # Look for model info details
                for details in model_extrainfo:
                    for detail in details:
                        if detail in found_str:
                            model_details += ' ' + details[0]
                            break   
                 
        # Mark offer as unrecognised if curse word found   
        found_curse_words = None
        for curse_word in curse_words:
            found_curse_words = re.search(curse_word,offer_title)
            if not found_curse_words is None:
                break
        
        # Fill with NA's and update counters
        if model_name == '' or not found_curse_words is None:
            model_name = 'NA'
            model_unrecognised.append(offer)
        elif model_name == model_keyword[0]:
            model_name = 'NA'
            model_unmatched.append(offer)
        else:
            model_recognised+=1
            
        if model_details == '':
            model_details = ' NA'
        
        # Add to model list
        models.append((model_name, model_details[1:]))
    if len(models) == len(offer_list):
        join_offers_with_models()
        compile_data_frame()
        print_info()
        if ask_prompt(f"Zapisac dane?"):     
            filename = 'data_processed.csv'
            save_csv(filename, offer_list)
      
def compile_data_frame():
    global df_offers
    df_offers = pd.DataFrame(offer_list)
    df_offers = df_offers.astype({'offer_price':'float'})
    df_offers = df_offers.astype({'offer_price':'int'})
  
def join_offers_with_models():
    for i in range(len(offer_list)):
        offer_list[i]['model_name'] = models[i][0]
        offer_list[i]['model_details'] = models[i][1]
    
def save_csv(filename, dict_list):
    try:
        keys = dict_list[0].keys()

        with open(filename, 'w', encoding='UTF8') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(dict_list)
            print(f'Zapisano dane do pliku {filename}')
    except Exception as e:
        print(f'File error: {filename}\n\t')
        print(e)

def load_csv(filename):
    try:
        with open(filename, 'r', encoding='UTF8') as input_file:
            current_list = []
            dict_reader = csv.DictReader(input_file)
            current_list = list(dict_reader)
            print(f'Zaladowano plik {filename}')
            return current_list
    except Exception as e:
        print(f'File error: {filename}\n\t')
        print(e)
        
def analise():
    if df_offers.empty:
        compile_data_frame()
    response = ''
    while response != 'exit':
        try:
            response = input('Podaj model: ')
            response = response.lower()
            # if response in model_names:
            model_data = df_offers[df_offers.model_name == response]
            print(model_data.describe())
        except:
            return
        
def print_info(update = False):
    if update: 
        process()
    print(f"Podsumowanie:")
    print(f"\t{len(offer_list)} zaladowanych ofert")
    print(f"\t{model_recognised} rozpoznanych ofert\n\t{len(model_unmatched)} ofert bez modelu\n\t{len(model_unrecognised)} ofert nierozpoznanych")
    
def config_info():
    print(f"main_page_url: {main_page_url}\npage_list_url: {page_list_url}")
    print(f"model_keyword: {model_keyword}\nmodel_names: {model_names}\nmodel_info: {model_info}\nmodel_extrainfo: {model_extrainfo}")

def print_row(offer_list):
    for offer in offer_list:
        print(f'{offer}\n')

def main():
    global offer_list
    global models
    global model_unmatched
    response = ''
    while response != 'exit':
        try:
            response = input("$ Uzywaniec > ")
        except:
            return
        if re.match('help', response):
            help()
            continue
        if re.match('print', response):
            if re.match('print unmatched', response):
                print_row(model_unmatched) 
                continue
            if re.match('print unrec', response):
                print_row(model_unrecognised) 
                continue            
            try:
                index = int(response[6:])-1
                offer = offer_list[index]
                print_row([offer])      
            except Exception as e:
                print(e)
            continue
        if re.match('config', response):
            config_info()
            continue        
        if re.match('info', response):
            if re.match('info update', response):
                print_info(True)
                continue
            print_info()
            continue
        if re.match('scrap', response):
            try:
                pages = int(response[6:])
            except:
                pages = 999
            read_olx(pages)
            continue
        if re.match('load_raw', response):
            offer_list = load_csv('data_raw.csv')
            continue
        if re.match('load', response):
            offer_list = load_csv('data_processed.csv')
            continue       
        if re.match('save', response):
            if len(models) > 0:
                save_csv('data_processed.csv', offer_list)
            continue    
        if re.match('process', response):
            try:
                row = int(response[8:])

                print(f'Processing row {row}...')
                offer_index = row-1
                process([offer_list[offer_index]])
                print(f'Row {row} processed successfully')
                continue
            except:
                pass
            process(offer_list)
            continue
        if re.match('analise', response):
            analise()
            continue

if __name__ == "__main__":
    offer_list = load_csv('data_processed.csv')
    # analise()
    main()
    