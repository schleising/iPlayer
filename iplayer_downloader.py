from pathlib import Path
import re
import subprocess
import atexit
import json

import requests

from rich import print

from pydantic import BaseModel

# An enumeration for the download status
class DownloadStatus:
    NOT_STARTED = 0
    SUCCESS = 1
    ERROR = 2

# A Pydantic to store the details of each episode
class Episode(BaseModel):
    series: int
    episode: int
    title: str
    url: str
    status: int = DownloadStatus.NOT_STARTED

# A Pydantic to store the details of each series
class Series(BaseModel):
    title: str
    episodes: dict[str, Episode] = {}

# Class for the iPlayer downloader
class iPlayerDownloader:
    def __init__(self, series_title, series_urls, series_regex) -> None:
        # Set the base URL for the BBC iPlayer website
        base_url = 'https://www.bbc.co.uk'

        # Set the title of the series
        self._series_title = series_title

        # Store the details of each episode
        self._series: Series = Series(title=series_title)

        # Loop through each series URL
        for seriesUrl in series_urls:
            # Download the page
            page = requests.get(seriesUrl)

            # If the page was downloaded successfully
            if page.status_code == requests.codes.OK:
                # Find all the URLs for each episode
                results = series_regex.finditer(page.text)

                # Loop through each result
                for result in results:
                    # Create the URL for the episode
                    url = f'{base_url}{result.group(0)}'

                    # Get the series number
                    series = int(result.group(1))

                    # Get the episode number
                    episode = int(result.group(2))

                    # Get the episode title, replace any dashes with spaces and title case it
                    title = result.group(3).replace('-', ' ').title()

                    # Add the episode to the dictionary
                    self._series.episodes[url] = Episode(
                        series=series,
                        episode=episode,
                        title=title,
                        url=url
                    )

    def download_episodes(self) -> None:
        # Loop through each episode, sorted by series and episode number
        for episode in sorted(self._series.episodes.values(), key=lambda x: (x.series, x.episode)):
            # Create the output file name
            output_file =  Path.home() / f'Downloads/{self._series_title}/Season {episode.series}/{self._series_title} - S{episode.series:02}E{episode.episode:02} - {episode.title}.mp4'
            print(f'[blue]Downloading Series {episode.series} Episode {episode.episode} - {episode.title}[/]')
            print(f'[blue]Saving to {output_file}[/]')

            # Create the output directory
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Download the episode
            completed_process = subprocess.run(['youtube-dl', '-o', output_file.absolute() , episode.url])

            # Check that the subprocess exited successfully
            if completed_process.returncode != 0:
                # Print an error message
                print(f'[red]Error downloading episode {episode.title}[/]')

                # Set the download status to error
                episode.status = DownloadStatus.ERROR
            else:
                # Print a success message
                print(f'[green]Downloaded {episode.title} successfully[/]')

                # Set the download status to success
                episode.status = DownloadStatus.SUCCESS

    def save_download_status(self) -> None:
        # Create the output file name
        output_file = Path.home() / f'Downloads/{self._series_title}/download_status.txt'

        # Create the output directory
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Save the download status to a JSON file
        with open(output_file, 'w') as f:
            json.dump(self._series.model_dump(), f, indent=2)

if __name__ == '__main__':
    # The regular expression used to find the URLs for each episode
    regex = re.compile(r'/iplayer/episode/[a-z0-9]+/inside-no-9-series-([0-9])-([0-9]+)-([a-zA-Z- ]+)')

    # The title of the series
    series_title = 'Inside No. 9'

    # The URLs for each series
    series_urls = [
        'https://www.bbc.co.uk/iplayer/episodes/b05p650r/inside-no-9?seriesId=b03tvq6m',
        'https://www.bbc.co.uk/iplayer/episodes/b05p650r/inside-no-9?seriesId=b05p655x',
        'https://www.bbc.co.uk/iplayer/episodes/b05p650r/inside-no-9?seriesId=b08ghppm',
        'https://www.bbc.co.uk/iplayer/episodes/b05p650r/inside-no-9?seriesId=b09lddtr',
        'https://www.bbc.co.uk/iplayer/episodes/b05p650r/inside-no-9?seriesId=m000f1tc',
        'https://www.bbc.co.uk/iplayer/episodes/b05p650r/inside-no-9?seriesId=p099qq07',
        'https://www.bbc.co.uk/iplayer/episodes/b05p650r/inside-no-9?seriesId=m0016mq4',
        'https://www.bbc.co.uk/iplayer/episodes/b05p650r/inside-no-9?seriesId=m001gdvb',
    ]

    # Create the iPlayer downloader
    downloader = iPlayerDownloader(series_title, series_urls, regex)

    # Register the save download status function to be called when the program exits
    atexit.register(downloader.save_download_status)

    # Download the episodes
    downloader.download_episodes()
