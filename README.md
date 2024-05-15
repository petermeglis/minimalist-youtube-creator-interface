# minimalist-youtube-creator-interface

The goal of this script is to be able to access the core functionalities a YouTube creator needs but without the distractions like video views, subscriber count, likes, etc.

Setup:
- Ensure python3 is installed
- `pip install` the packages from the YouTube API quickstart guide
- Run `python3 ytcli.py`

Termux Phone Instructions:
- Download F-Droid app repository, then in F-Droid download Termux
- Then:
- pkg install python
- pkg install git
- git clone to ~
- pkg update && pkg upgrade
- termux-setup-storage
- USB transfer the secrets from git repo on laptop to downloads folder, then transfer in termux from ~/storage/shared

Resources:
- YouTube API Quickstart Guide: https://developers.google.com/youtube/v3/quickstart/python
- API docs: https://developers.google.com/youtube/v3/docs/channels/list
