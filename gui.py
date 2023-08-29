import customtkinter as tk
import requests
from scraper import request_search
from PIL import Image, ImageTk, ImageOps
from typing import Tuple, List
from tkinter import font

tk.set_appearance_mode("System")
tk.set_default_color_theme("dark-blue")

MEIRYO_FONT = None

class MangaSearchFrame(tk.CTkScrollableFrame):
    def __init__(self, master, mangas: List[Tuple[str, str, str]]):
        super().__init__(master)
        self.mangas = mangas

        for i, manga in enumerate(mangas):
            manga_result_frame = MangaResultFrame(self, title=manga[0], manga_url=manga[1], image_url=manga[2])
            manga_result_frame.grid(row=i, column=0, padx=10, pady=10, sticky="we")


class MangaResultFrame(tk.CTkFrame):
    def __init__(self, master, title: str, image_url: str, manga_url: str):
        super().__init__(master)
        self.title = title
        self.image_url = image_url

        MEIRYO_FONT = tk.CTkFont(size=14, family="Meiryo")

        self.grid_columnconfigure((0, 2), weight=0)
        self.grid_columnconfigure(1, weight=1, minsize=500)

        image = tk.CTkLabel(self, image=self.get_manga_CTkImage(image_url), text="")
        image.grid(row=0, column=0, padx=4, pady=4)

        # shortened_title = title if len(title) <= 30 else title[:29] + "..."
        title = tk.CTkLabel(self, text=title, anchor="w", height=100, wraplength=500, justify="left", font=MEIRYO_FONT)
        title.grid(row=0, column=1, padx=8, pady=8, sticky="w")

        button = tk.CTkButton(self, text="See more...", fg_color="#D32F2F", command=self.get_manga_details, font=MEIRYO_FONT)
        button.grid(row=0, column=2, padx=8, pady=8)

    def get_manga_CTkImage(self, img_url) -> tk.CTkImage:
        headers = {'Referer': "https://hachiraw.com/"}
        img_raw = requests.get(img_url, headers=headers, stream=True).raw
        resized_image = None
        try:
            resized_image = ImageOps.fit(Image.open(img_raw), size=(90, 120))
        except:
            resized_image = ImageOps.fit(Image.linear_gradient("L"), size=(90, 120))
        return tk.CTkImage(light_image=resized_image, size=(90, 120))

    def get_manga_details(self):
        # TODO: Switch to another view / popup to see details about the manga (chapters, author, etc...)
        # TODO: Let the user chose which chapter they want to download
        pass


class App(tk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Hachiraw parser")
        self.geometry("820x480")

        MEIRYO_FONT = tk.CTkFont(size=14, family="Meiryo")

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self.settings_button = tk.CTkButton(self, text="Settings", image=tk.CTkImage(light_image=Image.open("./settings_icon.png"), size=(20, 20)), font=MEIRYO_FONT)
        self.settings_button.grid(row=0, column=0, padx=20, pady=20)

        self.search_input = tk.CTkEntry(self, placeholder_text="日本語の名前", font=MEIRYO_FONT)
        self.search_input.grid(row=0, column=1, padx=20, pady=20, sticky="ew")

        self.search_button = tk.CTkButton(master=self, text="Search", command=self.search_manga, font=MEIRYO_FONT)
        self.search_button.grid(row=0, column=2, padx=20, pady=20)

    def search_manga(self):
        loading_text = tk.CTkLabel(self, text="Loading...")
        loading_text.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        query = self.search_input.get()
        manga_list: List[Tuple[str, str, str]] = request_search(query)
        loading_text.pack_forget()

        self.manga_search_frame = MangaSearchFrame(self, mangas=manga_list)
        self.manga_search_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nwes", columnspan=3)

        # TODO: Add pagination


    def launch_settings(self):
        # TODO: Add a settings popup with :
        # - Downloads dir
        # - something else maybe ?
        pass





app = App()
app.mainloop()
