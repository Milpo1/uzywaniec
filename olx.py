import time
import requests
import re
from bs4 import BeautifulSoup
import csv
import pandas as pd
page_list = ['https://www.olx.pl/elektronika/telefony/smartfony-telefony-komorkowe/iphone/']
models = []
model_unmatched = 0
model_keyword = 'iphone'
model_names = ('5','5s','5c','6','6s','se2020','se2','se','7','8','x','xr','xs','11','12','13','14')
model_info = (('pro', '#'),('max', '#'),('plus', '#'),('mini', '#'))
model_extrainfo = (('16gb','16'),('32gb','32'),('64gb','64'),('128gb','128'),('256gb','256'),('512gb','512'),('1tb','#'))
offer_list = []
start = time.time()
df_offers = pd.DataFrame(offer_list)
def ask_prompt(text) -> bool:
    if input(text + " Y/n ").lower() == 'y':  
        return True
    return False

def read_web(page_max_count):
    offer_list.clear()
    for page_count in range(1,page_max_count+1):
        print(f'Przechodze do strony {page_count}. Pobrano razem {len(offer_list)} ofert.')
        page_prompt = f'page={page_count}'
        page_url = page_list[0]+f'?'+page_prompt+'&search[order]=created_at%3Adesc'
        page = requests.get(page_url)
        
        if not re.search(page_prompt,page.url) and page_count > 1:
            break
        soup = BeautifulSoup(page.content, 'html.parser')
    
        for a in soup.find_all('a', href=True):
            if a['href'][0:9]=='/d/oferta':
                try:
                    if a.find('div', attrs={'data-testid':'adCard-featured'}):
                        continue
                    
                    offer_title_h6 = a.find('h6')
                    offer_title = offer_title_h6.text
                    
                    offer_url = a['href']
                    
                    offer_price_p = a.find('p')
                    offer_price_text = re.sub(' zł','',offer_price_p.text)
                    offer_price_text = re.sub(' ','',offer_price_text)
                    offer_price_text = re.sub(',','.',offer_price_text)
                    offer_price_text = re.split(r'[a-zA-Z]', offer_price_text, maxsplit=1)
                    offer_price = float(offer_price_text[0])
                    
                    offer = {'offer_title':offer_title, 'offer_url':offer_url, 'offer_price':offer_price, 
                                'offer_price_info' : offer_price_text[1] if len(offer_price_text) > 1 else ''}
                    offer_list.append(offer)
                except:
                    pass
    
    print(f'Zakonczono pobieranie. Pobrałem {len(offer_list)} ofert w ciągu {round(time.time()-start,1)} sekund')
    if ask_prompt("Przetworzyc dane?"):
        process()
        if ask_prompt(f"Zapisac dane? \n\t{len(models)} przetworzonych ofert\n\t{model_unmatched} ofert bez modelu\n"):     
            join_offers_with_models()
            filename = 'data_processed.csv'
            save_csv(filename,offer_list)
    elif ask_prompt("Zapisac surowe dane?"):
        filename = 'data_raw.csv'
        save_csv(filename,offer_list) 

def process():
    global model_unmatched
    models.clear()
    pattern = re.compile(' ')
    to_whitespace = re.compile('[,-/]')
    to_remove = re.compile('[^\w\s]')
    model_unmatched = 0
    for offer in offer_list:
        offer_title = offer['offer_title'].lower()
        offer_title = to_whitespace.sub(' ', offer_title)
        offer_title = to_remove.sub('', offer_title)
        found_str = pattern.split(offer_title)
        model_name = ''
        model_details = ''
        for i in range(len(found_str)):
            if found_str[i] == model_keyword:
                model_name += model_keyword
                break
        if model_name != '':
            for model in model_names:
                if model in found_str:
                    model_name += ' ' + model
                    break
            for info in model_info:
                for synonim in info:
                    if synonim in found_str:
                        model_name += ' ' + info[0]
                        break
            for details in model_extrainfo:
                for detail in details:
                    if detail in found_str:
                        model_details += ' ' + details[0]
                        break           
        if model_name == model_keyword:
            model_name = 'NA'
            model_unmatched+=1
        if model_details == '':
            model_details = ' NA'
        models.append((model_name, model_details[1:]))
    compile_data_frame()
      
def compile_data_frame():
    global df_offers
    df_offers = pd.DataFrame(offer_list)
    df_offers = df_offers.astype({'offer_price':'float'})
    df_offers = df_offers.astype({'offer_price':'int'})
  
def join_offers_with_models():
    for i in range(len(offer_list)):
        offer_list[i]['model_name'] = models[i][0]
        offer_list[i]['model_details'] = models[i][1]
    
def save_csv(filename, list):
    try:
        keys = list[0].keys()

        with open(filename, 'w', encoding='UTF8') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(list)
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
            print(f'Zaladowanio plik {filename}')
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
            url = model_data[model_data.offer_price == 950].offer_url
            print(url.values[0])
            print(type(url))
        except:
            return
        
def info(update = False):
    if update: 
        process()
    print(f"\t{len(offer_list)} zaladowanych ofert\n")
    print(f"\t{len(models)} przetworzonych ofert\n\t{model_unmatched} ofert bez modelu\n")

def main():
    global offer_list
    global models
    global model_unmatched
    response = ''
    while response != 'exit':
        try:
            response = input("ScrapeIt > ")
        except:
            return
        if re.match('info',response):
            if re.match('info update',response):
                info(True)
                continue
            info()
            continue
        if re.match('scrap', response):
            try:
                pages = int(response[6:])
            except:
                pages = 999
            read_web(pages)
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
            process()
            if ask_prompt(f"Zapisac dane? \n\t{len(models)} przetworzonych ofert\n\t{model_unmatched} ofert bez modelu\n"):     
                join_offers_with_models()
                filename = 'data_processed.csv'
                save_csv(filename, offer_list)
            continue
        if re.match('analise', response):
            analise()
            continue

if __name__ == "__main__":
    offer_list = load_csv('data_processed.csv')
    analise()
    main()
    