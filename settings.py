from configparser import ConfigParser
from threading import Lock, Thread
import os

class SingletonMeta(type):
    _instances = {}
    _lock: Lock = Lock()
    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class Settings(metaclass=SingletonMeta):
    def __init__(self):
        self.downloads_directory: str = os.getcwd() + "\Raws"
        self.download_rate: float = 0.1
        self.SFW_mode: bool = False

    def load_settings(self):
        config = ConfigParser()
        config.read('settings.ini')
        print(config.sections())
        if config.sections():
            self.downloads_directory = config['settings']['downloads_dir']
            self.download_rate = float(config['settings']['download_rate'])
            self.SFW_mode = config['settings']['sfw_mode'] == "True"
            print(self.downloads_directory)
            print(self.download_rate)
            print(self.SFW_mode)

    def save_settings(self):
        config = ConfigParser()
        config['settings'] = {
            'downloads_dir': self.downloads_directory,
            'download_rate': self.download_rate,
            'sfw_mode': self.SFW_mode
        }
        with open('settings.ini', 'w') as configfile:
            config.write(configfile)