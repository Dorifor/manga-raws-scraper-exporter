import requests
from bs4 import BeautifulSoup as bs4
import os
from typing import TypedDict, List, Tuple
import time
from logger import log
from threading import Thread
import json
from settings import Settings


SEARCH_URL = "https://hachiraw.com/search?keyword="
DOWNLOAD_INTERVAL = 0.1  # in seconds


class Manga(TypedDict):
    title: str
    author: str
    artist: str
    description: str
    genre: List[str]
    chapters: Tuple[str, str]  # chapter_name, chapter_link


def remove_raw_free(string: str) -> str:
    return string.replace("(Raw - Free)", "").strip()


def remove_illegal_characters(string: str) -> str:
    invalid = '<>:"/\|?* '
    for char in invalid:
        string = string.replace(char, '')
    return string


# Returns ([manga_title, manga_link, manga_img_url], previous_page_link, next_page_link)
def request_search(query: str, isPaginationLink: bool) -> Tuple[List[Tuple[str, str, str]], str, str]:
    url = query if isPaginationLink else SEARCH_URL + query
    page = requests.get(url)
    soup = bs4(page.content, "html.parser")
    manga_list = soup.select(".manga-item .thumb > a")
    manga_list = list(
        map(lambda manga: (remove_raw_free(manga["title"]), manga['href'], manga.img['data-src']), manga_list))
    previous_page = soup.select(".pagination .prev a")
    previous_page = previous_page[0]['href'] if previous_page else None
    next_page = soup.select(".pagination .next a")
    next_page = next_page[0]['href'] if next_page else None
    return (manga_list, previous_page, next_page)


class AsyncSearch(Thread):
    def __init__(self, query: str, isPaginationLink: bool, onfinish):
        super().__init__()
        self.onfinish_callback = onfinish
        self.query = query
        self.isPaginationLink = isPaginationLink

    def run(self) -> None:
        manga_data = request_search(self.query, self.isPaginationLink)
        self.onfinish_callback(manga_data)


def request_chapter_data(url: str) -> List[str]:
    page = requests.get(url)
    soup = bs4(page.content, "html.parser")

    chapter_pages = soup.select("div.chapter-page > img")
    chapter_pages = list(map(lambda page: page['src'], chapter_pages))
    return chapter_pages


class AsyncDownload(Thread):
    def __init__(self, manga_data: Manga, onfinish, onstep):
        super().__init__()
        self.shoud_download = True
        self.manga_data = manga_data
        self.onfinish_callback = onfinish
        self.onstep_callback = onstep
        self.details_dict = {
            "title": manga_data["title"],
            "author": manga_data["author"],
            "artist": manga_data["artist"],
            "description": manga_data["description"],
            "genre": manga_data["genre"],
            "status": 0,
            "_status values": ["0 = Unknown", "1 = Ongoing", "2 = Completed", "3 = Licensed", "4 = Publishing finished",
                               "5 = Cancelled", "6 = On hiatus"]
        }

    def run(self) -> None:
        download_path = Settings().downloads_directory + "/"
        if not os.path.exists(download_path): os.mkdir(download_path)
        manga_path = download_path + remove_illegal_characters(self.manga_data['title'])
        if not os.path.exists(manga_path): os.mkdir(manga_path)
        details_path = manga_path + "/details.json"

        if not os.path.exists(details_path):
            with open(details_path, "w") as details_file:
                json.dump(self.details_dict, details_file)

        for chapter in self.manga_data['chapters']:
            if not self.shoud_download: break
            chapter_path = manga_path + "/" + chapter[0]
            if os.path.exists(chapter_path): continue
            os.mkdir(chapter_path)
            pages = request_chapter_data(chapter[1])
            name_format = '{:0' + str(len(str(len(pages)))) + 'd}'  # 0-9 / 00-99 / 000-999 / ...
            for i, page in enumerate(pages):
                if not self.shoud_download: break
                self.onstep_callback(f"{chapter[0]} ({i+1}/{len(pages)+1})")
                log("Requesting: " + page)
                headers = {'Referer': "https://hachiraw.com/"}
                page_img_content = requests.get(page, headers=headers).content
                page_path = chapter_path + "/" + name_format.format(i) + ".jpg"
                open(page_path, 'wb').write(page_img_content)
                time.sleep(Settings().download_rate)  # otherwise it's pure DDoS, big nono
        self.onfinish_callback()

    def stop(self):
        self.shoud_download = False


def request_manga_data(url) -> Manga:
    page = requests.get(url)
    soup = bs4(page.content, "html.parser")  # same parser as default python

    log(soup.title.text)

    manga_title = remove_raw_free(soup.title.text)
    manga_author = soup.select("div.authors-content > a")
    manga_author = manga_author[0].string if manga_author else ""
    manga_artist = soup.select("div.artists-content > a")
    manga_artist = manga_artist[0].string if manga_artist else ""
    manga_description = soup.select("div.dsct > p")[0].string or "あらすじがない"  # no desc
    manga_genres = soup.select("div.genres-content > a")
    manga_genres = list(map(lambda genre: genre.string, manga_genres))

    manga_chapters = soup.select("ul.list.row-content-chapter a.chapter-name")
    manga_chapters = list(map(lambda chapter: (chapter.contents[0], chapter['href']), manga_chapters))
    manga_chapters.reverse()

    log("title: ", manga_title)
    log("author: ", manga_author)
    log("artist: ", manga_artist)
    log("description: ", manga_description)
    log("genre: ", manga_genres)
    log("chapters: ", manga_chapters)

    return {
        "title": manga_title,
        "author": manga_author,
        "artist": manga_artist,
        "description": manga_description,
        "genre": manga_genres,
        "chapters": manga_chapters
    }
