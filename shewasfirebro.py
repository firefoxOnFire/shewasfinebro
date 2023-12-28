# pylint: disable-all
# copyright - firefoxonfire

import asyncio
import logging

import aiohttp
from telegram import Bot, Update
from telegram.error import BadRequest, RetryAfter
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

token1 = ""  
token2 = "" 
token3 = "" 
token4 = ""

bot2 = Bot(
    token=token1,
)
bot3 = Bot(
    token=token3,
)
bot4 = Bot(
    token=token4,
)
bot = Bot(
    token=token2,
)

admin = 43444447
chat_id = -1001444444450
thread = {
    'movies': 6, #movie, movies, stream, series, TV, TV shows, shows
    'others': 10,
    'adult': 13, #sex, sex cams, adult, naked, naked girls, stripchat, xxx, porn, fuck, porno, x rated, dildo, pussy, tits, ass, jav, hentai, 
    # 'sport': #sport, match, 
}

url_set = set()
urlscan_url = "https://urlscan.io/json/live/"
queue = asyncio.Queue()


movie_tag = "movie, movies, stream, series, TV shows, shows".split(', ')
porno_tag = "sex, sex cams, adult, naked, naked girls, stripchat, xxx, porn, fuck, porno, x rated, dildo, pussy, tits, JAV, hentai".split(', ')

def find_matching_thread(search_string):
    search_string_lower = search_string.lower()
    
    match_set1 = any(word.lower() in search_string_lower for word in movie_tag)
    match_set2 = any(word.lower() in search_string_lower for word in porno_tag)

    if match_set1 and match_set2:
        return thread["adult"]
    elif match_set1:
        return thread["movies"]
    elif match_set2:
        return thread["adult"]
    else:
        return thread["others"]
    

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()} !\n\nGO to @urlScanner",
    )


async def fetch_and_put_to_queue():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(urlscan_url) as response:
                    json_data = await response.json()

            json_data = json_data["results"]
            for entry in json_data:
                url = entry.get("task").get("url")
                url2 = entry.get("page").get("url")
                if 'urlscan.io' in url or 'urlscan.io' in url2:
                    continue
                server = entry.get("page").get("server")
                country = entry.get("page").get("country")
                ip = entry.get("page").get("ip")
                title = entry.get("page").get("title")
                screenshot = entry.get("screenshot")

                text = f"Title: {title}\nserver: #{server}\ncountry: #{country}\nIP: {ip}\nURL1: {url}\nURL2: {url2}"
                thread_id = thread['others']
                if title:
                    thread_id = find_matching_thread(title)
                if url and url not in url_set:
                    url_set.add(url)
                    await queue.put((text, screenshot, thread_id))
        except Exception as e:
            logging.info(e)
            await asyncio.sleep(30)

        await asyncio.sleep(10)


async def read_from_queue(boy: Bot):
    while True:
        try:
            url, screenshot, thread_id = await queue.get()
            queue.task_done()
            try:
                if not len(url) > 1024:
                    await boy.send_photo(chat_id, screenshot, url, message_thread_id=thread_id)
                else:
                    mes = await boy.send_photo(chat_id, screenshot, message_thread_id=thread_id)
                    await boy.send_message(
                        chat_id,
                        url[:4096],
                        reply_to_message_id=mes.message_id,
                        disable_web_page_preview=True,
                        message_thread_id=thread_id
                    )
                    await asyncio.sleep(3)
            except BadRequest as b:
                logging.info(b)
            except RetryAfter as e:
                await asyncio.sleep(e.retry_after)
            except Exception:
                pass
        except Exception:
            pass
        await asyncio.sleep(3)


async def tasker():
    loop = asyncio.get_running_loop()
    fetcher_task = loop.create_task(fetch_and_put_to_queue())
    reader_task = [
        loop.create_task(read_from_queue(b)) for b in (bot3, bot4, bot2, bot)
    ]


def runner():
    application = Application.builder().post_init(tasker).token(token2).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    runner()
