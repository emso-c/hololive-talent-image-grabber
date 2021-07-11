import urllib.request
import bs4
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
import logging
import time
import os
import json


logging.basicConfig(filename='logs.log', level=logging.ERROR,
    format='%(asctime)s:[%(levelname)s]:%(message)s')
logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)
logger.info("start ==================================================================================")

@dataclass
class Talent:
    #gen: str  # gen is not implemented yet
    name: str
    link: str
    img_urls: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return "Talent info\nName: {}\nLink: {}\nimage_urls:\n{}".format(
            self.name,
            self.link,
            '\n'.join(self.img_urls)
        )
    
    @property
    def dict_form(self) -> dict:
        return {
            'name':self.name,
            'link':self.link,
            'img_urls':self.img_urls
        }


class utils():
    def download_img(url, dest):
        logger.info(f"Downloading image from {url} to {dest}")
        urllib.request.urlretrieve(url, dest)

    def create_dir_if_not_exists(path):
        if not os.path.exists(path):
            try:
                os.makedirs(path)
                logger.debug(f"'{path}' created")
            except PermissionError as e:
                logger.error(f"Permission denied to {path}, consider trying another path")

    def file_amount(path):
        _, _, files = next(os.walk(path))
        logger.info(f"{len(files)} files found in {path}")
        return len(files)


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

def get_talents(mainpage) -> list[Talent]:
    """ get talent names and link to their wiki pages """

    logger.info('Getting talents')

    all_talents = []
    tables = mainpage.find_all("table", {"class": "wikitable"})
    for table in tables:
        talents = []
        for des in table.descendants:
            if isinstance(des, bs4.element.Tag) and des.name == 'a' and des['title']:
                logger.debug(f"Found {des['title']}")
                talents.append(Talent(
                    name=des['title'],
                    link='https://hololive.wiki'+des['href'],
                ))
        talents = talents[1:] # split gen name
        all_talents.extend(talents)

    # azki is a special case
    all_talents[0] = Talent(
        name='AZKi',
        link='https://hololive.wiki/wiki/AZKi',
    )

    logger.debug(f"{len(all_talents)} talents has been retrieved")
    return all_talents

def find_image_urls_of(talent):
    logger.info(f'Searching for image urls of {talent.name}')

    start = time.time()
    soup = get_soup(talent.link)
    costume_div = soup.find('div', {'class':'tabbertab', 'title': 'Costumes '})
    for tag in costume_div.descendants:
        if isinstance(tag, bs4.element.Tag) and tag.name == 'a':
            try:
                if tag['class'][0] == 'image':
                    img_page = get_soup("https://hololive.wiki"+tag['href'])
                    img_div = img_page.find('div', {'class':'fullImageLink'})
                    logger.debug(f"Found image url: {img_div.a['href']}")
                    talent.img_urls.append(img_div.a['href'])
            except:
                pass

    end = time.time()
    logger.debug(f"{len(talent.img_urls)} images found in {end-start}s")

# set forced argument to true to forcefully download all images, even if they are already present.
def download_all_images_of(talent, foldername=None, forced=False):
    if not foldername:
        foldername = 'Images'
    utils.create_dir_if_not_exists(foldername)
    path = foldername+'\\'+talent.name
    utils.create_dir_if_not_exists(path)
    logger.info(f"Downloading all images of {talent.name} to {path}")
    
    if not forced:
        if utils.file_amount(path) == len(talent.img_urls):
            logger.warning("Images are already downloaded")
            return

    start = time.time()
    for i, img_url in enumerate(talent.img_urls):
        utils.download_img(img_url, f'.\\{path}\\{i}.png')
    end = time.time()
    logger.debug(f"{len(talent.img_urls)} images has been downloaded in {end-start}s")



def import_talents(path):
    logger.info(f'Importing talents to {path}')
    pass

def export_talents(talents, path='./talents.json'):
    logger.info(f'Exporting talents to {path}')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(json.dumps([talent.dict_form for talent in talents], ensure_ascii=False, indent=4))

if __name__ == '__main__':
    mainpage = get_soup('https://hololive.wiki/wiki/Main_Page')
    talents = get_talents(mainpage)

    for talent in talents:
        find_image_urls_of(talent)

    export_talents(talents)

    for talent in talents:
        download_all_images_of(talent)

