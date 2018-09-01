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
import cgi
import fnmatch
import datetime as dt

from datetime import datetime
from ConfigParser import ConfigParser
from urlparse import urlparse


import gi
gi.require_version('Notify', '0.7') 
from gi.repository import Notify

Notify.init("Moodle Crawler")

#logvariable
loglevel = 5
useColors = "false"
config_path = 'config.ini'


progressmessagelength = 0



#Import Libs if needed
try:
   from bs4 import BeautifulSoup
   from bs4.element import Comment
except Exception as e:
   print("Module BeautifulSoup4 is missing!")
   exit(1)

#utf8 shit
reload(sys)
sys.setdefaultencoding('utf-8')



#Log levels:
# - Level 0: Minimal Information + small Errors
# - Level 1: More Information + Successes  + dublicates deleted
# - Level 2: Doing Statemants + Found information
# - Level 3: More Errors + More Infos
# - Level 4: More Doing Statements + Dowload Info + Scann Dublicates
# - Level 5: More Download Info + More Info about dublicates

 
def log(logString, level=0):
   logString = logString.encode('utf-8')
   if useColors == "true":
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
   else:
      if level <= int(loglevel):
         if level == 0:
            print(datetime.now().strftime('%H:%M:%S') + " " + logString)
         elif level == 1:
            print(datetime.now().strftime('%H:%M:%S') + " " + logString) 
         elif level == 2:
            print(datetime.now().strftime('%H:%M:%S') + " " + logString)
         elif level == 3:
            print(datetime.now().strftime('%H:%M:%S') + " " + logString)
         elif level == 4:
            print(datetime.now().strftime('%H:%M:%S') + " " + logString)
         elif level == 5:
            print(datetime.now().strftime('%H:%M:%S') + " " + logString)



def checkQuotationMarks(settingString):

   if not settingString is None and  len(settingString) > 2 and settingString[0] == "\"" and settingString[-1] == "\"":
      settingString = settingString[1:-1]
   if settingString is None:
      settingString = ""
   return settingString
 


def addSlashIfNeeded(settingString):
   if not settingString is None and not settingString[-1] == "/":
      settingString = settingString + "/"
   return settingString


def addQuestionmarkIfNeeded(settingString):
   if not settingString is None and not settingString[-1] == "?":
      settingString = settingString + "?"
   return settingString


def normPath(pathSring):
   return os.path.normpath(pathSring)



def removeSpaces(pathString):
   return pathString.replace(" ", "")

def checkBool(variable, name):
   if variable == "true" or variable == "false":
      return
   else:
      log("Error parsing Variable. Please check the config file for variable: " + name + ". This variable should be 'true' or 'false'", 0)
      exit()


def checkInt(variable, name):
   if variable.isdigit():
      return int(variable)
   else:
      log("Error parsing Variable. Please check the config file for variable: " + name + ". This variable should be an integer", 0)
      exit()



def progress(count, total, suffix=''):
    bar_len = 30
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)
    
    progressmessage = '[%s] %s%% ...%s\r' % (bar, percents, suffix)
    global progressmessagelength
    progressmessagelength = len(progressmessage)

    sys.stdout.write(progressmessage)
    sys.stdout.flush()

def clearprogress():
    progressclearmessage = ''.ljust(progressmessagelength) + "\r"
    sys.stdout.write(progressclearmessage)
    sys.stdout.flush()

def checkConf(cat, name):
  global conf
  try: 
     return checkQuotationMarks(conf.get(cat, name))
  except Exception as e:
     log("Variable in config is missing. Please set the variable: " + name + " in the config file in section: " + cat, 0)
     exit()  


#get Config
conf = ConfigParser()
project_dir = os.path.dirname(os.path.abspath(__file__))
conf.read(os.path.join(project_dir, config_path))
   
root_directory = checkConf("dirs", "root_dir")
root_directory = normPath(root_directory)


username = checkConf("auth", "username") 
password = checkConf("auth", "password") 
authentication_url = checkConf("auth", "authurl")  
base_url = checkConf("auth", "baseurl")  
useauthstate = checkConf("auth", "useauthstate")  
reLoginOnFile = checkConf("auth", "reloginonfile")  

crawlallcourses = checkConf("crawl", "allcourses")
crawlforum = checkConf("crawl", "forum")
crawlwiki = checkConf("crawl", "wiki")
usehistory = checkConf("crawl", "history")
downloadExternals = checkConf("crawl", "externallinks") 
findallduplicates = checkConf("crawl", "findallduplicates") 
findduplicates = checkConf("crawl", "findduplicates") 
deleteduplicates = checkConf("crawl", "deleteduplicates") 
downloadcoursepages = checkConf("crawl", "downloadcoursepages") 
informationaboutduplicates = checkConf("crawl", "informationaboutduplicates") 
loglevel = checkConf("crawl", "loglevel") 
maxdepth = checkConf("crawl", "maxdepth") 
dontcrawl = checkConf("crawl", "dontcrawl") 
onlycrawlcourses = checkConf("crawl", "onlycrawlcourses") 
dontcrawlcourses = checkConf("crawl", "dontcrawlcourses")
antirecrusion = checkConf("crawl", "antirecrusion")
 
useColors = checkConf("other", "colors") 
notifyFound = checkConf("other", "notifications") 



 
#check variables:
if not os.path.isdir(root_directory):
    log("Error parsing Variable. Please check the config file for variable: root_dir. This variable should be a path to an existing folder.", 0)
    exit()

checkBool(crawlallcourses, "allcourses")
checkBool(crawlforum, "forum")
checkBool(crawlwiki, "wiki")
checkBool(usehistory, "history")
checkBool(downloadExternals, "externallinks")
checkBool(findallduplicates, "findallduplicates")
checkBool(findduplicates, "findduplicates")
checkBool(deleteduplicates, "deleteduplicates")
checkBool(downloadcoursepages, "downloadcoursepages")
checkBool(informationaboutduplicates, "informationaboutduplicates")
checkBool(useColors, "colors")
checkBool(useauthstate, "useauthstate")
checkBool(notifyFound, "notifications")
checkBool(reLoginOnFile, "reloginonfile")
checkBool(antirecrusion, "antirecrusion")

loglevel = checkInt(loglevel, "loglevel")
maxdepth = checkInt(maxdepth, "maxdepth")

listOnlyCrawlCourses = onlycrawlcourses.split(",")
listDontCrawlCourses = dontcrawlcourses.split(",")
listDontCrawl = dontcrawl.split(",")

#add colors
if useColors == "true":
   try:
      from colorama import init
   except Exception as e:
      print("Module Colorama is missing!")
      exit(1)
   
   try:
      from termcolor import colored
   except Exception as e:
      print("Module Termcolor is missing!")
      exit(1)

   # use Colorama to make Termcolor work on Windows too
   init()



#Setup Dump Search    
filesBySize = {}


#Setup Loader
cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
opener.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36')]
urllib2.install_opener(opener)


#setup crawler live history
visitedPages = set() #hashtable -> faster !?


def walker(arg, dirname, fnames):
    d = os.getcwd()
    os.chdir(dirname)
    global filesBySize

    try:
        fnames.remove('Thumbs')
    except ValueError:
        pass
    for f in fnames:
        if not os.path.isfile(f):
            continue
        size = os.stat(f)[stat.ST_SIZE]
        #print f + " size: " + str(size)
        if size < 100:
            continue
        if filesBySize.has_key(size):
            a = filesBySize[size]
        else:
            a = []
            filesBySize[size] = a
        a.append(os.path.join(dirname, f))
    os.chdir(d)


def donwloadFile(downloadFileResponse):
   log("Download has started.", 4)
       
   downloadFileContent = ""
   
   if downloadFileResponse is None:
      log("Faild to download file", 4)
      return ""

   header = False
   try:
       total_size = downloadFileResponse.info().getheader('Content-Length').strip()
       header = True
   except Exception as e:
       log("No Content-Length available.", 5)
       header = False # a response doesn't always include the "Content-Length" header
    
   if header:
       total_size = int(total_size)
         
   bytes_so_far = 0
        
   #if not header: 
   #   log("Downloading a file", 0)
   
   tenmegabyte = 0
   bytespersec = 0
   MBbytespersec = 0

   starttime = dt.datetime.now()
   bytesSineLasteCalc = 0

   while True:
       downloadFileContentBuffer = downloadFileResponse.read(81924)
       if not downloadFileContentBuffer: 
           break
           
       bytes_so_far += len(downloadFileContentBuffer) 
       downloadFileContent = downloadFileContent + downloadFileContentBuffer
       

       #calc speed
       endtime = dt.datetime.now()
       
       if (endtime - starttime).total_seconds() >= 1:
          bytespersec = (bytes_so_far - bytesSineLasteCalc) / (endtime - starttime).total_seconds()
          MBbytespersec = bytespersec / 1024 / 1024
          starttime = dt.datetime.now()
          bytesSineLasteCalc = bytes_so_far
       

       if not header: 
         tenmegabyte += 81924
         
         if tenmegabyte >= 10485760:
            tenmegabyte = 0 
            log("Downloaded %d bytes (%dByts/s | %0.2f%%MByts/s)" % (bytes_so_far, bytespersec, MBbytespersec), 0)
         
         log("Downloaded %d bytes" % (bytes_so_far), 5)
           
       else: 
          progress(bytes_so_far, total_size, "%d/%dB %0.2fMB/s\r" % (bytes_so_far, total_size, MBbytespersec))
   
   #if header:  
   #   print ""

   clearprogress()
 
   log("Download complete.", 4)
   return downloadFileContent



def saveFile(webFileFilename, pathToSave, webFileContent, webFileResponse, webFileHref):
   if webFileFilename == "":
      webFileFilename = "index.html"
            
   if webFileFilename.split('.')[-1] == webFileFilename:
      webFileFilename = webFileFilename + ".html"


   file_name = normPath(addSlashIfNeeded(pathToSave) + webFileFilename)

   if file_name[-4:] == ".php":
      file_name = file_name[:len(file_name) - 4] + ".html"
   
   #file_name = urllib.unquote(url).decode('utf8')


   if not os.path.isdir(pathToSave):
      os.makedirs(pathToSave)


   filetype = "." + file_name.split('.')[-1]
   fileBeginn = file_name[:(len(file_name) - len(filetype))]
   fileName = fileBeginn.split(os.sep)[-1]
   pathtoSearch = fileBeginn[:(len(fileBeginn) - len(fileName))]

   fileend = file_name.split('.')[-1]
   filebegin = file_name[:(len(file_name) - len(fileend)) - 1]

   if os.path.isfile(file_name): 
                 
      ii = 1
      while True:
       new_name = filebegin + "_" + str(ii) + "." + fileend
       if not os.path.isfile(new_name):
          file_name = new_name
          break
       ii += 1


   try:
     pdfFile = io.open(file_name, 'wb')
     pdfFile.write(webFileContent)
     webFileResponse.close()
     pdfFile.close()

   except Exception as e:
        log('File was not created: "file://' +  file_name + '"' + "Exception: " + str(e))
        return file_name


    
   fileWasDeleted = False
  

   fileWasDeleted = searchfordumpsSpecific(file_name,fileName ,filetype, pathtoSearch)


   if fileWasDeleted == False:
      log('Creating new file: "file://' +  file_name + '"')
      if notifyFound == "true":
         Notify.Notification.new("Moodle Crawler: New File found!").show()
   return file_name


#adds an entry to the log file ... so that the file gets not recrawled
def addFileToLog(pageLink, filePath):
   logFileWriter = io.open(crawlHistoryFile, 'ab')
   logFileWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " "+ pageLink + " saved to '" + filePath + "'\n")
   logFileWriter.close()
   global logFile
   logFileReader = io.open(crawlHistoryFile, 'rb')
   logFile = logFileReader.read()
   logFileReader.close()



def addHashToLog(pageDir, calcHash):
   logFileWriter = io.open(crawlHistoryFile, 'ab')
   logFileWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " "+ pageDir + " calculated hash " + calcHash + "\n")
   logFileWriter.close()
   global logFile
   logFileReader = io.open(crawlHistoryFile, 'rb')
   logFile = logFileReader.read()
   logFileReader.close()



#moodlePage is Content not Soup
def simpleLoginCheck(moodlePage): 
 # print moodlePage
  if moodlePage.find("logout.php") >= 0: 
    return True 
  else:
    return False


def simpleMoodleCheck(moodlePage): 
 # print moodlePage
  if moodlePage.find("moodle") >= 0: 
    return True 
  else:
    return False



def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True


def text_from_html(body):
    soup = BeautifulSoup(body, 'lxml')
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)  
    return u" ".join(t.strip() for t in visible_texts)


#status:
# 0 - Not logged in
# 1 - Logged in
# 2 - Had to re login
# 3 - Something went wrong

def checkLoginStatus(pageContent):
   PageSoup = BeautifulSoup(pageContent, "lxml") 
   #LoginStatusConntent = PageSoup.find(class_="logininfo")
   #LoginStatusConntent = PageSoup.select(".logininfo")

   #if not LoginStatusConntent is None or len(LoginStatusConntent) == 0:
   
   
   log("Checking login status.", 4)  
   #Lookup in the Moodle source if it is standard (login / log in on every page)
   #Is a relogin needed ? Try to figure out when relogin is needed.
   if not simpleLoginCheck(pageContent):
   #if "Logout" not in str(LoginStatusConntent[-1]) and "logout" not in str(LoginStatusConntent[-1]):
      log("Try to relogin, connection maybe lost.", 3)
 
      global req
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
      #LoginStatusConntent = LoginSoup.find(class_="logininfo")
      #LoginStatusConntent = PageSoup.select(".logininfo")
     
      #if LoginStatusConntent is None or ("Logout" not in str(LoginStatusConntent[-1]) and "logout" not in str(LoginStatusConntent[-1])):  
      if not simpleLoginCheck(LoginContents):
          log("Cannot connect to moodle or Moodle has changed. Crawler is not logged in. Check your login data.", 3)
          return 0
        
      log("Successfully logged in again.", 4)
      #reload page  
      return 2
   else:
      log("Crawler is still loged in.", 4)
      return 1
   #else:
   #   log("No logininfo on this page.", 5)
   #   return 3    



def decodeFilename(fileName):

  htmlDecode = urllib.unquote(fileName).decode('utf8')
  htmlDecode = htmlDecode.replace('/', '-').replace('\\', '-').replace(' ', '-').replace('#', '-').replace('%', '-').replace('&', '-').replace('{', '-').replace('}', '-').replace('<', '-')
  htmlDecode = htmlDecode.replace('>', '-').replace('*', '-').replace('?', '-').replace('$', '-').replace('!', '-').replace(u'‘', '-').replace('|', '-').replace('=', '-').replace(u'`', '-').replace('+', '-')
  htmlDecode = htmlDecode.replace(':', '-').replace('@', '-').replace('"', '-')
  old = urllib.unquote(fileName).decode('utf8')
  if(old != htmlDecode):
  	log("Changed filename from '" + old + "'' to '" + htmlDecode + "'", 5)

  return htmlDecode

def dontCrawlCheck(url):
   extension = url.split("?")[0].split(".")[-1]
   if dontcrawl == "":
      return False

   if not extension is None and extension in listDontCrawl:
      return True
   return False


def onlyCrawlCoursesCheck(url):
   coursId = url.split("?")[1].split("&")[0].split("=")[1]
   if onlycrawlcourses == "":
      return True
   
   if not coursId is None and coursId in listOnlyCrawlCourses:
      return True
   return False

def dontCrawlCoursesCheck(url):
   coursId = url.split("?")[1].split("&")[0].split("=")[1]
   if dontcrawlcourses == "":
      return False
   
   if not coursId is None and coursId in listDontCrawlCourses:
      return True
   return False

#warning this function exit the stript if it could not load the course list page
#try to crawl all courses from moodlepage/my/
def findOwnCourses(myCoursesURL):
   log("Searching Courses...", 2)
   
   #Lookup in the Moodle source if it is standard (moodlePath/my/ are my courses)
   try:
      if crawlallcourses == "true":
         responseCourses = urllib2.urlopen(myCoursesURL + "my/index.php?mynumber=-2", timeout=10) 
      else:
         responseCourses = urllib2.urlopen(myCoursesURL + "my/", timeout=10) 
   except Exception as e:
      log("Connection lost! It is not possible to connect to course page! At: " + myCoursesURL)
      log("Exception details: " + str(e), 5)
      exit(1)
   CoursesContents = donwloadFile(responseCourses)
   
   
   
   
   CoursesContentsSoup = BeautifulSoup(CoursesContents, "lxml")
   
   CoursesContentsList = CoursesContentsSoup.find(id="region-main")
   
   
   #CoursesContentsList = CoursesContents.split('class="block_course_list  block list_block"')[1].split('class="footer"')[0]
   #>Meine Kurse</h2>
    
   if CoursesContentsList is None:
      log("Unable to find courses")
      log("Full page: " +  str(CoursesContents), 5)
      exit(1)
      
   #courseNameList = CoursesContentsList.find_all(class_="course_title")
   courseNameList = CoursesContentsList.select(".coursebox")
   
   #regexCourseName = re.compile('class="course_title">(.*?)</div>')
   #course_list = regexCourseName.findall(str(CoursesContentsList))
   courses = []
       
   #blockCourse = True
   
   for course_string in courseNameList:
       #aCourse = course_string.find('a')
       aCourse = course_string.select("h3 a, h2 a")
       #course_name = aCourse.text.encode('ascii', 'ignore').replace('/', '|').replace('\\', '|').replace(' ', '_').replace('.', '_')
   
       if aCourse is None or len(aCourse) == 0:
          log("No link to this course was found!", 3)
          log("Full page: " +  str(course_string), 5)
          continue
   
       course_name = decodeFilename(aCourse[0].text).strip("-")
   
       course_link = removeSpaces(aCourse[0].get('href'))
       #if course_name == "TINF15B5: Programmieren \ Java":
       #   blockCourse = False
   
       #if blockCourse == False:
       if not onlyCrawlCoursesCheck(course_link):
          log("Course " + course_name + " will not be crawled because the course id is not given in option 'onlycrawlcourses'.", 3)
          continue

       if dontCrawlCoursesCheck(course_link):
          log("Course" + course_name +" will not be crawled because the course id is given in option 'dontcrawlcourses'.", 3)
          continue


       courses.append([course_name, course_link])
       log("Found Course: '" + course_name + "'", 2)


   if len(courses) == 0:
      log("Unable to find courses")
      log("Full page: " + str(CoursesContentsList), 5)

   return courses


 

def searchfordumpsSpecific(filepath, fileName, filetype, pathtoSearch):
    #find dublication in folder pathtoSearch with specific filename and filetype without subfolders
      #filetype = "." + filepath.split('.')[-1]
      #fileBeginn = filepath[:(len(filepath) - len(filetype))]
      #fileName = fileBeginn.split(os.sep)[-1]
      #pathtoSearch = fileBeginn[:(len(fileBeginn) - len(fileName))]


    filesBySizeSpe = {}
    log('Scanning directory "' + pathtoSearch + '" (file: "file://' + filepath + '", filename: "' + fileName + '", filetype: "' + filetype +'")....' , 5)
    
    if not os.path.isfile(filepath):
        log('Error: "file://' + filepath + '" is not a file.') 
        return False

    coresize = os.stat(filepath)[stat.ST_SIZE]

    fnames = fnmatch.filter(os.listdir(pathtoSearch), fileName + '*' + filetype)
     
    for f in fnames:
        f = pathtoSearch + f

        if not os.path.isfile(f):
            continue
        size = os.stat(f)[stat.ST_SIZE]
        #print f + " size: " + str(size)
        if not size == coresize:
            continue
        if filesBySizeSpe.has_key(size):
            a = filesBySizeSpe[size]
        else:
            a = []
            filesBySizeSpe[size] = a
        a.append(f)
   
    log('Finding potential dupes...', 4)
    potentialDupes = []
    potentialCount = 0
    trueType = type(True)
    sizes = filesBySizeSpe.keys()
    sizes.sort()
    for k in sizes:
        inFiles = filesBySizeSpe[k]
        outFiles = []
        hashes = {}
        if len(inFiles) is 1:
          continue

        log('Testing %d files of size %d...' % (len(inFiles), k), 5)
        for fileNameSingle in inFiles:
            if not os.path.isfile(fileNameSingle):
                continue
            aFile = file(fileNameSingle, 'r')
            hasher = md5.new(aFile.read(1024))
            hashValue = hasher.digest()
            if hashes.has_key(hashValue):
                x = hashes[hashValue]
                if type(x) is not trueType:
                    outFiles.append(hashes[hashValue])
                    hashes[hashValue] = True
                outFiles.append(fileNameSingle)
            else:
                hashes[hashValue] = fileNameSingle
            aFile.close()
        if len(outFiles):
            potentialDupes.append(outFiles)
            potentialCount = potentialCount + len(outFiles)
    del filesBySizeSpe

    log('Found %d sets of potential dupes...' % potentialCount, 5)
    log('Scanning for real dupes...', 5)

    dupes = []
    for aSet in potentialDupes:
        outFiles = []
        hashes = {}
        for fileNameSingle in aSet:
            log('Scanning file "%s"...' % fileNameSingle, 5)
            aFile = file(fileNameSingle, 'r')
            hasher = md5.new()
            while True:
                r = aFile.read(4096)
                if not len(r):
                    break
                hasher.update(r)
            aFile.close()
            hashValue = hasher.digest()
            if hashes.has_key(hashValue):
                if not len(outFiles):
                    outFiles.append(hashes[hashValue])
                outFiles.append(fileNameSingle)
            else:
                hashes[hashValue] = fileNameSingle
        if len(outFiles):
            dupes.append(outFiles)
  
    foundfilepath = False
    foundDupes = None
    for d in dupes:
        log('Test for correct dumps', 5)
        if len(d) > 1:
          for f in d:
              if f == filepath:
                log('Found correct dump - filepath: "file://' + f + '"', 4)
                foundfilepath = True
                foundDupes = d    

    
    #old ... deletes all founds :/
    #for d in dupes:
    #    log('Original is %s' % d[0], 1)
    #    for f in d[1:]:
    #        log('Deleting %s' % f, 1)
    #        os.remove(f) 

    #delete only searched tupple
    if not foundDupes is None: 
        log('Original is %s' % foundDupes[0], 4)
        for f in foundDupes[1:]:
            log('Deleting %s' % f, 4)
            os.remove(f) 

    return foundfilepath



def searchfordumps(pathtoSearch):
    #find dublication in folder  pathtoSearch
    global filesBySize
    filesBySize = {}
    log('Scanning directory "%s"....' % pathtoSearch, 5)
    os.path.walk(pathtoSearch, walker, filesBySize)

    log('Finding potential dupes...', 4)
    potentialDupes = []
    potentialCount = 0
    trueType = type(True)
    sizes = filesBySize.keys()
    sizes.sort()
    for k in sizes:
        inFiles = filesBySize[k]
        outFiles = []
        hashes = {}
        if len(inFiles) is 1:
          continue

        log('Testing %d files of size %d...' % (len(inFiles), k), 5)
        for fileName in inFiles:
            if not os.path.isfile(fileName):
                continue
            aFile = file(fileName, 'r')
            hasher = md5.new(aFile.read(1024))
            hashValue = hasher.digest()
            if hashes.has_key(hashValue):
                x = hashes[hashValue]
                if type(x) is not trueType:
                    outFiles.append(hashes[hashValue])
                    hashes[hashValue] = True
                outFiles.append(fileName)
            else:
                hashes[hashValue] = fileName
            aFile.close()
        if len(outFiles):
            potentialDupes.append(outFiles)
            potentialCount = potentialCount + len(outFiles)
    del filesBySize

    log('Found %d sets of potential dupes...' % potentialCount, 5)
    log('Scanning for real dupes...', 5)

    dupes = []
    for aSet in potentialDupes:
        outFiles = []
        hashes = {}
        for fileName in aSet:
            log('Scanning file "%s"...' % fileName, 5)
            aFile = file(fileName, 'r')
            hasher = md5.new()
            while True:
                r = aFile.read(4096)
                if not len(r):
                    break
                hasher.update(r)
            aFile.close()
            hashValue = hasher.digest()
            if hashes.has_key(hashValue):
                if not len(outFiles):
                    outFiles.append(hashes[hashValue])
                outFiles.append(fileName)
            else:
                hashes[hashValue] = fileName
        if len(outFiles):
            dupes.append(outFiles)

    i = 0
    for d in dupes:
        log('Original is %s' % d[0], 4)
        for f in d[1:]:
            i = i + 1
            if deleteduplicates == "true":
               log('Deleting %s' % f, 4)
               os.remove(f) 
            if informationaboutduplicates == "true":
               logDuplicates(f, d[0])




#log Duplicates
def logDuplicates(dubPath, oriPath):
   fileName = dubPath.split(os.sep)[-1]
   dubDir = dubPath[:(len(dubPath) - len(fileName) )]

   if not os.path.isdir(dubDir):
      os.makedirs(dubDir)   
   
   dubLogPath = normPath(addSlashIfNeeded(dubDir) + "duplicates.log")


   if os.path.isfile(dubLogPath):
      dubLogReadeer = io.open(dubLogPath, 'rb')
      dubLog = dubLogReadeer.read()
      dubLogReadeer.close()
      if not dubPath in dubLog:
         log('I will store information about the duplicates in the "file://' + dubLogPath + '" file.', 4)
         dubLogWriter = io.open(dubLogPath, 'ab')
         dubLogWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " "+ dubPath + " was found in this place " + oriPath + "\n")
         dubLogWriter.close()
         

      else:
         log('This duplicates were found before and loged in the "file://' + dubLogPath + '" file earlier. Inform the project maintainer pleace.', 5)

   else:
      log('I will store information about the duplicates in the ""file://' + dubLogPath + '" file.', 4)
      dubLogWriter = io.open(dubLogPath, 'ab')
      dubLogWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " "+ dubPath + " was found in this place " + oriPath + "\n")
      dubLogWriter.close()

   

#log External Link toLog file and File in Folder
def logExternalLink(extlink, extname, extLinkDir):
    if not os.path.isdir(extLinkDir):
      os.makedirs(extLinkDir)   

    file_name = normPath(addSlashIfNeeded(extLinkDir) + extname + ".desktop")
    if os.name == "nt":
        file_name = normPath(addSlashIfNeeded(extLinkDir) + extname + ".URL")
        
    boolExternalLinkStored = True


 
    new_name = file_name
    fileend = file_name.split('.')[-1]
    filebegin = file_name[:(len(file_name) - len(fileend)) - 1]
    
      
    ii = 1
    while True:
        if not os.path.isfile(new_name):
            file_name = new_name
            log('I will store the external link ' + extlink + ' in "file://' + file_name + '".', 0)
            externalLinkWriter = io.open(file_name, 'ab')
            if os.name == "nt":
                externalLinkWriter.write(""""[InternetShortcut]
URL=""" + extlink)
            else:
                externalLinkWriter.write("""[Desktop Entry]
Encoding=UTF-8
Name=""" + extname + """                 
Type=Link
URL=""" + extlink + """
Icon=text-html
Name[en_US]=""" + extname)

            externalLinkWriter.close()
            break
        else:
            externalLinkReadeer = io.open(new_name, 'rb')
            externallinks = externalLinkReadeer.read()
            externalLinkReadeer.close()
            if extlink in externallinks:
                file_name = new_name
                log('This link was stored in the "file://' + file_name + '" file earlier.', 5)
                boolExternalLinkStored = False
                break;
        
        new_name = filebegin + "_" + str(ii) + "." + fileend
        ii += 1

    
         
    if boolExternalLinkStored == True:
      logFileWriter = io.open(crawlHistoryFile, 'ab')
      logFileWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " External: "+ extlink + " saved to '" + file_name + "'\n")
      logFileWriter.close()
      global logFile
      logFileReader = io.open(crawlHistoryFile, 'rb')
      logFile = logFileReader.read()
      logFileReader.close()

   



#try to crawl all links on a moodle page. And runs rekursive this funktion on it
def crawlMoodlePage(pagelink, pagename, parentDir, calledFrom, depth=0, forbidrecrusionfor=[]):

    if calledFrom is None or calledFrom == "":
       log("Something went wrong! CalledFrom is empty!", 2) 
       calledFrom = ""
    
    #check Parameter
    wrongParameter = False

    if pagelink is None or pagelink == "":
       log("Something went wrong! Pagelink is empty!", 2) 
       pagelink = ""
       wrongParameter = True
        
    if pagename is None or pagename == "":
       log("Something went wrong! Pagename is empty!", 2) 
       pagename = ""
        
    if parentDir is None or parentDir == "":
       log("Something went wrong! ParentDir is empty!", 2) 
       parentDir = ""
       wrongParameter = True
 
    log("Check page: '" + pagelink + "' named: '" + pagename + "' found on: '" + calledFrom + "' depth: " + str(depth) + " / " + str(maxdepth), 2) 

 
    if depth >= maxdepth:
       log("Max depth is reached! Please change the max depth if you want to crawl this link.", 2)
       return

    if wrongParameter == True:
       log("The parameters are to wrong. I return!", 2) 
       return

    #check if link is empty
    if pagelink is None or pagelink == "":
       log("There went something wrong, this is an empty link.", 3)
       return
 
    #korregiere link falls nicht korrekt
    if not pagelink.startswith("https://") and not pagelink.startswith("http://") and not pagelink.startswith("www."):
       if pagelink.startswith('/'):
          parsed_uri = urlparse(calledFrom)
          domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri) 
          pagelink = domain + pagelink[1:] 
       elif pagelink.startswith('#'):
          log("This is an bad link. I will not crawl it. It tries to kid me.", 3)
          return
       elif pagelink.startswith('mailto'):
          log("This is an bad link. I will not crawl it. It tries to kid me.", 3)
          return
       else:   
          #pagelink = calledFrom[:(len(calledFrom) - len(calledFrom.split('/')[-1])) - 1] + pagelink
          pagelink = calledFrom[:len(calledFrom) - len(calledFrom.split('/')[-1])] + pagelink

        


 
    pagelink = pagelink.split("#")[0]

    #check crawl history
    global logFile
    if usehistory == "true" and pagelink in logFile:
       log("This link was crawled in the past. I will not recrawl it, change the settings if you want to recrawl it.", 3)
       return

    #Add link to visited pages
    global visitedPages
    if pagelink in visitedPages:
       log("This link was viewed in the past. I will not reviewed it.", 3)
       return

    visitedPages.add(pagelink)




    #check if this is an external link
    isexternlink = False

    if not domainMoodle in pagelink:
       log("This is an external link.", 2)
       
       
       logExternalLink(pagelink, pagename, parentDir)
       
       isexternlink = True
       if downloadExternals == "false":
          log("Ups this is an external link. I do not crawl external links. Change the settings if you want to crawl external links.", 3)
          return


    #check if the page is in a forum
    if crawlforum == "false" and "/forum/" in pagelink and isexternlink == False:
       log("Ups this is a forum. I do not crawl this forum. Change the settings if you want to crawl forums.", 3)
       return
    
    #check if the page is in a wiki
    if crawlwiki == "false" and "/wiki/" in pagelink and isexternlink == False:
       log("Ups this is a wiki. I do not crawl this wiki. Change the settings if you want to crawl wikis.", 3)
       return


    #Skip Moodle Pages
    #/user/   = users                               | skipTotaly
    #/badges/ = Auszeichnungen                      | skipTotaly
    #/blog/ = blogs                                 | skipTotaly
    #/feedback/ = feedback page unwichtig ?         | skipTotaly

    #/choicegroup/ = gruppen wahl -- unwichtig ?    | skipTotaly
    #/groupexchange/ = gruppenwechsel unwichtig?    | skipTotaly
    #/calendar/ = kalender -- rekrusion!! unwicht.  | skipTotaly
    #/glossary/ = wörterbuch -- unwichtig           | skipTotaly
    #action=delchoice bzw. action= = aktionen -- nicht gut, sollten vom user getätigt werden | skipTotaly 
    if isexternlink == False:
       if "/user/" in pagelink or  "/badges/" in pagelink or "/blog/" in pagelink or "/feedback/" in pagelink or "/choicegroup/" in pagelink or "/groupexchange/" in pagelink or "/calender/" in pagelink or "/glossary/" in pagelink or "action=" in pagelink:
          log("This is a moodle page. But I will skip it because it is not important.", 4)
          return

    if dontCrawlCheck(pagelink):
       log("This page will not be crawled because it ends with a file extension given in option 'dontcrawl'.", 3)
       return
    
    #try to get a response from link
    try:
       responsePageLink = urllib2.urlopen(pagelink, timeout=10)
    except Exception as e:
       log("Connection lost! Page does not exist!", 2)
       log("Exception details: " + str(e), 5)
       return
   
    isSpecialExternLink = False
    realurl = responsePageLink.geturl()
    if isexternlink == False and not domainMoodle in realurl:
       log("This is an special external link.", 2)
       if usehistory == "true" and realurl in logFile:     
            log("This link was crawled in the past. I will not recrawl it, change the settings if you want to recrawl it.", 3)
            return

       logExternalLink(realurl, pagename, parentDir)
       
       isSpecialExternLink = True
       if downloadExternals == "false":
          log("Ups this is an external link. I do not crawl external links. Change the settings if you want to crawl external links.", 3)
          return


     
    #get the filename
    pageFileName = ""
    try:
       pageFileNameEnc = responsePageLink.info()['Content-Disposition']
       value, params = cgi.parse_header(pageFileNameEnc)
       pageFileName = params['filename']
    except Exception as e:
          log("No Content-Disposition available. Exception details: " + str(e), 5)
    if pageFileName is None or pageFileName == "":
       pageFileName = os.path.basename(urllib2.urlparse.urlsplit(pagelink).path)
    
    pageFileName = decodeFilename(pageFileName).strip("-")

    #is this page a html page
    pageIsHtml = False
    if "text/html" in responsePageLink.info().getheader('Content-Type') or pageFileName[-4:] == ".php" or pageFileName[-5:] == ".html":
       pageIsHtml = True

    #cheating: try to fix moodle page names
    if isexternlink == False and pageIsHtml == True:
       pageFileName = pagename + ".html"


    #stop recrusion
    forbidrecrusionforNew = forbidrecrusionfor[:]
    if not pagelink == calledFrom and pagelink.split('?')[0] == calledFrom.split('?')[0]: 
       log("Changing paramter detected! Recrusion posible!", 3)
       if antirecrusion == "true":
          if pagelink.split('?')[0] in forbidrecrusionfor:
            log("Stopping recrusion! If you do missing files, set the option 'antirecrusion' to 'false'.", 1)
            visitedPages.remove(pagelink)
            #TODO: add pagelink to a recrawl recruive list... 
            return
          else:
            forbidrecrusionforNew.append(pagelink.split('?')[0])
    

    PageLinkContent = donwloadFile(responsePageLink)
    
     
    #check for login status
    if pageIsHtml == True and reLoginOnFile == "true" and simpleMoodleCheck(PageLinkContent):

       try:
          loginStatus = checkLoginStatus(PageLinkContent) 
       except Exception as e:
          log("Connection lost! It is not possible to connect to moodle!", 3)
          log("Exception details: " + str(e), 5)
          return

       if loginStatus == 0:  #Not logged in
          log("Ups, there went something wrong with the moodle login - this is bad. If this happens again please contect the project maintainer.", 0)
          log("This page could not be crawled: " + pagelink)
          #try to donload anyway ? ++++++++++++++++++++++++++++++++++++

          return

       elif loginStatus == 2: #Relogged in
          log("Recheck Page: '" + pagelink + "'", 4)
          try:
             responsePageLink = urllib2.urlopen(pagelink, timeout=10)
          except Exception as e:
             log("Connection lost! Page does not exist!", 3)
             log("Exception details: " + str(e), 5)
             return
     
          PageLinkContent = donwloadFile(responsePageLink)
          
       elif loginStatus == 3: #Not a moodle Page
          if isexternlink == False:
             log("Strangely, this is not a moodle page! I did not expect that this is an external link!", 3)
             isexternlink = True
 

    pageDir = normPath(addSlashIfNeeded(parentDir) + pagename)

    pageFoundLinks = 0

    isaMoodlePage = False

    page_links = None
    course_section = None
    
    if pageIsHtml == True and isexternlink == False:
       PageSoup = BeautifulSoup(PageLinkContent, "lxml") 
 
       page_links_Soup = PageSoup.find(id="region-main") 

       if not page_links_Soup is None: 
          #build up own moodle page

          
          [s.decompose() for s in page_links_Soup.select("input[name=sesskey]")]
          
          #inputTags = page_links_Soup.select('input')
          #for inputB in inputTags:
          #    if inputB.has_attr('sesskey'):
          #        inputB['sesskey'] = ''

          aTags = page_links_Soup.select('a')
          for aBad in aTags:
            if aBad.has_attr('id'):
              if aBad['id'].startswith("action_link"):
                  del aBad['id']
          
          for dirtyTag in page_links_Soup.findAll(id=re.compile("^id_")):
             del dirtyTag['id']


          
          [s.decompose() for s in page_links_Soup.select(".questionflag")]
          [s.decompose() for s in page_links_Soup.select(".questionflagpostdata")]

          #fix broken html ... remove navigation
          [s.decompose() for s in page_links_Soup.select("aside")]

          #header without script tags
          moodlePageHeader = PageSoup.find("head")
          [s.decompose() for s in moodlePageHeader('script')]

          #[s.decompose() for s in moodlePageHeader('link')]
          
          stylesheetpattern = re.compile("^(.*)/styles.php/(.*)/\d*/(.*)$")
          faviconpattern = re.compile("^(.*)/image.php/(.*)/\d*/(.*)$")
          favicon2pattern = re.compile("^(.*)/pluginfile.php/(.*)/\d*/(.*)$")
            
          for s in moodlePageHeader.select('link'):
              m = stylesheetpattern.match(s['href'])
              if m != None:
                s['href'] = (m.group(1) + "/styles.php/" + m.group(2) + "/42/" + m.group(3))
                continue
              m = faviconpattern.match(s['href'])
              if m != None:
                s['href'] = (m.group(1) + "/image.php/" + m.group(2) + "/42/" + m.group(3)) 
                continue
              m = favicon2pattern.match(s['href'])
              if m != None:
                s['href'] = (m.group(1) + "/pluginfile.php/" + m.group(2) + "/42/" + m.group(3)) 
                continue
        

          for s in page_links_Soup.select('img'):
              m = stylesheetpattern.match(s['src'])
              if m != None:
                s['src'] = ( m.group(1) + "/styles.php/" + m.group(2) + "/42/" + m.group(3))
                continue
              m = faviconpattern.match(s['src'])
              if m != None:
                s['src'] = (m.group(1) + "/image.php/" + m.group(2) + "/42/" + m.group(3))
                continue 
              m = favicon2pattern.match(s['src'])
              if m != None:
                s['src'] = (m.group(1) + "/pluginfile.php/" + m.group(2) + "/42/" + m.group(3)) 
                continue
        
 



          #only main page
          PageLinkContent = "<!DOCTYPE html> <html>" + str(moodlePageHeader) + "<body class='format-topics path-mod path-mod-assign safari dir-ltr lang-de yui-skin-sam yui3-skin-sam  pagelayout-incourse category-246 has-region-side-pre used-region-side-pre has-region-side-post empty-region-side-post side-pre-only jsenabled'>" + str(page_links_Soup) + "</body></html>"

          if "/course/view.php" in pagelink:
             course_section = page_links_Soup.select('.section.main.clearfix')


          page_links = page_links_Soup.find_all('a')
        

          pageFoundLinks = len(page_links)
          isaMoodlePage = True 

          


    #do some filters for moodle pages
    pageSaveDir = parentDir
    doSave = True
    doAddToHistory = False


#/url/ = redirekt unwichtig                     | doNotSave; DoNotRecrawl
#/resource/ = redirekt unwichtig!               | doNotSave; DoNotRecrawl

#/folder/ = folder strukt unwichtig ?           | doNotSave;
#/assign/ = Aufgaben Folder                     | doNotSave;

#/pluginfile.php/ = download file               | DoNotRecrawl;

#/course/view.php = startpage course            | saveInPagedir

#/page/ = info meistens WICHTIG                 | ???
#/wiki/ = wiki shit                             | saveInPagedir
#/quiz/ = hausaufgaben wichtig ?                | saveInPagedir      ??maybe do not save  


    if isaMoodlePage:
         #saveIt in pageDir
         if "/course/view.php" in pagelink or "/wiki/" in pagelink  or "/quiz/" in pagelink:
            pageSaveDir = pageDir

         #Add To History -> not recrawl
         if  "/pluginfile.php/" in pagelink  or "/url/" in pagelink or "/resource/" in pagelink:
            doAddToHistory = True

         #do not save
         if "/folder/" in pagelink  or "/url/" in pagelink  or "/resource/" in pagelink or "/assign/" in pagelink:
            doSave = False

         if not downloadcoursepages == "true" and "/course/view.php" in pagelink:
            doSave = False
    
         #remove in every moodle page the action modules
    
    if pageIsHtml == True:  
         PageSoupHash = BeautifulSoup(PageLinkContent, "lxml") 
         #remove common changing text 
         [s.decompose() for s in PageSoupHash.select(".overdue")] 
         submissiontr = PageSoupHash.select(".submissionsummarytable tr")
         if len(submissiontr) > 2:
            submissiontr[-3].decompose() 
         
         textofhtml = text_from_html(str(PageLinkContent));
         #print(textofhtml);
         
         m = md5.new()
         m.update(textofhtml)
         calcHash = m.hexdigest()
        
         if usehistory == "true" and  (pageDir + " calculated hash " + calcHash) in logFile:
            log("This page was saved in the past. I will not resave it, change the recrawl settings if you want to resave it.", 3)
            doSave = False
         else:
            addHashToLog(pageDir, calcHash)



    pageFilePath = "This file was not saved. It is listed here for crawl purposes."
    if doSave:
       pageFilePath = saveFile(pageFileName, pageSaveDir, PageLinkContent, responsePageLink, pagelink)

    if not course_section is None:
       for one_section in course_section:
          section_links = one_section.find_all('a')
          
          if not section_links is None:

             sectionname = one_section.attrs["aria-label"]
             if sectionname is None or sectionname == "":
                continue
                
             sectionname = decodeFilename(sectionname).strip("-")

             sectionDir = normPath(addSlashIfNeeded(parentDir) + pagename + "/" + sectionname)

             for link in section_links:
                hrefPageLink = link.get('href') 
                nextName = link.text
                if not page_links is None:
                   if link in page_links:
                      page_links.remove(link)
 
                #remove moodle shit (at the end of a link text)
                removeShit = link.select(".accesshide")
                if not removeShit is None and len(removeShit) == 1:
                  removeShitText = removeShit[0].text
                  if nextName.endswith(removeShitText):
                      nextName = nextName[:-len(removeShitText)]
 
 
                nextName = decodeFilename(nextName).strip("-")
 
 
                crawlMoodlePage(hrefPageLink, nextName, sectionDir, pagelink, (depth + 1), forbidrecrusionforNew)

   

    if not page_links is None:
      for link in page_links:
         hrefPageLink = link.get('href') 
         nextName = link.text

         #remove moodle shit (at the end of a link text)
         removeShit = link.select(".accesshide")
         if not removeShit is None and len(removeShit) == 1:
           removeShitText = removeShit[0].text
           if nextName.endswith(removeShitText):
               nextName = nextName[:-len(removeShitText)]


         nextName = decodeFilename(nextName).strip("-")

         nextParentDir = pageDir
         if "/url/" in pagelink:
            nextParentDir = normPath(addSlashIfNeeded(parentDir))
            nextName = pagename
         
         
         crawlMoodlePage(hrefPageLink, nextName, nextParentDir, pagelink, (depth + 1), forbidrecrusionforNew)

  
    # add Link to crawler history
    if isexternlink == True or pageIsHtml == False or doAddToHistory == True or isSpecialExternLink == True: 
       addFileToLog(pagelink, pageFilePath)







 

#Setup Login Credentials
moodlePath = ""
useSpecpath = False

if authentication_url.split('?')[0][-16:] == "/login/index.php":
   moodlePath = addSlashIfNeeded(authentication_url.split('?')[0][:-16])
else:
   useSpecpath = True
   log("This script will probably not work. Please use an authentication URL that ends with /login/index.php or contact the project owner.")



payload = {
    'username': username,
    'password': password
}
 

log("Moodle Crawler started working.")


if useauthstate == "true":

  log("Create Auth State Session.")

  req = urllib2.Request(authentication_url)

  try:
     responseLogin = urllib2.urlopen(req, timeout=10)
  except Exception as e:
     log("Connection lost! It is not possible to connect to login page!")
     log("Exception details: " + str(e), 5)
     exit(1)

  LoginContents = donwloadFile(responseLogin)
  
  LoginSoup = BeautifulSoup(LoginContents, "lxml") 

  formsLogin = LoginSoup.select("form")

  if(not len(formsLogin) == 1):
    log("This type of AuthState is not yet suportet! Please conntect the Developer and send him this Debug Informations:")
    log("Debug information - Select formulars: " + formsLogin)
    exit(1)

  selectForm = formsLogin[0]

  actionLink = selectForm.get("action") 

  inputsLogin = selectForm.select("input")

  if(not len(inputsLogin)== 3):
    log("This type of AuthState is not yet suportet! Please conntect the Developer and send him this Debug Informations:")
    log("Debug information - Inputs: " + inputsLogin)
    exit(1)


  if(not inputsLogin[0].get("name") == "AuthState"):
    log("This type of AuthState is not yet suportet! Please conntect the Developer and send him this Debug Informations:")
    log("Debug information - Inputs: " + inputsLogin)
    exit(1)

  authstateValue = inputsLogin[0].get("value")
  thirdName = inputsLogin[2].get("name")
  thirdValue = inputsLogin[2].get("value")


  log("AuthState action = " + actionLink, 5)
  log("AuthState = " + authstateValue, 5)
  log(thirdName + " = " + thirdValue, 5)




  calledFrom = responseLogin.geturl() #get mainURL from login response (this is not normal)
  pagelink = actionLink  

  if not pagelink.startswith("https://") and not pagelink.startswith("http://") and not pagelink.startswith("www."):
       if pagelink.startswith('/'): 
          parsed_uri = urlparse(calledFrom)
          domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri) 
          pagelink = domain + pagelink[1:] 
       elif pagelink.startswith('#'):
          log("This is an bad link. I will not login. It tries to kid me.", 3)
          exit(1)
       elif pagelink.startswith('mailto'):
          log("This is an bad link. I will not login. It tries to kid me.", 3)
          exit(1)
       else:
          pagelink = calledFrom[:len(calledFrom) - len(calledFrom.split('/')[-1])] + pagelink
          #pagelink = calledFrom[:(len(calledFrom) - len(calledFrom.split('/')[-1])) - 1] + pagelink

  actionLink = pagelink


  payloadAuthState = {
    'AuthState': authstateValue,
    thirdName : thirdValue
  }

  extaLoginToken =  urllib.urlencode(payloadAuthState) 
  select_url = addQuestionmarkIfNeeded(actionLink) + extaLoginToken
  log("Select url = " + select_url, 2)


  req = urllib2.Request(select_url)

  try:
     responseLogin = urllib2.urlopen(req, timeout=10)
  except Exception as e:
     log("Connection lost! It is not possible to connect to login page!")
     log("Exception details: " + str(e), 5)
     exit(1)

  LoginContents = donwloadFile(responseLogin)
  
  LoginSoup = BeautifulSoup(LoginContents, "lxml") 


  payload = {
    'username': username,
    'password': password,
    'AuthState': authstateValue 
  }

  authentication_url = responseLogin.geturl().split("?")[0]
  log("Authentication url = " + authentication_url, 5)
      




data = urllib.urlencode(payload)

crawlHistoryFile = normPath(addSlashIfNeeded(root_directory)+ ".crawlhistory.log")





# Connection established?
log("Try to login...", 2)

#Log the credentials
#log("+++++++++ Login Credentials - Remove these lines from the log file +++++++++, 3)
#log("These lines are only for check purposes, 3)
#log("Authentication url: '" + authentication_url + "'", 3)
#log("Username: '" + username + "'", 3)
#log("Password: '" + password + "'", 3)
#log("Root directory: '" + root_directory + "'", 3)
#log("+++++++++ End Login Credentials +++++++++, 3)




#login prozedur
req = urllib2.Request(authentication_url, data)

try:
   responseLogin = urllib2.urlopen(req, timeout=10)
except Exception as e:
   log("Connection lost! It is not possible to connect to login page!")
   log("Exception details: " + str(e), 5)
   exit(1)
   
LoginContents = donwloadFile(responseLogin)
 
if "errorcode=" in responseLogin.geturl():
    log("Cannot login. Check your login data.")
    log("Full url: " + responseLogin.geturl(), 5)
    exit(1)

#Lookup in the Moodle source if it is standard   ("Logout" on every Page)
LoginSoup = BeautifulSoup(LoginContents, "lxml") 

if not simpleLoginCheck(LoginContents):
  log("Cannot connect to moodle or Moodle has changed. Crawler is not logged in. Check your login data.") 
  # log("Full page: " + str(LoginStatusConntent[-1]), 5)
  exit(1)
 
 
 

log("Logged in!", 1)
 
 

#Get moodle base url

mainpageURL = addSlashIfNeeded(base_url)

#Lookup in the Moodle source if it is standard (Domain + subfolder)
#mainpageURL = responseLogin.geturl()  #get mainURL from login response (this is not normal)

#parsed_uri = urlparse(mainpageURL)
#domainMoodle = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri) 
domainMoodle = mainpageURL

#
#if useSpecpath == False:  #get mainURL from Login page link (this is normal)
#   mainpageURL = moodlePath







#create rootdir ++++++++++++++ warning danger +++++++++++
if not os.path.isdir(root_directory):
   os.makedirs(root_directory)    


 #create crealHistoryfile
if not os.path.isfile(crawlHistoryFile):
   logFileWriter = open(crawlHistoryFile, 'ab')
   logFileWriter.write("LogFile:V1.0")
   logFileWriter.close()
   
logFileReader = open(crawlHistoryFile, 'rb')
logFile = logFileReader.read()
logFileReader.close()


#Update log file 
logfileOld = False
logFileLines = logFile.split("\n")

for line in logFileLines:
  if not "LogFile:V1.0" in line:
    logfileOld = True
  break

if logfileOld:
  log("Fixing Log File", 2)
  os.remove(crawlHistoryFile)
  logFileWriter = open(crawlHistoryFile, 'ab')
  logFileWriter.write("LogFile:V1.0\n")
  for line in logFileLines:
     if "Crawler" in line and "log" in line and "file" in line and "for" in line:
        continue
     logFileWriter.write(line + "\n")
          
  logFileWriter.close()
     
  logFileReader = open(crawlHistoryFile, 'rb')
  logFile = logFileReader.read()
  logFileReader.close()

#find own courses (returns an array)
courses = findOwnCourses(mainpageURL)
 

   

#couse loop
current_dir = normPath(addSlashIfNeeded(root_directory))

for course in courses:

    log("Check course: '" + course[0] + "'")
    crawlMoodlePage(course[1], course[0], current_dir, mainpageURL + "my/")
    if findduplicates == "true":
       searchfordumps(normPath(current_dir + "/" + course[0] + "/"))


if findallduplicates == "true":
   searchfordumps(current_dir)


 
log("Update Complete")
