import customtkinter as tk
import requests
from scraper import request_search, request_manga_data, request_chapter_data, Manga, create_folder_structure_and_fill_chapters
from PIL import Image, ImageTk, ImageOps, ImageFilter
from typing import Tuple, List
from tkinter import font
from time import sleep
from threading import Thread

tk.set_appearance_mode("System")
tk.set_default_color_theme("dark-blue")

MEIRYO_FONT = None
NSFW = False


def get_manga_CTkImage(img_url: str, size: Tuple[int, int] = (90, 120)) -> tk.CTkImage:
    headers = {'Referer': "https://hachiraw.com/"}
    img_raw = requests.get(img_url, headers=headers, stream=True).raw
    resized_image = None
    try:
        img = Image.open(img_raw)
        if not NSFW: img = img.filter(ImageFilter.GaussianBlur(15))
        resized_image = ImageOps.fit(img, size=(size[0], size[1]))
    except:
        resized_image = ImageOps.fit(Image.linear_gradient("L"), size=(size[0], size[1]))
    return tk.CTkImage(light_image=resized_image, size=(size[0], size[1]))


class MangaSearchFrame(tk.CTkScrollableFrame):
    def __init__(self, master, mangas: List[Tuple[str, str, str]]):
        super().__init__(master)
        self.mangas = mangas

        for i, manga in enumerate(mangas):
            manga_result_frame = MangaResultFrame(self, title=manga[0], manga_url=manga[1], image_url=manga[2])
            manga_result_frame.grid(row=i, column=0, padx=10, pady=10, sticky="we")


class MangaDetailsChaptersFrame(tk.CTkScrollableFrame):
    def __init__(self, master, chapters: List[Tuple[str, str]]):
        super().__init__(master)
        self.parent = master
        self.checked_chapters = set()
        self.checkboxes = {}

        checkbox_font = tk.CTkFont(size=14, family="Meiryo")

        for i, chapter in enumerate(chapters):
            self.checkboxes[i] = tk.CTkCheckBox(self, text=chapter[0], onvalue=(chapter[0], chapter[1]), offvalue=None,
                                                command=lambda c=(chapter[0], chapter[1]): self.on_checkbox_checked(chapter_info=c),
                                                font=checkbox_font) # lambda i, _l are a workaround, if not there the values are the last one's
            self.checkboxes[i].grid(row=i, column=0, columnspan=3, padx=10, pady=10, sticky="e")

    def on_checkbox_checked(self, chapter_info: Tuple[str, str]):
        if chapter_info in self.checked_chapters:
            self.checked_chapters.remove(chapter_info)
        else:
            self.checked_chapters.add(chapter_info)
        if len(self.checked_chapters) > 0: self.parent.download_button.configure(state="normal")
        else: self.parent.download_button.configure(state="disabled")

    def check_all(self):
        for checkbox in self.checkboxes:
            chapter_link = self.checkboxes[checkbox].cget("onvalue")
            self.checked_chapters.add(chapter_link)
            self.checkboxes[checkbox].select()
            self.parent.download_button.configure(state="normal")

    def uncheck_all(self):
        for checkbox in self.checkboxes:
            chapter_link = self.checkboxes[checkbox].cget("onvalue")
            if chapter_link in self.checked_chapters: self.checked_chapters.remove(chapter_link)
            self.checkboxes[checkbox].deselect()
            self.parent.download_button.configure(state="disabled")



class MangaResultFrame(tk.CTkFrame):
    def __init__(self, master, title: str, image_url: str, manga_url: str):
        super().__init__(master)
        self.title = title
        self.image_url = image_url

        MEIRYO_FONT = tk.CTkFont(size=14, family="Meiryo")

        self.grid_columnconfigure((0, 2), weight=0)
        self.grid_columnconfigure(1, weight=1, minsize=500)

        self.img = get_manga_CTkImage(image_url)
        image = tk.CTkLabel(self, image=self.img, text="")
        image.grid(row=0, column=0, padx=4, pady=4)

        # shortened_title = title if len(title) <= 30 else title[:29] + "..."
        title = tk.CTkLabel(self, text=title, anchor="w", height=100, wraplength=500, justify="left", font=MEIRYO_FONT)
        title.grid(row=0, column=1, padx=8, pady=8, sticky="w")

        button = tk.CTkButton(self, text="See more...", fg_color="#D32F2F",
                              command=lambda: self.get_manga_details(manga_url), font=MEIRYO_FONT)
        button.grid(row=0, column=2, padx=8, pady=8)

    def get_manga_details(self, manga_url: str):
        manga_details_window = MangaDetailsWindow(manga_url, manga_image=self.image_url)
        pass


class MangaDetailsWindow(tk.CTkToplevel):
    def __init__(self, manga_url: str, manga_image: str):
        super().__init__()
        self.geometry("800x500")
        self.after(100, self.focus)
        self.after(100, self.lift)

        self.manga_data: Manga = request_manga_data(manga_url)

        self.manga_title: str = self.manga_data['title']
        self.manga_author: str = self.manga_data['author']
        self.manga_artist: str = self.manga_data['artist']
        self.manga_description: str = self.manga_data['description'][:100] + "..."
        self.manga_genre: List[str] = self.manga_data['genre']
        self.manga_chapters: Tuple[str, str] = self.manga_data['chapters']
        self.manga_image: tk.CTkImage = get_manga_CTkImage(manga_image, (172, 230))

        self.title(self.manga_title)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=1)
        self.grid_rowconfigure(5, weight=0)

        self.draw_informations()

    def draw_informations(self):
        title_font = tk.CTkFont(size=15, family="Meiryo Bold")
        info_font = tk.CTkFont(size=12, family="Meiryo")
        description_font = tk.CTkFont(size=14, family="Meiryo")

        image = tk.CTkLabel(self, image=self.manga_image, text="")
        title = tk.CTkLabel(self, text=self.manga_title, wraplength=500, anchor="w", justify="left",
                            text_color="#d94343", font=title_font)
        author = tk.CTkLabel(self, text=f"{self.manga_author} /// {self.manga_artist}", font=info_font,
                             text_color="#474747")
        genre = tk.CTkLabel(self, text=', '.join(self.manga_genre), font=info_font, text_color="#474747")
        description = tk.CTkLabel(self, text=self.manga_description, wraplength=600, anchor="nw", justify="left", height=3,
                                  font=description_font, text_color="#e0e0e0")
        self.manga_chapter_frame = MangaDetailsChaptersFrame(self, chapters=self.manga_chapters)
        check_all_button = tk.CTkButton(self, text="Check All", command=self.manga_chapter_frame.check_all)
        uncheck_all_button = tk.CTkButton(self, text="Uncheck All", command=self.manga_chapter_frame.uncheck_all)
        self.download_button = tk.CTkButton(self, text="Download", command=self.start_download, state="disabled")

        image.grid(row=0, rowspan=4, column=0, padx=10, pady=10, sticky="nwe")
        title.grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky="nw")
        author.grid(row=1, column=1, padx=10, pady=10, sticky="nw")
        genre.grid(row=1, column=2, padx=10, pady=10, sticky="ne")
        description.grid(row=2, rowspan=2, column=1, columnspan=2, padx=10, pady=10, sticky="nw")
        self.manga_chapter_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        uncheck_all_button.grid(row=5, column=0, padx=10, pady=10, sticky="nsew")
        check_all_button.grid(row=5, column=1, padx=10, pady=10, sticky="nsew")
        self.download_button.grid(row=5, column=2, padx=10, pady=10, sticky="nsew")

    def start_download(self):
        print(len(self.manga_chapter_frame.checked_chapters))
        print(list(self.manga_chapter_frame.checked_chapters))
        self.manga_data['chapters'] = list(self.manga_chapter_frame.checked_chapters)
        print(self.manga_data)
        download_task = Thread(target=create_folder_structure_and_fill_chapters, args=(self.manga_data,))
        download_task.start()

        # TODO: Kill threads on app kill


class App(tk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Hachiraw Parser")
        self.geometry("820x680")
        self.resizable(False, True)

        MEIRYO_FONT = tk.CTkFont(size=14, family="Meiryo")

        self.init_widgets()

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure((1, 2), weight=1)
        self.grid_columnconfigure(3, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self.settings_button = tk.CTkButton(self, text="Settings",
                                            image=tk.CTkImage(light_image=Image.open("./settings_icon.png"),
                                                              size=(20, 20)), font=MEIRYO_FONT)
        self.settings_button.grid(row=0, column=0, padx=20, pady=20)

        txtvar = tk.StringVar(value="とも")
        self.search_input = tk.CTkEntry(self, placeholder_text="日本語の名前", font=MEIRYO_FONT, textvariable=txtvar)
        self.search_input.grid(row=0, column=1, padx=20, pady=20, columnspan=2, sticky="ew")

        self.search_button = tk.CTkButton(master=self, text="Search", command=self.init_search, font=MEIRYO_FONT)
        self.search_button.grid(row=0, column=3, padx=20, pady=20)

    def init_widgets(self):
        self.loading_text = None
        self.manga_search_frame = None
        self.search_input = None
        self.settings_button = None
        self.search_button = None
        self.previous_button = None
        self.next_button = None

    def init_search(self, pagination_link: str = None):
        self.destroy_widgets(self.loading_text, self.manga_search_frame)
        self.loading_text = tk.CTkLabel(self, text="Loading...", font=MEIRYO_FONT)
        self.loading_text.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        query = pagination_link if pagination_link is not None else self.search_input.get()
        manga_list: Tuple[List[Tuple[str, str, str]], str, str] = request_search(query, pagination_link is not None)
        self.draw_manga_search(manga_list[0])
        self.draw_pagination(previous_link=manga_list[1], next_link=manga_list[2])

    def draw_manga_search(self, manga_list: List[Tuple[str, str, str]]):
        if manga_list:
            self.loading_text.destroy()
            self.manga_search_frame = MangaSearchFrame(self, mangas=manga_list)
            self.manga_search_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nwes", columnspan=4)
        else:
            self.loading_text.configure(text="作品がありません")

    def draw_pagination(self, previous_link: str = None, next_link: str = None):
        self.destroy_widgets(self.previous_button, self.next_button)
        if previous_link is not None:
            self.previous_button = tk.CTkButton(self, text="<<<", command=lambda: self.init_search(previous_link))
            self.previous_button.grid(row=2, column=0, columnspan=2, padx=20, pady=20)
        if next_link is not None:
            self.next_button = tk.CTkButton(self, text=">>>", command=lambda: self.init_search(next_link))
            self.next_button.grid(row=2, column=2, columnspan=2, padx=20, pady=20)

    def launch_settings(self):
        # TODO: Add a settings popup with :
        # - Downloads dir
        # - download rate (time in seconds between img download
        # - SFW mode : blue literally every img lol
        pass

    def destroy_widgets(self, *widgets):
        for widget in widgets:
            if widget is not None: widget.destroy()


app = App()
app.mainloop()
