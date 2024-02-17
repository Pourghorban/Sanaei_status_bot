from config import the_config
from pyrogram import Client


class BotClient(Client):
    def __init__(self):
        proxy = None
        if the_config.use_proxy:
            proxy = {
                "scheme": the_config.proxy_scheme,  # "socks4", "socks5" and "http" are supported
                "hostname": the_config.proxy_hostname,
                "port": the_config.proxy_port,
                "username": the_config.proxy_username,
                "password": the_config.proxy_password
            }
        super().__init__(
            name=the_config.name,
            api_id=the_config.api_id,
            api_hash=the_config.api_hash,
            bot_token=the_config.bot_token,
            proxy=proxy
        )
