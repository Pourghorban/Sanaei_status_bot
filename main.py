import asyncio
import json
import base64
import re
import jdatetime
from peewee import SqliteDatabase
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Entities.inbound import Inbounds
from Entities.user import User
from client import BotClient
from pyrogram import filters
from pyrogram.enums import ChatAction
from config import the_config
import aiohttp
from urllib.parse import urlparse


db = SqliteDatabase('bot.db')
db.connect()
db.create_tables([User, Inbounds])

app = BotClient()


@app.on_message(filters.command(commands=['start']))
async def start(bot, update):
    existing_user = User.select().where(User.telegram_id == update.from_user.id).first()

    if not existing_user:
        User.create(telegram_id=update.from_user.id)

    await bot.send_chat_action(chat_id=update.chat.id, action=ChatAction.TYPING)
    await bot.send_message(
        chat_id=update.chat.id,
        text='سلام🤞به بات اعلام وضعیت خوش امدید.\n\nبرای اضافه کردن کانفیگ از دستور /add و برای اطلاع از وضعیت کانفیگ ها از دستور /status استفاده کنید.'
        )


@app.on_message(filters.command(commands=['add']))
async def add_config(bot, update):
    await bot.send_chat_action(chat_id=update.chat.id, action=ChatAction.TYPING)
    await bot.send_message(chat_id=update.chat.id, text='لطقا کانفیگ یا پورت را ارسال کنید.')


async def get_inbound(port):
    async with aiohttp.ClientSession(cookies={"lang": "en-US"}, cookie_jar=aiohttp.CookieJar(unsafe=True)) as sess:
        for burl in the_config.url:
            server = urlparse(burl).hostname
            # login
            async with sess.post(f"{burl}/login", data={"username": the_config.username, "password": the_config.password}) as resp:
                r = await resp.json()


            if not r["success"]:
                raise Exception(f"login failed {server}")

            # get inbounds
            async with sess.get(f"{burl}/panel/api/inbounds/list") as resp:
                r = await resp.json()
            if not r["success"]:
                raise Exception(f"get inbounds failed {server}")
            # find the port
            try:
                inb = dict(tuple(filter(lambda i: i["port"] == int(port), r["obj"]))[0])
            except IndexError:
                continue  # go to the next server
            return inb["up"], inb["down"], inb["total"], inb["expiryTime"] // 1000, inb["enable"], inb['remark']
    raise Exception("port not found!")


async def human_bytes(n):
    vahed = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while abs(n) >= 1024:
        n /= 1024
        i += 1
    return f"{n:.2f}{vahed[i]}"


async def get_conn(port) -> dict:
    conn = {}
    try:
        port = int(port)
        if not 0 < port < 65535:
            raise
    except:
        return conn
    proc = await asyncio.subprocess.create_subprocess_shell(
        f"ss -nH state established sport = :{port} | awk '{{print $5}}' | cut -d \":\" -f 4 | cut -d \"]\" -f 1 | sort | uniq -c | awk '{{print $1\"|\"$2}}'",
        stdout=asyncio.subprocess.PIPE,
        shell=True,
    )
    out, _err = await proc.communicate()
    out = out.decode().strip().split("\n")
    if not out or not out[0]:
        return conn
    for i in out:
        num, ip = i.strip().split("|")
        conn[ip] = num
    return conn


@app.on_message(filters.command(commands=['status']))
async def status(bot, update):
    user_inbounds = Inbounds.select().where(Inbounds.user_id == update.from_user.id)
    keyboard_buttons = []

    for inbound in user_inbounds:
        button = InlineKeyboardButton(
            text=inbound.remark,
            callback_data=str(inbound.port)
        )

        keyboard_buttons.append([button])
    keyboard = InlineKeyboardMarkup(keyboard_buttons)

    await bot.send_message(
        chat_id=update.chat.id,
        reply_to_message_id=update.message_id,
        text="🌐 کانفیگ های شما:",
        reply_markup=keyboard
    )


@app.on_message(filters.text & ~filters.command(commands=['start', 'status']))
async def handleMsg(bot, update):
    if update.text == None:
        return

    mode = 1
    try:
        port = int(update.text)
        existing_port = Inbounds.select().where(
            (Inbounds.user_id == update.from_user.id) & (Inbounds.port == port)).first()

        if existing_port:
            config = await get_inbound(port)
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text=config[5], callback_data=str(port)),
                    ]
                ]
            )

            await bot.send_message(update.chat.id, text="این کانفیگ قبلاً اضافه شده است!", reply_markup=keyboard)

        else:
            req_inbound = await get_inbound(port)
            new_inbound = Inbounds.create(port=port, user_id=update.from_user.id, remark=req_inbound[5])

            user_inbounds = Inbounds.select().where(Inbounds.user_id == update.from_user.id)
            keyboard_buttons = []

            for inbound in user_inbounds:
                button = InlineKeyboardButton(
                    text=inbound.remark,
                    callback_data=str(inbound.port)
                )

                keyboard_buttons.append([button])
            keyboard = InlineKeyboardMarkup(keyboard_buttons)

            await bot.send_message(
                chat_id=update.chat.id,
                reply_to_message_id=update.message_id,
                text="🌐 کانفیگ های شما:",
                reply_markup=keyboard
            )

    except ValueError:
        mode = 2

    if mode == 2:
        try:
            vmess = re.search(r"^vmess://(?P<VM>.+)$", update.text)
            vless = re.search(r":(?P<VL>\d+)\?", update.text)
            if vmess:
                port = int(json.loads(base64.b64decode(vmess.group("VM")))["port"])
            elif vless:
                port = int(vless.group("VL"))
            else:
                raise

            existing_port = Inbounds.select().where(
                (Inbounds.user_id == update.from_user.id) & (Inbounds.port == port)).first()

            if existing_port:
                config = await get_inbound(port)
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text=config[5], callback_data=str(port)),
                        ]
                    ]
                )

                await bot.send_message(update.chat.id, text="این کانفیگ قبلاً اضافه شده است!", reply_markup=keyboard)

            else:
                req_inbound = await get_inbound(port)
                new_inbound = Inbounds.create(port=port, user_id=update.from_user.id, remark=req_inbound[5])

                user_inbounds = Inbounds.select().where(Inbounds.user_id == update.from_user.id)
                keyboard_buttons = []

                for inbound in user_inbounds:
                    button = InlineKeyboardButton(
                        text=inbound.remark,
                        callback_data=str(inbound.port)
                    )

                    keyboard_buttons.append([button])
                keyboard = InlineKeyboardMarkup(keyboard_buttons)

                await bot.send_message(
                    chat_id=update.chat.id,
                    reply_to_message_id=update.message_id,
                    text="🌐 کانفیگ های شما:",
                    reply_markup=keyboard
                )

        except ValueError:
            print(ValueError)
            await bot.send_message(update.chat.id, "invalid msg!")
            return


@app.on_callback_query()
async def callback_query_handler(bot, update):
    port = int(update.data)  # تبدیل مقدار port به عدد
    try:
        if port > 65535 or port < 1:
            raise Exception("invalid port!")
        info = await get_inbound(port)
    except Exception as ex:
        await bot.send_message(update.message.chat.id, ex)
        return
    conn = await get_conn(port)

    if info[3] != 0:
        formatted_date = jdatetime.date.fromtimestamp(info[3]).strftime('%Y/%m/%d')
    else:
        formatted_date = 'نامحدود'

    await update.message.edit_text(
        text=f"🌐 وضعیت: {'فعال ✅' if info[4] else 'غیرفعال ❌'}\n"
        f"🖥️نام کانفیگ: {info[5]}\n\r\n\r"
        f"📥 حجم دانلود: {await human_bytes(info[1])}\n\r"
        f"📤 حجم آپلود: {await human_bytes(info[0])}\n\r"
        f"📦 حجم باقی‌مانده: {await human_bytes(info[2]-(info[0]+info[1])) if info[2]!=0 else 'نامحدود'}\n\r\n\r"
        f"🗓 تاریخ انقضا: {formatted_date}\n\r\n\r"
        f"👤 تعداد افراد متصل: {len(conn.keys())}\n\r"
        f"🌐 لیست کانکشن ها:\n"
        + "<blockquote>"
        + "\n".join(f" - {i[0]} -> {i[1]}" for i in conn.items())
        + "</blockquote>"
    )


app.run()
