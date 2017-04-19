#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#  Copyright 2017 Daniel Vogt
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


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


def normPath(pathSring):
   return os.path.normpath(pathSring)

def removeSpaces(pathString):
   return pathString.replace(" ", "")



conf = ConfigParser()
project_dir = os.path.dirname(os.path.abspath(__file__))
conf.read(os.path.join(project_dir, 'config.ini'))
  

root_directory = normPath(checkQuotationMarks(conf.get("dirs", "root_dir")))
username = checkQuotationMarks(conf.get("auth", "username"))
password = checkQuotationMarks(conf.get("auth", "password"))
crawlforum = checkQuotationMarks(conf.get("crawl", "forum")) #/forum/
usehistory = checkQuotationMarks(conf.get("crawl", "history")) #do not recrawl
loglevel = checkQuotationMarks(conf.get("crawl", "loglevel"))
downloadExternals = checkQuotationMarks(conf.get("crawl", "externallinks"))


authentication_url = checkQuotationMarks(conf.get("auth", "url"))
useColors = checkQuotationMarks(conf.get("other", "colors"))



try:
   from bs4 import BeautifulSoup
except Exception as e:
   print("Module BeautifulSoup4 is missing!")
   exit(1)

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


#utf8 shit
reload(sys)
sys.setdefaultencoding('utf-8')

filesBySize = {}

def walker(arg, dirname, fnames):
    d = os.getcwd()
    os.chdir(dirname)
    try:
        fnames.remove('Thumbs')
    except ValueError:
        pass
    for f in fnames:
        if not os.path.isfile(f):
            continue
        size = os.stat(f)[stat.ST_SIZE]
        if size < 100:
            continue
        if filesBySize.has_key(size):
            a = filesBySize[size]
        else:
            a = []
            filesBySize[size] = a
        a.append(os.path.join(dirname, f))
    os.chdir(d)

#Log levels:
# - Level 0: Minimal Information + small Errors
# - Level 1: More Information + Successes 
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




def donwloadFile(downloadFileResponse):
   log("Download has started.", 4)
       
   downloadFileContent = ""
   
   if downloadFileResponse is None:
      log("Faild to download file", 4)
      return ""

   try:
       total_size = downloadFileResponse.info().getheader('Content-Length').strip()
       header = True
   except Exception as e:
       log("No Content-Length available.", 5)
       header = False # a response doesn't always include the "Content-Length" header
          
   if header:
       total_size = int(total_size)
         
   bytes_so_far = 0
        
   while True:
       downloadFileContentBuffer = downloadFileResponse.read(81924)
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

   if os.path.isfile(file_name): 
      fileend = file_name.split('.')[-1]
      filebegin = file_name[:(len(file_name) - len(fileend)) - 1]
         
      ii = 1
      while True:
       new_name = filebegin + "_" + str(ii) + "." + fileend
       if not os.path.isfile(new_name):
          file_name = new_name
          break
       ii += 1
     
   try:
      log("Creating new file: '" +  file_name + "'")
   except Exception as e:
      log("Exception: " + str(e) + "    Lol   " +  pathToSave)
      exit(1)


   pdfFile = io.open(file_name, 'wb')
   pdfFile.write(webFileContent)
   webFileResponse.close()
   pdfFile.close()
   logFileWriter = io.open(crawlHistoryFile, 'ab')
   logFileWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " "+ webFileHref + " saved to '" + file_name + "'\n")
   logFileWriter.close()
   global logFile
   logFileReader = io.open(crawlHistoryFile, 'rb')
   logFile = logFileReader.read()
   logFileReader.close()


#status:
# 0 - Not logged in
# 1 - Logged in
# 2 - Had to re login
# 3 - Something went wrong

def checkLoginStatus(pageContent):
   PageSoup = BeautifulSoup(pageContent, "lxml") 
   #LoginStatusConntent = PageSoup.find(class_="logininfo")
   LoginStatusConntent = PageSoup.select(".logininfo")

   if not LoginStatusConntent is None or len(LoginStatusConntent) == 0:
   
      log("Checking login status.", 4)  
      #Lookup in the Moodle source if it is standard (login / log in on every page)
      #Is a relogin needed ? Try to figure out when relogin is needed.
      if "Logout" not in str(LoginStatusConntent[-1]) and "logout" not in str(LoginStatusConntent[-1]):
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
         #LoginStatusConntent = LoginSoup.find(class_="logininfo")
         LoginStatusConntent = PageSoup.select(".logininfo")
        
         if LoginStatusConntent is None or ("Logout" not in str(LoginStatusConntent[-1]) and "logout" not in str(LoginStatusConntent[-1])):  
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




#warning this function exit the stript if it could not load the course list page
#try to crawl all courses from moodlepage/my/
def findOwnCourses():
   log("Searching Courses...", 2)
   
   #Lookup in the Moodle source if it is standard (moodlePath/my/ are my courses)
   try:
      responseCourses = urllib2.urlopen(mainpageURL + "my/", timeout=10)
   except Exception as e:
      log("Connection lost! It is not possible to connect to course page! At: " + mainpageURL)
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
       courses.append([course_name, course_link])
       log("Found Course: '" + course_name + "'", 2)

   return courses


def searchfordumps(pathtoSearch):
#find dublication in folder  pathtoSearch
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
        if len(inFiles) is 1: continue
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
            log('Deleting %s' % f, 4)
            os.remove(f) 



#Login prozedur


cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
opener.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36')]
urllib2.install_opener(opener)



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


crawlHistoryFile = normPath(addSlashIfNeeded(root_directory)+ ".crawlhistory.log")

data = urllib.urlencode(payload)


log("Moodle Crawler started working.")

# Connection established?
log("Try to login...", 2)
log("Authentication url: '" + authentication_url + "'", 3)
log("Username: '" + username + "'", 3)
log("Password: '" + password + "'", 3)
log("Root directory: '" + root_directory + "'", 3)



req = urllib2.Request(authentication_url, data)
#response = urllib2.urlopen(req)
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
#LoginStatusConntent = LoginSoup.find(class_="logininfo")
LoginStatusConntent = LoginSoup.select(".logininfo")
if LoginStatusConntent is None or len(LoginStatusConntent) == 0 or ("Logout" not in str(LoginStatusConntent[-1]) and "logout" not in str(LoginStatusConntent[-1])): 
   log("Cannot connect to moodle or Moodle has changed. Crawler is not logged in. Check your login data.") 
   log("Full page: " + str(LoginStatusConntent[-1]), 5)
   exit(1)


log("Logged in!", 1)
 
 

#Lookup in the Moodle source if it is standard (Domain + subfolder)
mainpageURL = addSlashIfNeeded(responseLogin.geturl())

domainMoodle = "" 
if mainpageURL.startswith("https://"):
   domainMoodle = mainpageURL[8:]

if mainpageURL.startswith("http://"):
   domainMoodle = mainpageURL[7:]

domainMoodle = domainMoodle.split("/")[0]
 
if useSpecpath == False:
   mainpageURL = moodlePath


 #create necessary stuff
if not os.path.isfile(crawlHistoryFile):
   logFileWriter = open(crawlHistoryFile, 'ab')
   logFileWriter.close()
   
logFileReader = open(crawlHistoryFile, 'rb')
logFile = logFileReader.read()
logFileReader.close()




courses = findOwnCourses()
 

if len(courses) == 0:
   log("Unable to find courses")
   log("Full page: " + str(CoursesContentsList), 5)
   

#couse loop

for course in courses:
    #response1 = urllib2.urlopen(course[1], timeout=10)
   

    log("Check course: '" + course[0] + "'")

    try:
       responseCourseLink = urllib2.urlopen(course[1], timeout=10)
    except Exception as e:
       log("Connection lost! Course does not exist!", 2)
       log("Exception details: " + str(e), 5)
       continue

    CourseLinkContent = donwloadFile(responseCourseLink)

         

    if "text/html" in responseCourseLink.info().getheader('Content-Type'): 
       try:
          loginStatus = checkLoginStatus(CourseLinkContent) 
       except Exception as e:
          log("Connection lost! It is not possible to connect to moodle!", 3)
          log("Exception details: " + str(e), 5)
          continue

       if loginStatus == 0:
          continue
       elif loginStatus == 2:
          log("Recheck Course: '" + course[0] + "'", 4)
          try:
             responseCourseLink = urllib2.urlopen(course[1], timeout=10)
          except Exception as e:
             log("Connection lost! Course does not exist!", 3)
             log("Exception details: " + str(e), 5)
             continue
     
          CourseLinkContent = donwloadFile(responseCourseLink)
          
       #elif loginStatus == 3:
          #this should not heppend
          #mh maybe continue ?  

       CourseSoup = BeautifulSoup(CourseLinkContent, "lxml") 

 

    if not course[1] in logFile:
       logFileWriter = open(crawlHistoryFile, 'ab')
       logFileWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " Crawler log file for: "+ course[1] + "\n")
       logFileWriter.close()
       logFileReader = open(crawlHistoryFile, 'rb')
       logFile = logFileReader.read()
       logFileReader.close()

 
    course_links_Soup = CourseSoup.find(id="region-main")


 
    if course_links_Soup is None:
       log("Unable detect a Course")  #Maybe save the page standalone
       log("Full page: " +  str(CourseSoup), 5)
       continue
   
 
    course_links = course_links_Soup.find_all('a')


    current_dir = normPath(addSlashIfNeeded(root_directory) + course[0] )
    for link in course_links:
        hrefCourseFile = link.get('href')

        if hrefCourseFile is None or hrefCourseFile == "":
             log("There went something wrong, this is an empty link.", 3)
             continue
 

        # Checking only resources... Ignoring forum and folders, etc
        #if "/pluginfile.php/" in hrefCourseFile or "/resource/" in hrefCourseFile  or "/mod/page/" in hrefCourseFile or "/folder/" in hrefCourseFile:
        
        if not hrefCourseFile.startswith("https://") and not hrefCourseFile.startswith("http://") and not hrefCourseFile.startswith("www."):
           if hrefCourseFile.startswith('/'):
              hrefCourseFile = course[1][:(len(course[1]) - len(course[1].split('/')[-1])) - 1] + hrefCourseFile
           else:
              hrefCourseFile = course[1][:len(course[1]) - len(course[1].split('/')[-1])] + hrefCourseFile
        

        
        log("Found Link: " + hrefCourseFile, 2)
        if usehistory == "true" and hrefCourseFile in logFile:
           log("This link was crawled in the past. I will not recrawl it, change the settings if you want to recrawl it.", 3)
           continue

        #log("found: " + hrefCourseFile + " in " + course[0])
        #cj1 = cookielib.CookieJar()
        #opener1 = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj1))
        #opener1.addheaders = [('User-agent', 'HeyThanksForWatchingThisAgenet')]
        #urllib2.install_opener(opener1)
        #req1 = urllib2.Request(authentication_url, data)
        #resp = urllib2.urlopen(req1, timeout=10)
 

        isexternlink = False

        if not domainMoodle in hrefCourseFile:
           log("This is an external link.", 2)
           #log("I will try to find more links on the external page! This will fail maybe.", 4) 
           
           if not os.path.isdir(current_dir):
              os.makedirs(current_dir)   
           
           externalLinkPath = normPath(addSlashIfNeeded(current_dir) + "external-links.log")
          

           if os.path.isfile(externalLinkPath):
              externalLinkReadeer = io.open(externalLinkPath, 'rb')
              externallinks = externalLinkReadeer.read()
              externalLinkReadeer.close()
              if not hrefCourseFile in externallinks:
                 log("I will store it in the '" + externalLinkPath + "' file.", 4)
                 externalLinkWriter = io.open(externalLinkPath, 'ab')
                 externalLinkWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " "+ hrefCourseFile + "\n")
                 externalLinkWriter.close()
                 

              else:
                 log("This link was stored in the '" + externalLinkPath + "' file earlier.", 5)


           else:
              log("I will store it in the '" + externalLinkPath + "' file.", 4)
              externalLinkWriter = io.open(externalLinkPath, 'ab')
              externalLinkWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " "+ hrefCourseFile + "\n")
              externalLinkWriter.close()
 
           logFileWriter = io.open(crawlHistoryFile, 'ab')
           logFileWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " External: "+ hrefCourseFile + " saved to '" + externalLinkPath + "'\n")
           logFileWriter.close()
           logFileReader = io.open(crawlHistoryFile, 'rb')
           logFile = logFileReader.read()
           logFileReader.close()

           isexternlink = True
           if downloadExternals == "false":
              log("Ups this is an external link. I do not crawl external links. Change the settings if you want to crawl external links.", 3)
              continue


        if crawlforum == "false" and "/forum/" in hrefCourseFile:
           log("Ups this is a forum. I do not crawl this forum. Change the settings if you want to crawl forums.", 3)
           continue

        #webFileCourseFile = urllib2.urlopen(hrefCourseFile, timeout=10)
        try:
           webFileCourseFile = urllib2.urlopen(hrefCourseFile, timeout=10)
        except Exception as e:
           log("Connection lost! Link does not exist!", 3)
           log("Exception details: " + str(e), 5)
           continue
        
        webFileContent = donwloadFile(webFileCourseFile)

        
        if "text/html" in webFileCourseFile.info().getheader('Content-Type'):
           if not isexternlink:
              try:
                 loginStatus = checkLoginStatus(webFileContent)
                 
              except Exception as e:
                 log("Connection lost! It is not possible to connect to moodle!", 3)
                 log("Exception details: " + str(e), 5)
                 continue

              if loginStatus == 0:
                  continue
              elif loginStatus == 2:
                 try:
                    webFileCourseFile = urllib2.urlopen(hrefCourseFile, timeout=10)
                 except Exception as e:
                    log("Connection lost! Link does not exist!", 3)
                    log("Exception details: " + str(e), 5)
                    continue
                 
                     
                 webFileContent = donwloadFile(webFileCourseFile)  
  
               #elif loginStatus == 3:
                  #this should not heppend
                  #mh maybe continue ?  
        
           webFileSoup = BeautifulSoup(webFileContent, "lxml") 
    

        #webfileurlCourseFile = webFileCourseFile.geturl().split('/')[-1].split('?')[0].encode('ascii', 'ignore').replace('/', '|').replace('\\', '|').replace(' ', '_')

        webfileurlCourseFile = decodeFilename(webFileCourseFile.geturl().split('/')[-1].split('?')[0]).strip("-")

        trapscount = 0
         
        
        if "text/html" in webFileCourseFile.info().getheader('Content-Type') or webfileurlCourseFile[-4:] == ".php" or webfileurlCourseFile[-4:] == ".html":
          log("It is a  folder! Try to find more links!", 2)
          
          trap_links_region = webFileSoup.find(id="region-main")

          if not trap_links_region is None:
    
             trap_links = trap_links_region.find_all('a')
                  
             myTitle = webFileSoup.title.string
             
             #myTitle = myTitle.encode('ascii', 'ignore').replace('/', '|').replace('\\', '|').replace(' ', '_').replace('.', '_')
   

             myTitle = decodeFilename(myTitle).replace(course[0], '').strip("-")

             sub_dir = normPath( addSlashIfNeeded(root_directory) + course[0] + "/" + myTitle )
   
             for traplink in trap_links:
               hrefT = traplink.get('href')
                  
               if hrefT is None or hrefT == "":
                    log("There went something wrong, this is an empty link.", 3)
                    continue
   
               # Checking only resources... Ignoring forum and folders, etc
               #if "/pluginfile.php/" in hrefT or "/resource/" in hrefT:
               if not hrefT.startswith("https://") and not hrefT.startswith("http://") and not hrefT.startswith("www."):
                  if hrefT.startswith('/'):
                     hrefT = hrefCourseFile[:(len(hrefCourseFile) - len(hrefCourseFile.split('/')[-1])) - 1] + hrefT
                  else:
                     hrefT = hrefCourseFile[:len(hrefCourseFile) - len(hrefCourseFile.split('/')[-1])] + hrefT
               
                  
   
               trapscount = trapscount + 1
               log("Found link in folder: " + hrefT, 2)
               if usehistory == "true" and hrefT in logFile:
                 log("This link was crawled in the past. I will not recrawl it, change the settings if you want to recrawl it.", 3)
                 continue
   
               isexternLinkT = False
   
               if not domainMoodle in hrefT: 
                  log("This is an external link.", 4)


                  if not os.path.isdir(sub_dir):
                     os.makedirs(sub_dir)    

                  externalLinkPath = normPath(addSlashIfNeeded(sub_dir) + "external-links.log")

                  if os.path.isfile(externalLinkPath):
                     externalLinkReadeer = io.open(externalLinkPath, 'rb')
                     externallinks = externalLinkReadeer.read()
                     externalLinkReadeer.close()
                     if not hrefT in externallinks: 
                        log("I will store it in the '" + externalLinkPath + "' file", 4)
                        externalLinkWriter = io.open(externalLinkPath, 'ab')
                        externalLinkWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " "+ hrefT + "\n")
                        externalLinkWriter.close()
                     else:
                        log("This link was stored in the '" + externalLinkPath + "' file earlier.", 5)
       
                  else: 
                     log("I will store it in the '" + externalLinkPath + "' file", 4)
                     externalLinkWriter = io.open(externalLinkPath, 'ab')
                     externalLinkWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " "+ hrefT + "\n")
                     externalLinkWriter.close()

                  logFileWriter = io.open(crawlHistoryFile, 'ab')
                  logFileWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " External: "+ hrefCourseFile + " saved to '" + externalLinkPath + "'\n")
                  logFileWriter.close()
                  logFileReader = io.open(crawlHistoryFile, 'rb')
                  logFile = logFileReader.read()
                  logFileReader.close()

                  isexternLinkT = True
                  if downloadExternals == "false":
                     log("Ups this is an external link. I do not crawl external links. Change the settings if you want to crawl external links.", 3)
                     continue
   
               try:
                  webFileTrap = urllib2.urlopen(hrefT, timeout=10)
               except Exception as e:
                  log("Connection lost! File does not exist!", 3)
                  log("Exception details: " + str(e), 5)
                  continue
    
              # webFileTrapContent = donwloadFile(webFileTrap)
   
               
               webFileTrapContent = donwloadFile(webFileTrap)   
   
               if not isexternLinkT and "text/html" in webFileTrap.info().getheader('Content-Type'):
                  try:
                     loginStatus = checkLoginStatus(webFileTrapContent)
                     
                  except Exception as e:
                     log("Connection lost! It is not possible to connect to moodle!", 3)
                     log("Exception details: " + str(e), 5)
                     continue

                  if loginStatus == 0:
                      continue
                  elif loginStatus == 2:
                     try:
                       webFileTrap = urllib2.urlopen(hrefT, timeout=10)
                     except Exception as e:
                       log("Connection lost! Link does not exist!", 3)
                       log("Exception details: " + str(e), 5)
                       continue
                       
                     webFileTrapContent = donwloadFile(webFileTrap)  
      
                   #elif loginStatus == 3:
                      #this should not heppend
                      #mh maybe continue ?  
            
               webfileTrapurl = decodeFilename(webFileTrap.geturl().split('/')[-1].split('?')[0]).strip("-")
               # webfileTrapurl = webFileTrap.geturl().split('/')[-1].split('?')[0].encode('ascii', 'ignore').replace('/', '|').replace('\\', '|').replace(' ', '_')
    
               saveFile(webfileTrapurl, sub_dir, webFileTrapContent, webFileTrap, hrefT)

          else:
             log("This page seems not to be a folder.", 4)             
                      
                   
                       
        if trapscount == 0:
           if webfileurlCourseFile[-4:] == ".php" or webfileurlCourseFile[-4:] == ".html":
              log("Ups no link was found in this folder!", 3)
 
           log("Try to save the page: " + hrefCourseFile, 4)
           
           saveFile(webfileurlCourseFile, current_dir, webFileContent, webFileCourseFile, hrefCourseFile) 

    #find dublication in folder  current_dir
    searchfordumps(current_dir)


log("Update Complete")
