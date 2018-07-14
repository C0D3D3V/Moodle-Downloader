#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#  Copyright 2017 Daniel Vogt
#
#   This file is part of Moodle-Crawler.
#
#   Moodle-Crawler is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Moodle-Crawler is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Moodle-Crawler.  If not, see <http://www.gnu.org/licenses/>.



import cookielib
import urllib2
import urllib
import io
import os
import os.path
import hashlib
import sys
import stat
import md5
import re
import filecmp
import sys

from datetime import datetime
from ConfigParser import ConfigParser

try:
   from bs4 import BeautifulSoup
except Exception, e:
   print("Module BeautifulSoup4 is missing!")
   exit(1)

try:
   from colorama import init
except Exception, e:
   print("Module Colorama is missing!")
   exit(1)

try:
   from termcolor import colored
except Exception, e:
   print("Module Termcolor is missing!")
   exit(1)

# use Colorama to make Termcolor work on Windows too
init()


#utf8 shit
reload(sys)
sys.setdefaultencoding('utf-8')

def checkQuotationMarks(settingString):
   if not settingString is None and settingString[0] == "\"" and settingString[-1] == "\"":
      settingString = settingString[1:-1]
   if settingString is None:
      settingString = ""
   return settingString
 

def addSlashIfNeeded(settingString):
   if not settingString is None and not settingString[-1] == "/":
      settingString = settingString + "/"
   return settingString

def addBegSlashIfNeeded(settingString):
   if not settingString is None and not settingString[0] == "/":
      settingString =  "/" + settingString
   return settingString

#Log levels:
# - Level 0: Minimal Information + small Errors
# - Level 1: More Information + Successes 
# - Level 2: Doing Statemants + Found information
# - Level 3: More Errors + More Infos
# - Level 4: More Doing Statements + Dowload Info + Scann Dublicates
# - Level 5: More Download Info + More Info about dublicates

 
def log(logString, level=0):
   if level <= int(loglevel):
      if level == 0:
         print(datetime.now().strftime('%H:%M:%S') + " " + logString)
      elif level == 1:
         print(colored(datetime.now().strftime('%H:%M:%S') + " " + logString, "green")) 
      elif level == 2:
         print(colored(datetime.now().strftime('%H:%M:%S') + " " + logString, "yellow"))
      elif level == 3:
         print(colored(datetime.now().strftime('%H:%M:%S') + " " + logString, "red"))
      elif level == 4:
         print(colored(datetime.now().strftime('%H:%M:%S') + " " + logString, "magenta"))
      elif level == 5:
         print(colored(datetime.now().strftime('%H:%M:%S') + " " + logString, "cyan"))




def donwloadFile(downloadFileResponse):
   log("Download has started.", 4)
       
   downloadFileContent = ""
   
   if downloadFileResponse is None:
      log("Faild to download file", 4)
      return ""

   try:
       total_size = downloadFileResponse.info().getheader('Content-Length').strip()
       header = True
   except Exception:
       log("No Content-Length available.", 5)
       header = False # a response doesn't always include the "Content-Length" header
          
   if header:
       total_size = int(total_size)
         
   bytes_so_far = 0
        
   while True:
       downloadFileContentBuffer = downloadFileResponse.read(8192)
       if not downloadFileContentBuffer: 
           break
           
       bytes_so_far += len(downloadFileContentBuffer) 
       downloadFileContent = downloadFileContent + downloadFileContentBuffer
              
       if not header: 
          log("Downloaded %d bytes" % (bytes_so_far), 5)
           
       else:
          percent = float(bytes_so_far) / total_size
          percent = round(percent*100, 2)
          log("Downloaded %d of %d bytes (%0.2f%%)\r" % (bytes_so_far, total_size, percent), 5)
            
          
   log("Download complete.", 4)
   return downloadFileContent

 


#status:
# 0 - Not logged in
# 1 - Logged in
# 2 - Had to re login
# 3 - Something went wrong

def checkLoginStatus(pageContent):
   PageSoup = BeautifulSoup(pageContent, "lxml") 
   LoginStatusConntent = PageSoup.find(class_="logininfo")
   if not LoginStatusConntent is None:
   
      log("Checking login status.", 4)  
      #Lookup in the Moodle source if it is standard (login / log in on every page)
      #Is a relogin needed ? Try to figure out when relogin is needed.
      if "Logout" not in str(LoginStatusConntent) and "logout" not in str(LoginStatusConntent):
         log("Try to relogin, connection maybe lost.", 3)
         
         try:
            responseLogin = urllib2.urlopen(req, timeout=10)
         except Exception as e:
            raise NotGoodErrror(e)
          
         LoginContents = donwloadFile(responseLogin)
          
          
         if "errorcode=" in responseLogin.geturl():
             log("Cannot login. Check your login data.", 3)
             return 0
         
         #Lookup in the Moodle source if it is standard   ("Logout" on every Page)
         LoginSoup = BeautifulSoup(LoginContents, "lxml") 
         LoginStatusConntent = LoginSoup.find(class_="logininfo")
         if LoginStatusConntent is None or ("Logout" not in str(LoginStatusConntent) and "logout" not in str(LoginStatusConntent)):  
             log("Cannot connect to moodle or Moodle has changed. Crawler is not logged in. Check your login data.", 3)
             return 0
           
         log("Successfully logged in again.", 4)
         #reload page  
         return 2
      else:
         log("Crawler is still loged in.", 4)
         return 1
   else:
      log("No logininfo on this page.", 5)
      return 3    



def decodeFilename(fileName):
  htmlDecode = urllib.unquote(fileName).decode('utf8')
  htmlDecode = htmlDecode.replace('/', '-').replace('\\', '-').replace(' ', '-').replace('#', '-').replace('%', '-').replace('&', '-').replace('{', '-').replace('}', '-').replace('<', '-')
  htmlDecode = htmlDecode.replace('>', '-').replace('*', '-').replace('?', '-').replace('$', '-').replace('!', '-').replace(u'‘', '-').replace('|', '-').replace('=', '-').replace(u'`', '-').replace('+', '-')
  htmlDecode = htmlDecode.replace(':', '-').replace('@', '-').replace('"', '-')
  return htmlDecode




def crawlCourses(searchIn, ebene = 0, leftlinks = 0):
   log("Now in level: " + str(ebene))
         
   #Lookup in the Moodle source if it is standard (moodlePath/my/ are my courses)
   try:
      responseCourses = urllib2.urlopen(searchIn, timeout=10)
   except Exception:
      log("Connection lost! It is not possible to connect to moodle!", 3)
      return

   CoursesContents = donwloadFile(responseCourses)
   
     
   if "text/html" in responseCourses.info().getheader('Content-Type'): 
      try:
         loginStatus = checkLoginStatus(CoursesContents) 
      except Exception:
         log("Connection lost! It is not possible to connect to course list page!", 3)
         return
            
      if loginStatus == 0:
         return
      elif loginStatus == 2:
         log("Recheck Course: '" + searchIn + "'", 4)
         try:
            responseCourses = urllib2.urlopen(searchIn, timeout=10)
         except Exception:
            log("Connection lost! Course does not exist!", 3)
            return
         
         CoursesContents = donwloadFile(responseCourses)
          
      #elif loginStatus == 3:
         #this should not heppend
         #mh maybe continue ?  
          
   else:
       log("Ups, this seem not to be a moodle page.", 3)
       return


   CoursesContentsSoup = BeautifulSoup(CoursesContents, "lxml") 
   CoursesContentsList = CoursesContentsSoup.find(id="region-main")
    
    
   if CoursesContentsList is None:
      log("Unable to find courses", 3)
      return
      
   courseCategoryList = CoursesContentsList.find_all(class_="categoryname")
   courseNameList = CoursesContentsList.find_all(class_="coursename")

   leftlinks += len(courseCategoryList)
   
   
   for catergory_string in courseCategoryList:
      log("Links to crawl: " + str(leftlinks) + ". Now in level: " + str(ebene), 1)
      categoryLink = catergory_string.find("a")
      if not categoryLink is None:
         category_name = decodeFilename(categoryLink.text).strip("-")
         category_link = categoryLink.get('href')
         log("Entering Category: " + category_name + " (" + category_link + ")", 2)
         crawlCourses(category_link, ebene + 1, leftlinks)
      leftlinks -= 1

   for course_string in courseNameList:
      courseLink = course_string.find("a")
      if not courseLink is None:
         course_name = decodeFilename(courseLink.text).strip("-")
         course_link = courseLink.get('href')
         
         global courselogFile

         if not course_link in courselogFile: 
            log("Found new Course: " + course_name + " (" + course_link + ")") 
            externalLinkWriter = io.open(courseLinkFile, 'ab')
            externalLinkWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " " + course_name + ": "+  course_link + "\n")
            externalLinkWriter.close()
            courselogFileReader = io.open(courseLinkFile, 'rb')
            courselogFile = courselogFileReader.read()
            courselogFileReader.close()
   
   return





conf = ConfigParser()
project_dir = os.path.dirname(os.path.abspath(__file__))
conf.read(os.path.join(project_dir, '../config.ini'))
 


root_directory = checkQuotationMarks(conf.get("dirs", "root_dir"))
username = checkQuotationMarks(conf.get("auth", "username"))
password = checkQuotationMarks(conf.get("auth", "password"))
loglevel = checkQuotationMarks(conf.get("crawl", "loglevel"))
crawlcoursesink = addBegSlashIfNeeded(checkQuotationMarks(conf.get("crawl", "crawlcourseslink")))


authentication_url = checkQuotationMarks(conf.get("auth", "url"))

  

cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
opener.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36')]

urllib2.install_opener(opener)


payload = {
    'username': username,
    'password': password
}


courseLinkFile = root_directory + "courselinks.log" 

data = urllib.urlencode(payload)



moodlePath = ""
useSpecpath = False

if authentication_url.split('?')[0][-16:] == "/login/index.php":
   moodlePath = addSlashIfNeeded(authentication_url.split('?')[0][:-16])
else:
   useSpecpath = True
   log("This script will probably not work. Please use an authentication URL that ends with /login/index.php or contact the project owner.")


if not crawlcoursesink.startswith("/course/index.php"):
   log("This script will probably not work. Please use an course URL that starts with /course/index.php or contact the project owner.")



log("Moodle Course Crawler started working.")

# Connection established?
log("Try to login...", 2)

req = urllib2.Request(authentication_url, data)
#response = urllib2.urlopen(req)
try:
   responseLogin = urllib2.urlopen(req, timeout=10)
except Exception:
   log("Connection lost! It is not possible to connect to moodle!")
   exit(1)
LoginContents = donwloadFile(responseLogin)
 
if "errorcode=" in responseLogin.geturl():
    log("Cannot login. Check your login data.")
    exit(1)

#Lookup in the Moodle source if it is standard   ("Logout" on every Page)
LoginSoup = BeautifulSoup(LoginContents, "lxml") 
LoginStatusConntent = LoginSoup.find(class_="logininfo")
if LoginStatusConntent is None or ("Logout" not in str(LoginStatusConntent) and "logout" not in str(LoginStatusConntent)): 
   log("Cannot connect to moodle or Moodle has changed. Crawler is not logged in. Check your login data.") 
   exit(1)


log("Logged in!", 1)
 
 

#Lookup in the Moodle source if it is standard (Domain + subfolder)
mainpageURL = addSlashIfNeeded(responseLogin.geturl())
 
 
if useSpecpath == False:
   mainpageURL = moodlePath


 
 #create necessary stuff 

if not os.path.isfile(courseLinkFile):
   courselogFileReader = io.open(courseLinkFile, 'ab') 
   courselogFileReader.close()

courselogFileReader = io.open(courseLinkFile, 'rb')
courselogFile = courselogFileReader.read()
courselogFileReader.close()

if not os.path.isdir(root_directory):
   os.makedirs(root_directory)    

crawlCourses(mainpageURL + crawlcoursesink)  #"course/index.php"
 
  
#blockCourse = True
  

log("Update Complete")
