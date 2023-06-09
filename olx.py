import time
import requests
import re
from bs4 import BeautifulSoup
import csv

page_list =['https://www.olx.pl/elektronika/telefony/smartfony-telefony-komorkowe/iphone/']
offer_list = []
start = time.time()

def read_web(page_max_count):
    
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
                    
                    offer = (offer_title, offer_url, offer_price, 
                                offer_price_text[1] if len(offer_price_text) > 1 else '')
                    offer_list.append(offer)
                except:
                    pass
            
    print(f'Zakonczono pobieranie. Pobrałem {len(offer_list)} ofert w ciągu {round(time.time()-start,1)} sekund')
    if input("Zapisac dane? Y/n ").lower() == 'y':     
        header = ('offer_title','offer_url','offer_price','offer_price_info')
        header_info = ('',page_list[0],'','')
        filename = 'data.csv'
        with open(filename, 'w', encoding='UTF8') as f:
            writer = csv.writer(f, lineterminator='\n')

            # write the header
            writer.writerow(header)

            # write the data
            writer.writerows(offer_list)
        print(f'Zapisano dane do pliku {filename}')

def main():
    response = ''
    while response != 'exit':
        response = input("> ")
        if response[0:5] == 'scrap':
            read_web(int(response[6:]))
    

if __name__ == "__main__":
    main()
    