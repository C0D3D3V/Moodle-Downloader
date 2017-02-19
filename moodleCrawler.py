#!/usr/bin/env python2

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
import os
import os.path
import hashlib
import sys
import stat
import md5
import re
import filecmp


from datetime import datetime
from ConfigParser import ConfigParser

from bs4 import BeautifulSoup

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

def checkQuotationMarks(settingString):
   if not settingString is None and settingString[0] == "\"" and settingString[-1] == "\"":
      settingString = settingString[1:-1]
   return settingString
 

def addSlashIfNeeded(settingString):
   if not settingString is None and not settingString[-1] == "/":
      settingString = settingString + "/"
   return settingString


#Loglevel:
# - Level 0: Minimal Information + small Errors
# - Level 1: More Information + Successes 
# - Level 2: Doing Statemants + Found information
# - Level 3: More Errors + More Infos
# - Level 4: More Doing Statements + Dowload Info + Scann Dublicates
# - Level 5: More Download Info + More Info about dublicates

 
def log(logString, level=0):
   if level <= int(loglevel):
      print(datetime.now().strftime('%H:%M:%S') + " " + logString)


conf = ConfigParser()
project_dir = os.path.dirname(os.path.abspath(__file__))
conf.read(os.path.join(project_dir, 'config.ini'))
 


root_directory = checkQuotationMarks(conf.get("dirs", "root_dir"))
username = checkQuotationMarks(conf.get("auth", "username"))
password = checkQuotationMarks(conf.get("auth", "password"))
crawlforum = checkQuotationMarks(conf.get("crawl", "forum")) #/forum/
usehistory = checkQuotationMarks(conf.get("crawl", "history")) #do not recrawl
loglevel = checkQuotationMarks(conf.get("crawl", "loglevel"))

authentication_url = addSlashIfNeeded(checkQuotationMarks(conf.get("auth", "url")))

  

cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
opener.addheaders = [('User-agent', 'HeyThanksForWatchingThisAgenet')]
urllib2.install_opener(opener)


payload = {
    'username': username,
    'password': password
}


data = urllib.urlencode(payload)


log("Moodle Crawler started working.")

# Connection established?
log("Try to login...", 2)

req = urllib2.Request(authentication_url, data)
#response = urllib2.urlopen(req)
try:
   responseLogin = urllib2.urlopen(req, timeout=10)
except Exception:
   log("Connection lost! It is not possible to connect to moodle!")
   exit(1)
LoginContents = responseLogin.read()
 
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
mainpageURL = responseLogin.geturl()

domainMoodle = ""
if not mainpageURL[-1] == "/":
   mainpageURL = mainpageURL + "/" 

if mainpageURL.startswith("https://"):
   domainMoodle = mainpageURL[8:]

if mainpageURL.startswith("http://"):
   domainMoodle = mainpageURL[7:]

domainMoodle = domainMoodle.split("/")[0]
 


log("Searching Courses...", 2)

#Lookup in the Moodle source if it is standard (moodlePath/my/ are my courses)
try:
   responseCourses = urllib2.urlopen(mainpageURL + "my/", timeout=10)
except Exception:
   log("Connection lost! It is not possible to connect to moodle!")
   exit(1)
CoursesContents = responseCourses.read()




CoursesContentsSoup = BeautifulSoup(CoursesContents, "lxml")

CoursesContentsList = CoursesContentsSoup.find(id="region-main")

#CoursesContentsList = CoursesContents.split('class="block_course_list  block list_block"')[1].split('class="footer"')[0]
#>Meine Kurse</h2>
 
if CoursesContentsList is None:
   log("Unable to find courses")
   exit(1)
   
 
regexCourseName = re.compile('class="course_title">(.*?)</div>')
course_list = regexCourseName.findall(str(CoursesContentsList))
courses = []

#blockCourse = True

for course_string in course_list:
    CourseTitleSoup = BeautifulSoup(course_string, "lxml")
    aCourse = CourseTitleSoup.find('a')
    course_name = aCourse.text.encode('ascii', 'ignore').replace('/', '|').replace('\\', '|').replace(' ', '_').replace('.', '_')
    course_link = aCourse.get('href')
    #if course_name == "TINF15B5: Programmieren \ Java":
    #   blockCourse = False

    #if blockCourse == False:
    courses.append([course_name, course_link])
    log("Found Course: '" + course_name + "'", 2)




for course in courses:
    if not os.path.isdir(root_directory + course[0]):
        os.mkdir(root_directory+course[0])
    #response1 = urllib2.urlopen(course[1], timeout=10)
    logFileWriter = open(root_directory + course[0] + "/crawlhistory.log", 'ab')
    logFileWriter.close()
    logFileReader = open(root_directory + course[0] + "/crawlhistory.log", 'rb')
    logFile = logFileReader.read()
    logFileReader.close()
    if not course[1] in logFile:
       logFileWriter = open(root_directory + course[0] + "/crawlhistory.log", 'ab')
       logFileWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " Crawler log file for: "+ course[1] + "\n")
       logFileWriter.close()
       logFileReader = open(root_directory + course[0] + "/crawlhistory.log", 'rb')
       logFile = logFileReader.read()
       logFileReader.close()



    log("Check Course: '" + course[0] + "'")

    try:
       responseCourseLink = urllib2.urlopen(course[1], timeout=10)
    except Exception:
       log("Connection lost! Course does not exist!", 2)
       continue

    CourseLinkContent = responseCourseLink.read()

 
         

    if "text/html" in responseCourseLink.info().getheader('Content-Type'):

       CourseSoup = BeautifulSoup(CourseLinkContent, "lxml") 
       LoginStatusConntent = CourseSoup.find(class_="logininfo")
       if not LoginStatusConntent is None:
       
          log("Checking login status.", 4)  
          #Lookup in the Moodle source if it is standard (login / log in on every page)
          #Is a relogin needed ? Try to figure out when relogin is needed.
          if "Logout" not in str(LoginStatusConntent) and "logout" not in str(LoginStatusConntent):
             log("Try to relogin, connection maybe lost.", 3)
             
             try:
                responseLogin = urllib2.urlopen(req, timeout=10)
             except Exception:
                log("Connection lost! It is not possible to connect to moodle!", 3)
                continue
              
             LoginContents = responseLogin.read()
              
              
             if "errorcode=" in responseLogin.geturl():
                 log("Cannot login. Check your login data.", 3)
                 continue
             
             #Lookup in the Moodle source if it is standard   ("Logout" on every Page)
             LoginSoup = BeautifulSoup(LoginContents, "lxml") 
             LoginStatusConntent = LoginSoup.find(class_="logininfo")
             if LoginStatusConntent is None or ("Logout" not in str(LoginStatusConntent) and "logout" not in str(LoginStatusConntent)):  
                 log(" Cannot connect to moodle or Moodle has changed. Crawler is not logged in. Check your login data.", 3)
                 continue
               
             #reload page  
             log("Recheck Course: '" + course[0] + "'", 4)
             try:
                responseCourseLink = urllib2.urlopen(course[1], timeout=10)
             except Exception:
                log("Connection lost! Course does not exist!", 3)
                continue
       
             CourseLinkContent = responseCourseLink.read()
          else:
             log("Crawler is still loged in.", 4)           

 

    course_links = CourseSoup.find(id="region-main").find_all('a')


    current_dir = root_directory + course[0] + "/"
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
           log("This is an external link. I will store it in the 'externel-links.log' file", 2)
           #log("I will try to find more links on the external page! This will fail maybe.", 4)
           externalLinkWriter = open(current_dir + "externel-links.log", 'ab')
           externalLinkWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " "+ hrefCourseFile + "\n")
           externalLinkWriter.close()
           isexternlink = True


        if crawlforum == "false" and "/forum/" in hrefCourseFile:
           log("Ups this is a forum. I do not crawl this forum. Change the settings if you want to crawl forums.", 3)
           continue

        #webFileCourseFile = urllib2.urlopen(hrefCourseFile, timeout=10)
        try:
           webFileCourseFile = urllib2.urlopen(hrefCourseFile, timeout=10)
        except Exception:
           log("Connection lost! Link does not exist!", 3)
           continue
        

        log("Download has started.", 4)

        webFileContent = ""

        try:
            total_size = webFileCourseFile.info().getheader('Content-Length').strip()
            header = True
        except Exception:
            log("No Content-Length available.", 5)
            header = False # a response doesn't always include the "Content-Length" header

        if header:
            total_size = int(total_size)
 
        bytes_so_far = 0
 
        while True:
            webFileContentBuffer = webFileCourseFile.read(8192)
            if not webFileContentBuffer: 
                break
        
            bytes_so_far += len(webFileContentBuffer) 
            webFileContent = webFileContent + webFileContentBuffer

            if not header: 
               log("Downloaded %d bytes" % (bytes_so_far), 5)
 
            else:
               percent = float(bytes_so_far) / total_size
               percent = round(percent*100, 2)
               log("Downloaded %d of %d bytes (%0.2f%%)\r" % (bytes_so_far, total_size, percent), 5)
 

        log("Download complete.", 4)  



        
        if "text/html" in webFileCourseFile.info().getheader('Content-Type'):
 
           webFileSoup = BeautifulSoup(webFileContent, "lxml") 
   
           if not isexternlink:
              LoginStatusConntent = webFileSoup.find(class_="logininfo") 
   
              if not LoginStatusConntent is None:
                 log("Checking login status.", 4)  
              
                 #Lookup in the Moodle source if it is standard (login / log in on every page)
                 #Is a relogin needed ? Try to figure out when relogin is needed.
                 if "Logout" not in str(LoginStatusConntent) and "logout" not in str(LoginStatusConntent):
                    log("Try to relogin, connection maybe lost.", 3)
                    
                    try:
                       responseLogin = urllib2.urlopen(req, timeout=10)
                    except Exception:
                       log("Connection lost! It is not possible to connect to moodle!", 3)
                       continue
                     
                    LoginContents = responseLogin.read()
                     
                     
                    if "errorcode=" in responseLogin.geturl():
                        log(" Cannot login. Check your login data.", 3)
                        continue
                    
                    #Lookup in the Moodle source if it is standard   ("Logout" on every Page)
                    LoginSoup = BeautifulSoup(LoginContents, "lxml") 
                    LoginStatusConntent = LoginSoup.find(class_="logininfo")
                    if LoginStatusConntent is None or ("Logout" not in str(LoginStatusConntent) and "logout" not in str(LoginStatusConntent)):  
                        log(" Cannot connect to moodle or Moodle has changed. Crawler is not logged in. Check your login data.", 3)
                        continue
                      
                    #reload page
                    try:
                       webFileCourseFile = urllib2.urlopen(hrefCourseFile, timeout=10)
                    except Exception:
                       log("Connection lost! Link does not exist!", 3)
                       continue
                    
                      
                    log("Download has restarted.", 4)
                    #webFileContent = webFileCourseFile.read()
                    webFileContent = ""
   
                    try:
                        total_size = webFileCourseFile.info().getheader('Content-Length').strip()
                        header = True
                    except Exception:
                        log("No Content-Length available.", 5)
                        header = False # a response doesn't always include the "Content-Length" header
            
                    if header:
                        total_size = int(total_size)
             
                    bytes_so_far = 0
             
                    while True:
                        webFileContentBuffer = webFileCourseFile.read(8192)
                        if not webFileContentBuffer: 
                            break
                    
                        bytes_so_far += len(webFileContentBuffer) 
                        webFileContent = webFileContent + webFileContentBuffer
            
                        if not header: 
                           log("Downloaded %d bytes" % (bytes_so_far), 5)
             
                        else:
                           percent = float(bytes_so_far) / total_size
                           percent = round(percent*100, 2)
                           log("Downloaded %d of %d bytes (%0.2f%%)\r" % (bytes_so_far, total_size, percent), 5)
    
   
                    log("Download complete.", 4)  
                 else:
                    log("Crawler is still loged in.", 4)  





        webfileurlCourseFile = webFileCourseFile.geturl().split('/')[-1].split('?')[0].encode('ascii', 'ignore').replace('/', '|').replace('\\', '|').replace(' ', '_')

        trapscount = 0
         
        
        if "text/html" in webFileCourseFile.info().getheader('Content-Type') or webfileurlCourseFile[-4:] == ".php" or webfileurlCourseFile[-4:] == ".html":
          log("It is a  folder! Try to find more links!", 2)
          
          trap_links_region = webFileSoup.find(id="region-main")

          if not trap_links_region is None:
    
             trap_links = trap_links_region.find_all('a')
                  
             myTitle = webFileSoup.title.string
             
             myTitle = myTitle.encode('ascii', 'ignore').replace('/', '|').replace('\\', '|').replace(' ', '_').replace('.', '_').replace(course[0] + ":_", '')
   
             sub_dir = root_directory + course[0] + "/" + myTitle + "/"
             if not os.path.isdir(root_directory + course[0] + "/" + myTitle):
                os.mkdir(root_directory + course[0] + "/" + myTitle)
   
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
                  log("This is an external link. I will store it in the 'externel-links.log' file", 4)
                  externalLinkWriter = open(sub_dir + "externel-links.log", 'ab')
                  externalLinkWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " "+ hrefT + "\n")
                  externalLinkWriter.close()
                  isexternLinkT = True
   
               try:
                  webFileTrap = urllib2.urlopen(hrefT, timeout=10)
               except Exception:
                  log("Connection lost! File does not exist!", 3)
                  continue
   
               log("Download has started.", 4)
              # webFileTrapContent = webFileTrap.read()
   
   
               webFileTrapContent = ""
   
               try:
                   total_size = webFileTrap.info().getheader('Content-Length').strip()
                   header = True
               except Exception:
                   log("No Content-Length available.", 5)
                   header = False # a response doesn't always include the "Content-Length" header
       
               if header:
                   total_size = int(total_size)
        
               bytes_so_far = 0
        
               while True:
                   webFileTrapBuffer = webFileTrap.read(8192)
                   if not webFileTrapBuffer: 
                       break
               
                   bytes_so_far += len(webFileTrapBuffer) 
                   webFileTrapContent = webFileTrapContent + webFileTrapBuffer
       
                   if not header: 
                      log("Downloaded %d bytes" % (bytes_so_far), 5)
        
                   else:
                      percent = float(bytes_so_far) / total_size
                      percent = round(percent*100, 2)
                      log("Downloaded %d of %d bytes (%0.2f%%)\r" % (bytes_so_far, total_size, percent), 5)
    
   
               log("Download complete.", 4)  
   
      
   
               if not isexternLinkT and "text/html" in webFileTrap.info().getheader('Content-Type'):
                  TrapSoup = BeautifulSoup(webFileTrapContent, "lxml") 
                  LoginStatusConntent = TrapSoup.find(class_="logininfo")   
                  if not LoginStatusConntent is None:
                     log("Checking login status.", 4)  
                     #Lookup in the Moodle source if it is standard (login / log in on every page)
                     #Is a relogin needed ? Try to figure out when relogin is needed.
                     if "Logout" not in str(LoginStatusConntent) and "logout" not in str(LoginStatusConntent):
                        log("Try to relogin, connection maybe lost.", 3)
                        
                        try:
                           responseLogin = urllib2.urlopen(req, timeout=10)
                        except Exception:
                           log("Connection lost! It is not possible to connect to moodle!", 3)
                           continue
                         
                        LoginContents = responseLogin.read()
                         
                         
                        if "errorcode=" in responseLogin.geturl():
                            log(" Cannot login. Check your login data.", 3)
                            continue
                        
                        #Lookup in the Moodle source if it is standard   ("Logout" on every Page)
                        LoginSoup = BeautifulSoup(LoginContents, "lxml") 
                        LoginStatusConntent = LoginSoup.find(class_="logininfo")
                        if LoginStatusConntent is None or ("Logout" not in str(LoginStatusConntent)  and "logout" not in str(LoginStatusConntent) ):  
                            log(" Cannot connect to moodle or Moodle has changed. Crawler is not logged in. Check your login data.", 3)# 
                            continue
                          
                        #reload page
                        try:
                           webFileTrap = urllib2.urlopen(hrefT, timeout=10)
                        except Exception:
                           log("Connection lost! File does not exist!", 3)
                           continue
       
                        log("Download has restarted.", 4)
                        #webFileTrapContent = webFileTrap.read()
                        webFileTrapContent = ""
            
                        try:
                            total_size = webFileTrap.info().getheader('Content-Length').strip()
                            header = True
                        except Exception:
                            log("No Content-Length available.", 5)
                            header = False # a response doesn't always include the "Content-Length" header
                
                        if header:
                            total_size = int(total_size)
                 
                        bytes_so_far = 0
                 
                        while True:
                            webFileTrapBuffer = webFileTrap.read(8192)
                            if not webFileTrapBuffer: 
                                break
                        
                            bytes_so_far += len(webFileTrapBuffer) 
                            webFileTrapContent = webFileTrapContent + webFileTrapBuffer
                
                            if not header: 
                               log("Downloaded %d bytes" % (bytes_so_far), 5)
                 
                            else:
                               percent = float(bytes_so_far) / total_size
                               percent = round(percent*100, 2)
                               log("Downloaded %d of %d bytes (%0.2f%%)\r" % (bytes_so_far, total_size, percent), 5)
              
   
                        log("Download complete.", 4)  
                     else:
                        log("Crawler is still loged in.", 4)  
   
   
   
     
               webfileTrapurl = webFileTrap.geturl().split('/')[-1].split('?')[0].encode('ascii', 'ignore').replace('/', '|').replace('\\', '|').replace(' ', '_')
    
               if webfileTrapurl == "":
                  webfileTrapurl = "index.html"
                      
               url = sub_dir + webfileTrapurl
               file_name = url 
               if file_name[-4:] == ".php":
                  file_name = file_name[:len(file_name) - 4] + ".html"
    
               if file_name.split('.')[-1] == file_name:
                  file_name = file_name + ".html"
   
               #file_name = urllib.unquote(url).decode('utf8')
                   
               old_name = ""
               if os.path.isfile(file_name):
                  old_name = file_name
                  fileend = file_name.split('.')[-1]
                  filebegin = file_name[:(len(file_name) - len(fileend)) - 1]
                    
                  ii = 1
                  while True:
                   new_name = filebegin + "_" + str(ii) + "." + fileend
                   if not os.path.isfile(new_name):
                      file_name = new_name
                      break
                   ii += 1
                 
     
               log("Creating new file: '" +  file_name + "'")
               pdfFile = open(file_name, 'wb')
               pdfFile.write(webFileTrapContent)
               webFileTrap.close()
               pdfFile.close()
               logFileWriter = open(root_directory + course[0] + "/crawlhistory.log", 'ab')
               logFileWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " "+ hrefT + " saved to '" + file_name + "'\n")
               logFileWriter.close()
               logFileReader = open(root_directory + course[0] + "/crawlhistory.log", 'rb')
               logFile = logFileReader.read()
               logFileReader.close()
                       
                        
                   
                       
        if trapscount == 0:
           if webfileurlCourseFile[-4:] == ".php" or webfileurlCourseFile[-4:] == ".html":
              log("Ups no link was found in this folder!", 3)
 
           log("Try to save the page: " + hrefCourseFile, 4)

           if webfileurlCourseFile == "":
              webfileurlCourseFile = "index.html"
 
           url = current_dir + webfileurlCourseFile
           #file_name = urllib.unquote(url).decode('utf8')
 
           file_name = url
           if file_name[-4:] == ".php":
              file_name = file_name[:len(file_name) - 4] + ".html"
                  
           if file_name.split('.')[-1] == file_name:
              file_name = file_name + ".html"
 

           old_name = ""
           if os.path.isfile(file_name):
                 
              old_name = file_name
              fileend = file_name.split('.')[-1]
              filebegin = file_name[:(len(file_name) - len(fileend)) - 1]
                   
              ii = 1
              while True:
               new_name = filebegin + "_" + str(ii) + "." + fileend
               if not os.path.isfile(new_name):
                  file_name = new_name
                  break
               ii += 1
                   
           log("Creating file: '" + file_name + "'")
           pdfFile = open(file_name, 'wb')
           pdfFile.write(webFileContent)
           webFileCourseFile.close()
           pdfFile.close()
           logFileWriter = open(root_directory + course[0] + "/crawlhistory.log", 'ab')
           logFileWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " "+ hrefCourseFile + " saved to '" + file_name + "'\n")
           logFileWriter.close()
           logFileReader = open(root_directory + course[0] + "/crawlhistory.log", 'rb')
           logFile = logFileReader.read()
           logFileReader.close()

    #find dublication in folder  current_dir
    filesBySize = {}
    log('Scanning directory "%s"....' % current_dir, 5)
    os.path.walk(current_dir, walker, filesBySize)

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


log("Update Complete")
