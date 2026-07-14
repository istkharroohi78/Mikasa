import asyncio
import os
import re
import random
from typing import Union
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from AviaxMusic.utils.formatters import time_to_seconds
import aiohttp
from AviaxMusic import LOGGER

try:
    from py_yt import VideosSearch
except ImportError:
    from youtubesearchpython.__future__ import VideosSearch

# ==========================================
# NEW API CONFIGURATION
# ==========================================
SHRUTI_API_URL = os.environ.get("SHRUTI_API_URL", "https://api.shrutibots.site")
SHRUTI_API_KEY = os.environ.get("SHRUTI_API_KEY", "ShrutiBotsC0WH1GowF2HkGoKv4F3y")

ONEGRAB_API_URL = os.environ.get("ONEGRAB_API_URL", "https://api.onegrab.fun")
ONEGRAB_API_KEYS = [
    os.environ.get("ONEGRAB_API_KEY_1", "0b168a_I21sJa-aeWzx30ubnZOrbSmjY5eST1ID"),
    os.environ.get("ONEGRAB_API_KEY_2", "c93415_Qc6z38kFH52j38qSF4MShLaojVL1JOB5"),
    os.environ.get("ONEGRAB_API_KEY_3", "be7ccd_J_G_4M4LlNUSRbm9YuyhGKXoERPC3_1H")
]

# Strict YouTube Regex Check
YOUTUBE_REGEX = re.compile(r"^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$")

def is_valid_youtube_link(link: str) -> bool:
    """Checks if the provided link is a strictly valid YouTube URL."""
    # Agar 11 character ka video ID hai (internal bot process), allow it
    if len(link) == 11 and not link.startswith("http"):
        return True
    return bool(YOUTUBE_REGEX.match(link))

def get_api_configs():
    """Returns a list of API configs to try (Shruti first, then a random OneGrab)"""
    return [
        {"url": SHRUTI_API_URL, "key": SHRUTI_API_KEY},
        {"url": ONEGRAB_API_URL, "key": random.choice(ONEGRAB_API_KEYS)}
    ]

async def download_song(link: str) -> str:
    if not is_valid_youtube_link(link):
        return None

    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link

    if not video_id or len(video_id) < 3:
        return None

    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")

    if os.path.exists(file_path):
        return file_path

    apis_to_try = get_api_configs()

    for api in apis_to_try:
        api_url = api["url"]
        api_key = api["key"]
        
        try:
            async with aiohttp.ClientSession() as session:
                # API keys are usually passed in params or headers. Passing in both to be safe.
                params = {"url": video_id, "type": "audio", "api_key": api_key, "key": api_key}
                headers = {"Authorization": f"Bearer {api_key}"}

                async with session.get(
                    f"{api_url}/download",
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=7)
                ) as response:
                    if response.status != 200:
                        continue

                    data = await response.json()
                    download_token = data.get("download_token")

                    if not download_token:
                        continue

                    stream_url = f"{api_url}/stream/{video_id}?type=audio&token={download_token}"

                    async with session.get(
                        stream_url,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=300)
                    ) as file_response:
                        if file_response.status == 302:
                            redirect_url = file_response.headers.get('Location')
                            if redirect_url:
                                async with session.get(redirect_url) as final_response:
                                    if final_response.status != 200:
                                        continue
                                    with open(file_path, "wb") as f:
                                        async for chunk in final_response.content.iter_chunked(16384):
                                            f.write(chunk)
                                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                                        return file_path
                                    else:
                                        continue
                        elif file_response.status == 200:
                            with open(file_path, "wb") as f:
                                async for chunk in file_response.content.iter_chunked(16384):
                                    f.write(chunk)
                            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                                return file_path
                            else:
                                continue
                        else:
                            continue

        except Exception:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            continue

    return None

async def download_video(link: str) -> str:
    if not is_valid_youtube_link(link):
        return None

    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link

    if not video_id or len(video_id) < 3:
        return None

    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")

    if os.path.exists(file_path):
        return file_path

    apis_to_try = get_api_configs()

    for api in apis_to_try:
        api_url = api["url"]
        api_key = api["key"]
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {"url": video_id, "type": "video", "api_key": api_key, "key": api_key}
                headers = {"Authorization": f"Bearer {api_key}"}

                async with session.get(
                    f"{api_url}/download",
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=7)
                ) as response:
                    if response.status != 200:
                        continue

                    data = await response.json()
                    download_token = data.get("download_token")

                    if not download_token:
                        continue

                    stream_url = f"{api_url}/stream/{video_id}?type=video&token={download_token}"

                    async with session.get(
                        stream_url,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=600)
                    ) as file_response:
                        if file_response.status == 302:
                            redirect_url = file_response.headers.get('Location')
                            if redirect_url:
                                async with session.get(redirect_url) as final_response:
                                    if final_response.status != 200:
                                        continue
                                    with open(file_path, "wb") as f:
                                        async for chunk in final_response.content.iter_chunked(16384):
                                            f.write(chunk)
                                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                                        return file_path
                                    else:
                                        continue
                        elif file_response.status == 200:
                            with open(file_path, "wb") as f:
                                async for chunk in file_response.content.iter_chunked(16384):
                                    f.write(chunk)
                            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                                return file_path
                            else:
                                continue
                        else:
                            continue

        except Exception:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            continue

    return None

async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        # STRICT REGEX APPLIED HERE TOO
        self.regex = r"^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.match(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        extracted_url = text[entity.offset: entity.offset + entity.length]
                        if is_valid_youtube_link(extracted_url):
                            return extracted_url
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        if is_valid_youtube_link(entity.url):
                            return entity.url
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["title"]

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["duration"]

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["thumbnails"][0]["url"].split("?")[0]

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        try:
            downloaded_file = await download_video(link)
            if downloaded_file:
                return 1, downloaded_file
            else:
                return 0, "Video download failed"
        except Exception as e:
            return 0, f"Video download error: {e}"

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        playlist = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --playlist-end {limit} --skip-download {link}"
        )
        try:
            result = [key for key in playlist.split("\n") if key]
        except:
            result = []
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        ytdl_opts = {"quiet": True}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    if "dash" not in str(format["format"]).lower():
                        formats_available.append(
                            {
                                "format": format["format"],
                                "filesize": format.get("filesize"),
                                "format_id": format["format_id"],
                                "ext": format["ext"],
                                "format_note": format["format_note"],
                                "yturl": link,
                            }
                        )
                except:
                    continue
        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + link

        try:
            if video:
                downloaded_file = await download_video(link)
            else:
                downloaded_file = await download_song(link)

            if downloaded_file:
                return downloaded_file, True
            else:
                return None, False
        except Exception:
            return None, False
    
