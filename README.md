# Automatic Moodle Downloader

The `moodleCrawler.py` script downloads all the files posted in the course page of all the courses you are enroled to.
Dublicated Files in the `root_dir` get deleted. Links in the history file get not downloaded.

You can change names of downloaded Files and Places them to a different location, they will not be downloaded again (only if you delete the history files).

Set the following in the file `config.ini` before running the script

- `username` [String] : Moodle Username
- `password` [String] : Moodle Password
- `root_dir` [String] : The path to the directory where the files are to be stored
- `authurl` [String] : URL for moodle authentication. Mostly ends with '/login/index.php'
- `baseurl` [String] : URL of moodle installation. Could be something like 'https://moodle.someMoodle.de' or 'https://someMoodle.de/moodle/'
- `useauthstate` [Boolean] : If AuthState should be used for login. This needs to be set to true if in the authentication URL the parameter AuthState is set. Try to set this to `true` if the login fails!
- `uselogintoken` [Boolean] : If a logintoken should be used for login. This needs to be set to true if in the login post request the parameter logintoken is set. Try to set this to `true` if the login fails! 
- `reloginonfile` [Boolean] : If the crawler should check if it is still logged in, if not it relogin. This is normally not necessary
- `allcourses` [Boolean] : If all courses should be crawled or only the courses listed on the dashboard
- `forum` [Boolean] : If forums should also be crawled 
- `wiki` [Boolean] : If wikis should also be crawled 
- `history` [Boolean] : If a history file should be used 
- `maxdepth` [Integer] : The depth how deep the crawler should maximal crawl (default = 9) 
- `loglevel` [Integer] : Sets the level of logging (0 - less information / 5 - all information)
- `externallinks` [Boolean] : If external links should get crawled
- `findduplicates` [Boolean] : If files in course folders should be checked for duplicates (duplicates get not deleted)
- `findallduplicates` [Boolean] : If files in different courses should be checked for duplicates (duplicates get not deleted)
- `deleteduplicates` [Boolean] : If duplicates should be deleted. (works only if findduplicates and/or findallduplicates is set to true) 
- `informationaboutduplicates` [Boolean] : If a information file should be created in a folder with duplicates. The file inform about the duplicates. (works only if findduplicates and/or findallduplicates is set)
- `downloadcoursepages` [Boolean] : If the course main page should be downloaded
- `crawlcourseslink` [String] : Moodle Course Crawler startpoint (Default course/index.php = all Courses). This is not necessary for the Moodle Crawler Script
- `dontcrawl` [List] : A list of file extensions, that should not be crawled
- `colors` [Boolean] : If colors should be used (For Windows use Cmder to display colors correct. http://cmder.net/)
- `notifications` [Boolean] : If you want to get notified if new files were found
- `onlycrawlcourses` [List] : A list of course IDs, that should only be crawled. It creates a subset of courses that were found in the dashboard (option `allcourses` creates the superset). If the list is empty no courses will be ignored.
- `dontcrawlcourses` [List] : A list of course IDs, that should not be crawled. It creates a subset of courses that were found in the dashboard (option `allcourses` creates the superset). If the list is empty no courses will be ignored.
- `antirecrusion` [Boolean] : Default this prevent recrusive crawling of the same page. If you do missing files try to set this to `false`

All the files are stored in their respective directories inside the `root_dir` with the names as in moodle.

The crawler finds only coourses in your course list. So make sure that you check your settings of your course list on `https://whateverYourMoodleAdress/my` , so that every of your courses gets displayed there.

It is planed to build a script to login (and logout) from all courses on a moodle platform. For the moment there is a script called `moodleCourseCrawler.py` that uses the `crawlcourseslink` option. This script only logs all courses on the platform.


#### REQUIREMENTS

- Python 2
- Beautifulsoup - `sudo apt-get install python-beautifulsoup` or `sudo pip install beautifulsoup4`
- lxml or similar - `easy_install lxml` or see http://lxml.de/installation.html for more information.

If `colors` is set to true:
- Colorama - `sudo pip install colorama`
- Termcolor - `sudo pip install termcolor`

### EXTRAS

- Put `watch -n 3600 python moodleCrawler.py` in startup to fetch the files every hour.



This code is the modified version of the downloader created by Vinay Chandra



  Copyright 2017 Daniel Vogt

   This file is part of Moodle-Crawler.

   Moodle-Crawler is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   Moodle-Crawler is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with Moodle-Crawler.  If not, see <http://www.gnu.org/licenses/>.
