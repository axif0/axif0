import requests
from bs4 import BeautifulSoup

def test_codeforces():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get('https://codeforces.com/profile/asif2001', headers=headers)
        print('Response status:', response.status_code)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try different selectors
        print('\nTrying different selectors:')
        
        # Method 1: info div
        info_div = soup.find('div', class_='info')
        print('\n1. Info div found:', bool(info_div))
        if info_div:
            print('Info div text:', info_div.get_text()[:200])
        
        # Method 2: user-info div
        user_info = soup.find('div', class_='user-info')
        print('\n2. User info div found:', bool(user_info))
        if user_info:
            print('User info text:', user_info.get_text()[:200])
        
        # Method 3: main-info div
        main_info = soup.find('div', class_='main-info')
        print('\n3. Main info div found:', bool(main_info))
        if main_info:
            print('Main info text:', main_info.get_text()[:200])
        
        # Save HTML for inspection
        with open('cf_response.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
            print('\nSaved HTML response to cf_response.html')
            
    except Exception as e:
        print('Error:', str(e))

if __name__ == '__main__':
    test_codeforces() 