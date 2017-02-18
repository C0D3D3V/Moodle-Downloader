# Automatic Moodle Downloader

The `moodleCrawler.py` script downloads all the files posted in the course page of all the courses in your moodle page.
Dublicated Files get deleted.
Links in the history file get not 
.

Set the following in the file `config.ini` before running the script

- `username` : Moodle Username
- `password` : Moodle Password
- `root_dir` : The root directory for where the files are to be stored
- `url` : URL for moodle authentication
- `forum` : If forums should also be crawled
- `history` : If a history file should be used

All the files are stored in their respective directories inside the `root_dir` with the names as in moodle.


#### REQUIREMENTS

- Python 2.7+
- Beautifulsoup - `sudo apt-get install python-beautifulsoup`

### EXTRAS

- Put `watch -n 3600 python moodleCrawler.py` in startup to fetch the files every hour.

This code is the modified version of the downloader created by Vinay Chandra

This work is licensed under a Creative Commons Attribution 4.0 International License.
