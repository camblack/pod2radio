import feedparser
import requests
import os
import time
import psutil
import json
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, TIT2, TPE1
from datetime import datetime
from urllib.parse import urlparse

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

rss_feeds = config['rss_feeds']
download_folder = config['download_folder']
check_interval = config['check_interval']

etag_cache = {}
last_modified_cache = {}
failed_downloads = {}

def is_file_in_use(file_path):
    for proc in psutil.process_iter():
        try:
            for item in proc.open_files():
                if file_path == item.path:
                    return True
        except Exception:
            pass
    return False

def get_qualified_episodes(rss_url, min_duration, count=None, day_of_week=None):
    headers = {}
    if rss_url in etag_cache:
        headers['If-None-Match'] = etag_cache[rss_url]
    if rss_url in last_modified_cache:
        headers['If-Modified-Since'] = last_modified_cache[rss_url]
    
    response = requests.get(rss_url, headers=headers)
    if response.status_code == 304:
        print(f"No changes detected for feed: {rss_url}")
        return []

    feed = feedparser.parse(response.content)
    etag_cache[rss_url] = response.headers.get('ETag')
    last_modified_cache[rss_url] = response.headers.get('Last-Modified')

    qualified_episodes = []
    for entry in feed.entries:
        duration = entry.get('itunes_duration')
        published_date = entry.published_parsed
        if day_of_week and datetime(*published_date[:6]).strftime('%A') != day_of_week:
            continue
        if duration and min_duration > 0:
            duration_seconds = sum(int(x) * 60 ** i for i, x in enumerate(reversed(duration.split(":"))))
            if duration_seconds >= min_duration:
                enclosure = entry.enclosures[0]
                mp3_url = enclosure.href
                episode_title = entry.title
                qualified_episodes.append((mp3_url, episode_title, published_date, entry, duration_seconds))
                if count and len(qualified_episodes) >= count:
                    break
    if not qualified_episodes:
        print(f"No entries found in feed: {rss_url} that meet the minimum duration of {min_duration} seconds for {day_of_week or 'any day'}")
    return qualified_episodes

def download_episode(mp3_url, download_path, show_name, episode_title):
    response = requests.get(mp3_url, stream=True)
    if response.status_code == 200:
        with open(download_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print(f"Downloaded episode: {episode_title}")
        
        # Set metadata
        try:
            audio = EasyID3(download_path)
        except mutagen.id3.ID3NoHeaderError:
            audio = mutagen.File(download_path, easy=True)
            audio.add_tags()
        audio['title'] = episode_title
        audio['artist'] = show_name
        audio.save()
        print(f"Set metadata for {download_path}: Title - {episode_title}, Artist - {show_name}")
    else:
        print(f"Failed to download: {mp3_url}")

def main():
    while True:
        for feed in rss_feeds:
            rss_url = feed['url']
            output_directory = feed.get('output_directory', '')
            output_filename = feed['output_filename']
            min_duration = feed.get('min_duration', 0)
            keep_latest = feed.get('keep_latest', False)
            keep_weekdays = feed.get('keep_weekdays', False)
            weekday_filenames = feed.get('weekday_filenames', {})
            keep_latest_n = feed.get('keep_latest_n', 0)
            
            directory_path = os.path.join(download_folder, output_directory)
            if not os.path.exists(directory_path):
                os.makedirs(directory_path)
            
            # Handle keep_latest
            if keep_latest:
                episodes = get_qualified_episodes(rss_url, min_duration, count=1)
                if episodes:
                    mp3_url, episode_title, published_date, latest_entry, duration_seconds = episodes[0]
                    temp_filename = os.path.join(directory_path, 'temp_' + output_filename)
                    download_path = os.path.join(directory_path, output_filename)
                    show_name = feedparser.parse(rss_url).feed.title
                    download_episode(mp3_url, temp_filename, show_name, episode_title)

                    if os.path.exists(temp_filename):
                        if not is_file_in_use(download_path):
                            if os.path.exists(download_path):
                                os.remove(download_path)
                            os.rename(temp_filename, download_path)
                            print(f"Replaced old episode with the latest: {episode_title}")
                        else:
                            failed_downloads[download_path] = (mp3_url, temp_filename, show_name, episode_title)
                            print(f"File {output_filename} is in use, will retry later")

            # Handle keep_weekdays
            if keep_weekdays:
                show_name = feedparser.parse(rss_url).feed.title
                for day, filename in weekday_filenames.items():
                    episodes = get_qualified_episodes(rss_url, min_duration, count=1, day_of_week=day)
                    if episodes:
                        mp3_url, episode_title, published_date, latest_entry, duration_seconds = episodes[0]
                        weekday_filename = filename
                        temp_filename = os.path.join(directory_path, 'temp_' + weekday_filename)
                        download_path = os.path.join(directory_path, weekday_filename)
                        download_episode(mp3_url, temp_filename, show_name, episode_title)

                        if os.path.exists(temp_filename):
                            if not is_file_in_use(download_path):
                                if os.path.exists(download_path):
                                    os.remove(download_path)
                                os.rename(temp_filename, download_path)
                                print(f"Replaced old {day} episode with the latest: {episode_title}")
                            else:
                                failed_downloads[download_path] = (mp3_url, temp_filename, show_name, episode_title)
                                print(f"File {weekday_filename} is in use, will retry later")

            # Handle keep_latest_n
            if keep_latest_n > 0:
                episodes = get_qualified_episodes(rss_url, min_duration, count=keep_latest_n)
                if episodes:
                    show_name = feedparser.parse(rss_url).feed.title
                    latest_episode = episodes[0]
                    # Save the latest episode with a consistent filename
                    mp3_url, episode_title, published_date, latest_entry, duration_seconds = latest_episode
                    temp_filename = os.path.join(directory_path, 'temp_' + output_filename)
                    download_path = os.path.join(directory_path, output_filename)
                    download_episode(mp3_url, temp_filename, show_name, episode_title)

                    if os.path.exists(temp_filename):
                        if not is_file_in_use(download_path):
                            if os.path.exists(download_path):
                                os.remove(download_path)
                            os.rename(temp_filename, download_path)
                            print(f"Replaced old episode with the latest: {episode_title}")
                        else:
                            failed_downloads[download_path] = (mp3_url, temp_filename, show_name, episode_title)
                            print(f"File {output_filename} is in use, will retry later")

                    # Save the rest of the episodes with indexed filenames
                    for i, (mp3_url, episode_title, published_date, latest_entry, duration_seconds) in enumerate(episodes[1:], start=1):
                        output_filename_n = f"{i}_{output_directory}_{output_filename}"
                        temp_filename = os.path.join(directory_path, 'temp_' + output_filename_n)
                        download_path = os.path.join(directory_path, output_filename_n)
                        download_episode(mp3_url, temp_filename, show_name, episode_title)

                        if os.path.exists(temp_filename):
                            if not is_file_in_use(download_path):
                                if os.path.exists(download_path):
                                    os.remove(download_path)
                                os.rename(temp_filename, download_path)
                                print(f"Saved episode {i} with filename: {output_filename_n}")
                            else:
                                failed_downloads[download_path] = (mp3_url, temp_filename, show_name, episode_title)
                                print(f"File {output_filename_n} is in use, will retry later")

                    # Remove older episodes if there are more than keep_latest_n
                    existing_files = sorted(
                        [f for f in os.listdir(directory_path) if f.startswith(output_directory) and (f.endswith(output_filename) or f.startswith(str(i) + '_'))],
                        key=lambda x: os.path.getctime(os.path.join(directory_path, x))
                    )
                    if len(existing_files) > keep_latest_n:
                        for old_file in existing_files[:-keep_latest_n]:
                            os.remove(os.path.join(directory_path, old_file))
                            print(f"Removed old episode: {old_file}")

        # Retry failed downloads
        for download_path, (mp3_url, temp_filename, show_name, episode_title) in list(failed_downloads.items()):
            if not is_file_in_use(download_path):
                download_episode(mp3_url, temp_filename, show_name, episode_title)
                if os.path.exists(temp_filename):
                    if os.path.exists(download_path):
                        os.remove(download_path)
                    os.rename(temp_filename, download_path)
                    print(f"Replaced old episode with the latest: {episode_title}")
                del failed_downloads[download_path]

        print(f"Sleeping for {check_interval} seconds before next check...")
        time.sleep(check_interval)

if __name__ == "__main__":
    main()
