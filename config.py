from configparser import ConfigParser
import typing
import logging


def list_map(func, iterator):
    if not iterator:
        return []
    return list(map(func, iterator))


class Config:
    _the_config: ConfigParser = None

    name: str = ''
    api_id: str = ''
    api_hash: str = ''
    bot_token: str = ''

    _admin: typing.List[int] = []

    use_proxy:bool = False
    proxy_scheme: str = ''
    proxy_hostname: str = ''
    proxy_port: int = 0
    proxy_username: str = ''
    proxy_password: str = ''

    url: str = ''
    username: str = ''
    password: str = ''


    def __init__(self, config_file='config.ini') -> None:
        self._the_config = ConfigParser()
        self._the_config.read(config_file)

        self.name = self._the_config.get('telegram', 'name')
        self.api_id = self._the_config.get('telegram', 'api_id')
        self.api_hash = self._the_config.get('telegram', 'api_hash')
        self.bot_token = self._the_config.get('telegram', 'bot_token')

        self._admin = list_map(int, self._the_config.get('bot', 'admin').split())

        self.url = list_map(str, self._the_config.get('panel', 'url').split())
        self.username = self._the_config.get('panel', 'username')
        self.password = self._the_config.get('panel', 'password')

        try:
            self.load_proxy()
        except Exception as e:
            logging.warning(e, stacklevel=3)

    def load_proxy(self) -> None:
        self.use_proxy = self._the_config.getboolean('proxy', 'use_proxy', fallback=False)
        self.proxy_scheme = self._the_config.get('proxy', 'scheme', fallback='')
        self.proxy_hostname = self._the_config.get('proxy', 'hostname', fallback='')
        self.proxy_port = self._the_config.getint('proxy', 'port', fallback=0)
        self.proxy_username = self._the_config.get('proxy', 'username', fallback=None)
        self.proxy_password = self._the_config.get('proxy', 'password', fallback=None)


the_config: Config = Config()
