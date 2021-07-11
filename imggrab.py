from typing import Union
import urllib.request
import bs4
from bs4 import BeautifulSoup
from dataclasses import dataclass
import logging
import time
import os


logging.basicConfig(filename='logs.log', level=logging.ERROR,
    format='%(asctime)s:[%(levelname)s]:%(message)s')
logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)
logger.info("start ==================================================================================")

@dataclass
class Talent:
    gen: str  # gen is not implemented yet
    name: str
    link: str
    img_urls: list[str] 

    def __repr__(self) -> str:
        return self.name


def get_html(url):
    with urllib.request.urlopen(url) as f:
        html = f.read().decode('utf-8')
    return html

def get_soup(url):
    logger.info(f'Getting source code from {url=}')
    start = time.time()
    source = get_html(url)
    soup = BeautifulSoup(source, 'html.parser')
    end = time.time()
    logger.info(f'Got source code in {end-start}s')
    return soup

def get_talents(mainpage, split_by_gen=False) -> list[Union[list[dict], dict]]:
    """ get talent names and link to their wiki pages """
    
    logger.info('Getting talents')
    logger.debug(f"{split_by_gen=}")

    all_talents = []
    tables = mainpage.find_all("table", {"class": "wikitable"})
    for table in tables:
        talents = []
        for des in table.descendants:
            if isinstance(des, bs4.element.Tag) and des.name == 'a':
                logger.debug(f"Found {des['title']}")
                talents.append({
                    'name':des['title'],
                    'link':"https://hololive.wiki"+des['href'],
                })
        talents = talents[1:] # split gen name
        if split_by_gen:
            all_talents.append(talents)
        else:
            all_talents.extend(talents)

    # azki is a special case
    if split_by_gen:
        all_talents[0][0] = {
            'name':'AZKi',
            'link':'https://hololive.wiki/wiki/AZKi'
        }
    else:
        all_talents[0] = {
        'name':'AZKi',
        'link':'https://hololive.wiki/wiki/AZKi'
    }

    logger.debug(f"{len(all_talents)} talents has been retrieved")
    return all_talents

def find_image_urls(talent) -> list:

    logger.info(f'Searching for image urls of {talent["name"]}')

    start = time.time()
    soup = get_soup(talent['link'])
    costume_div = soup.find('div', {'class':'tabbertab', 'title': 'Costumes '})

    image_urls = []
    for tag in costume_div.descendants:
        if isinstance(tag, bs4.element.Tag) and tag.name == 'a':
            try:
                if tag['class'][0] == 'image':
                    img_page = get_soup("https://hololive.wiki"+tag['href'])
                    img_div = img_page.find('div', {'class':'fullImageLink'})
                    logger.debug(f"Found image url: {img_div.a['href']}")
                    image_urls.append(img_div.a['href'])
            except:
                pass

    end = time.time()
    logger.debug(f"{len(image_urls)} images found in {end-start}s")
    return image_urls

def download_img(url, dest):
    logger.info(f"Downloading image from {url} to {dest}")
    urllib.request.urlretrieve(url, dest)

def create_dir_if_not_exists(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path)
            logger.debug(f"'{path}' created")
        except PermissionError as e:
            logger.error(f"Permission denied to {path}")

def file_amount(path):
    _, _, files = next(os.walk(path))
    logger.info(f"{len(files)} files found in {path}")
    return len(files)

# set forced argument to true to forcefully download all images, even if they are already present.
def download_all_images(talent, urls, foldername=None, forced=False):
    if not foldername:
        foldername = talent['name']
    create_dir_if_not_exists(foldername)

    if not forced:
        if file_amount(foldername) == len(urls):
            logger.warning("Images are already downloaded")
            return

    logger.info(f"Downloading all images of {talent['name']} to {foldername}")
    start = time.time()
    for i, img_url in enumerate(urls):
        download_img(img_url, f'.\\{foldername}\\{i}.png')
    end = time.time()
    logger.debug(f"{len(urls)} images has been downloaded in {end-start}s")


mainpage = get_soup('https://hololive.wiki/wiki/Main_Page')

talents = get_talents(mainpage)

urls = find_image_urls(talents[0])

download_all_images(talents[0], urls) # TODO merge arguments
