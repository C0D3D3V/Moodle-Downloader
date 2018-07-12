# Automatic Moodle Course Crawler

The `moodleCourseCrawler.py` script crawl all courses on a moodle platform. After running this script you get a list with a name and a link to each cours of the platform. 

Set the following in the file `config.ini` before running the script

- `root_dir` : The root directory for where the files are to be stored
- `url` : URL for moodle authentication
- `crawlcourseslink` : Moodle Course Crawler startpoint (Default course/index.php = all Courses) 
- `colors` : If colors should be used (For Windows use Cmder to display colors correct. http://cmder.net/)

#### REQUIREMENTS

- Python 2
- Beautifulsoup - `sudo apt-get install python-beautifulsoup` or `sudo pip install beautifulsoup4`
- lxml or similar - `easy_install lxml` or see http://lxml.de/installation.html for more information.

If `colors` is set to true:
- Colorama - `sudo pip install colorama`
- Termcolor - `sudo pip install termcolor`
