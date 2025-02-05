# Pod2Radio

This script is designed to automate the downloading and management of podcast episodes from multiple RSS feeds. It allows you to configure various options, including keeping the latest episode, keeping episodes for each weekday, and retaining a specified number of the most recent episodes.

Note: This script is mainly designed to run on Windows systems in conjunction with an automation system such as StationPlaylist, etc

## Features

- Download the latest episode from an RSS feed.
- Keep episodes for specific weekdays.
- Retain a configurable number of the most recent episodes.
- Set minimum duration thresholds for episodes.
- Manage episodes from multiple RSS feeds, even when stored in the same directory.

## Requirements

- Python 3.x
- `requests` library
- `feedparser` library
- `mutagen` library
- `psutil` library

## Installation

1. **Install Python 3.x**: Ensure Python 3.x is installed on your system. You can download it from [python.org](https://www.python.org/).
2. **Install Required Libraries**: Open a command prompt and run the following commands to install the necessary libraries:
    ```sh
    pip install requests feedparser mutagen psutil
    ```
3. **Download the Script**: Save the `rss_downloader.py` script to a directory of your choice (e.g., `C:\\downloader`).
4. **Create Configuration File**: In the same directory as the script, create a file named `config.json` with your configuration.

## Configuration

The `config.json` file defines the RSS feeds and their respective options. Here is a basic example:

```json
{
    "rss_feeds": [
        {
            "url": "https://example.com/rss_feed_1.xml",
            "output_directory": "show_1",
            "min_duration": 60,
            "output_filename": "latest_episode.mp3",
            "keep_latest": true
        },
        {
            "url": "https://example.com/rss_feed_2.xml",
            "output_directory": "show_2",
            "min_duration": 30,
            "output_filename": "latest_episode.mp3",
            "keep_latest": true
        },
        {
            "url": "https://example.com/rss_feed_3.xml",
            "output_directory": "show_3",
            "output_filename": "latest_episode.mp3",
            "min_duration": 300,
            "keep_latest": true,
            "keep_weekdays": true,
            "weekday_filenames": {
                "Monday": "monday_episode.mp3",
                "Tuesday": "tuesday_episode.mp3",
                "Wednesday": "wednesday_episode.mp3",
                "Thursday": "thursday_episode.mp3",
                "Friday": "friday_episode.mp3",
                "Saturday": "saturday_episode.mp3",
                "Sunday": "sunday_episode.mp3"
            }
        },
        {
            "url": "https://example.com/rss_feed_4.xml",
            "output_directory": "show_4",
            "output_filename": "latest_episode.mp3",
            "min_duration": 300,
            "keep_latest": true,
            "keep_weekdays": true,
            "weekday_filenames": {
                "Monday": "monday_episode.mp3",
                "Tuesday": "tuesday_episode.mp3",
                "Wednesday": "wednesday_episode.mp3",
                "Thursday": "thursday_episode.mp3",
                "Friday": "friday_episode.mp3",
                "Saturday": "saturday_episode.mp3",
                "Sunday": "sunday_episode.mp3"
            }
        },
        {
            "url": "https://example.com/rss_feed_5.xml",
            "output_directory": "show_5",
            "output_filename": "latest_episode.mp3",
            "min_duration": 300,
            "keep_latest_n": 5
        }
    ],
    "download_folder": "C:\\media\\rss_downloads",
    "check_interval": 3600
}
```

### Configuration Options

- **url**: The URL of the RSS feed.
- **output_directory**: The directory where episodes will be saved.
- **min_duration**: The minimum duration (in seconds) an episode must have to be downloaded.
- **output_filename**: The filename for the latest episode.
- **keep_latest**: Boolean value indicating whether to keep only the latest episode.
- **keep_weekdays**: Boolean value indicating whether to keep episodes for specific weekdays.
- **weekday_filenames**: A dictionary mapping weekdays to filenames.
- **keep_latest_n**: An integer specifying the number of most recent episodes to keep.

## Running the Script

1. **Open Command Prompt**: Press `Win + R`, type `cmd`, and press Enter.
2. **Navigate to the Script Directory**: Use the `cd` command to navigate to the directory where you saved `rss_downloader.py` and `config.json` (e.g., `C:\\downloader`):
    ```sh
    cd C:\\downloader
    ```
3. **Run the Script**:
    ```sh
    python rss_downloader.py
    ```

The script will run indefinitely, checking the RSS feeds at the interval specified in `config.json` (`check_interval` is in seconds).

### Example Usage

Here is an example of the expected behavior with the provided configuration:

- **Show 1**: Keeps the latest episode for `show_1`.
- **Show 2**: Keeps the latest episode for `show_2`.
- **Show 3**: Keeps the latest episode and episodes for each weekday.
- **Show 4**: Keeps the latest episode and episodes for each weekday.
- **Show 5**: Retains the 5 most recent episodes, deleting the oldest when a new one is downloaded.

Ensure the output directory exists and is writable. The script manages the downloaded episodes based on the configuration, ensuring the latest content is always available while adhering to the specified retention policies.
