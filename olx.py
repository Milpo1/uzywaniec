import time
import requests
import re
from bs4 import BeautifulSoup
import csv

page_list =['https://www.olx.pl/elektronika/telefony/smartfony-telefony-komorkowe/iphone/']
models = []
offer_list = []
start = time.time()

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
                    
                    offer = [offer_title, offer_url, offer_price, 
                                offer_price_text[1] if len(offer_price_text) > 1 else '']
                    offer_list.append(offer)
                except:
                    pass
    
    print(f'Zakonczono pobieranie. Pobrałem {len(offer_list)} ofert w ciągu {round(time.time()-start,1)} sekund')
    if ask_prompt("Przetworzyc dane?"):
        process()
    elif ask_prompt("Zapisac surowe dane?"):  
        header = ('offer_title','offer_url','offer_price','offer_price_info')
        filename = 'data_raw.csv'
        save_csv(filename,offer_list,header) 

def process():
    models.clear()
    pattern = re.compile(' ')
    to_whitespace = re.compile('[,-]')
    to_remove = re.compile('[^\w\s]')
    model_names = ('5','5s','5c','6','6s','se2020','se2','se','7','8','x','xr','xs','11','12','13','14')
    model_info = ('pro','max','plus','mini')
    model_unmatched = 0
    for offer in offer_list:
        offer_title = offer[0].lower()
        offer_title = to_whitespace.sub(' ', offer_title)
        offer_title = to_remove.sub('', offer_title)
        found_str = pattern.split(offer_title)
        product_name = ''
        temp_product_name = ''
        for i in range(len(found_str)):
            if found_str[i] == 'iphone':
                temp_product_name = found_str[i:i+4]
        for model in model_names:
            if model in temp_product_name:
                product_name += ' '+model
                break
        for info in model_info:
            if info in temp_product_name:
                product_name += ' '+info
        models.append(product_name[1:])
        if product_name == '':
            model_unmatched+=1
    # if input("Zaktualizowac liste ofert? Y/n ").lower() == 'y':
    join_offers_with_models()
    if ask_prompt(f"Zapisac dane? \n\t{len(models)} przetworzonych ofert\n\t{model_unmatched} ofert bez modelu\n"):     
        header = ('product_model','offer_title','offer_url','offer_price','offer_price_info')
        filename = 'data_processed.csv'
        save_csv(filename,offer_list,header)
        
def join_offers_with_models():
    for i in range(len(offer_list)):
        offer_list[i].insert(0,models[i])
    
def save_csv(filename, list, header):
    try:
        with open(filename, 'w', encoding='UTF8') as f:
            writer = csv.writer(f, lineterminator='\n')

            # write the header
            writer.writerow(header)

            # write the data
            writer.writerows(list)
        print(f'Zapisano dane do pliku {filename}')
    except:
        print(f'File error: {filename}')

def load_csv(filename, list):
    offer_count = 0
    try:
        with open(filename, 'r', encoding='UTF8') as f:
            reader = csv.reader(f, lineterminator='\n')
            list.clear()
            for row in reader:
                offer_count+=1
                if offer_count == 1: continue
                list.append(row)
        print(f'Zaladowanio plik {filename} do ')
    except:
        print(f'File error: {filename}')
        
def main():
    response = ''
    while response != 'exit':
        response = input("ScrapeIt > ")
        if re.match('scrap',response):
            try:
                pages = int(response[6:])
            except:
                pages = 999
            read_web(pages)
            continue
        if re.match('load_raw',response):
            load_csv('data_raw.csv', offer_list)
            continue
        if re.match('load',response):
            load_csv('data_processed.csv', offer_list)
            continue       
        if re.match('process',response):
            process()
            continue

if __name__ == "__main__":
    main()
    