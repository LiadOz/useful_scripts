from bs4 import BeautifulSoup
import requests
import re

INJECT_SCRIPT = -3 # the index of data injection script

def get_window_attribute(attribute_name, script):
    pattern = attribute_name + ": '(.*)'"
    return re.search(pattern, script).group(1)

def save_as_mp4(file_name, link):
    session = requests.Session()
    # using user-agent changes the page to be focused on js instead of html
    session.headers.update({'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36'})
    resp = session.get(link)
    soup = BeautifulSoup(resp.text, features='html.parser')
    inject = soup.findAll('script')[INJECT_SCRIPT].string
    url = get_window_attribute('viewMp4Url', inject)
    file_size = get_window_attribute('fileSize', inject)

    session.headers.update({'referer': link})
    r = session.get(url)
    print('Downloading ' + file_name + ' size is ' + file_size)
    with open(file_name + '.mp4', 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

def save_chat(file_name, link):
    resp = requests.get(link).text
    soup = BeautifulSoup(resp, features='html.parser')
    print('Downloading ' + file_name + ' chat')
    with open(file_name + '.txt', 'w') as f:
        f.write(soup.find('div', {'class': 'aside-chat'}).text)


file_name = input('Choose file without extension ')
with open(file_name + '.txt') as f:
    for i, link in enumerate(f.readlines()):
        save_as_mp4(file_name + '_' + str(i), link.strip())
        save_chat(file_name + '_' + str(i) + '_chat', link.strip())
