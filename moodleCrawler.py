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


conf = ConfigParser()
project_dir = os.path.dirname(os.path.abspath(__file__))
conf.read(os.path.join(project_dir, 'config.ini'))

#ToDo: use quotation marks to read in settings    | check if a slash is at the end of the path
root_directory = conf.get("dirs", "root_dir")
username = conf.get("auth", "username")
password = conf.get("auth", "password")
crawlforum = conf.get("crawl", "forum") #/forum/
usehistory = conf.get("crawl", "history") #do not recrawl

authentication_url = conf.get("auth", "url").strip('\'"')

  
cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
opener.addheaders = [('User-agent', 'HeyThanksForWatchingThisAgenet')]
urllib2.install_opener(opener)


payload = {
    'username': username,
    'password': password
}


data = urllib.urlencode(payload)


# Connection established?
print(datetime.now().strftime('%H:%M:%S') + "  Try to login...")

req = urllib2.Request(authentication_url, data)
#response = urllib2.urlopen(req)
try:
   responseLogin = urllib2.urlopen(req)
except Exception:
   print(datetime.now().strftime('%H:%M:%S') + "Connection lost! It is not possible to connect to moodle!")
   exit(1)
LoginContents = responseLogin.read()
 
if "errorcode=" in responseLogin.geturl():
    print(datetime.now().strftime('%H:%M:%S') + "   Cannot login. Check your login data.")
    exit(1)

#Lookup in the Moodle source if it is standard   ("Logout" on every Page)
LoginSoup = BeautifulSoup(LoginContents, "lxml") 
LoginStatusConntent = LoginSoup.find(class_="logininfo")
if LoginStatusConntent is None or ("Logout" not in str(LoginStatusConntent) and "logout" not in str(LoginStatusConntent)): 
   print(datetime.now().strftime('%H:%M:%S') + "   Cannot connect to moodle or Moodle has changed. Crawler is not logged in. Check your login data.") 
   exit(1)


print(datetime.now().strftime('%H:%M:%S') + "  Logged in!")
 
 

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
 


print(datetime.now().strftime('%H:%M:%S') + "  Searching Courses...")

#Lookup in the Moodle source if it is standard (moodlePath/my/ are my courses)
try:
   responseCourses = urllib2.urlopen(mainpageURL + "my/")
except Exception:
   print(datetime.now().strftime('%H:%M:%S') + " Connection lost! It is not possible to connect to moodle!")
   exit(1)
CoursesContents = responseCourses.read()




CoursesContentsSoup = BeautifulSoup(CoursesContents, "lxml")

CoursesContentsList = CoursesContentsSoup.find(id="region-main")

#CoursesContentsList = CoursesContents.split('class="block_course_list  block list_block"')[1].split('class="footer"')[0]
#>Meine Kurse</h2>
 
if CoursesContentsList is None:
   print(datetime.now().strftime('%H:%M:%S') + "  Unable to find Courses")
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
    print(datetime.now().strftime('%H:%M:%S') + "  Found Course: '" + course_name + "'")




for course in courses:
    if not os.path.isdir(root_directory + course[0]):
        os.mkdir(root_directory+course[0])
    #response1 = urllib2.urlopen(course[1])
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



    print(datetime.now().strftime('%H:%M:%S') + "  Check Course: '" + course[0] + "'")

    try:
       responseCourseLink = urllib2.urlopen(course[1])
    except Exception:
       print(datetime.now().strftime('%H:%M:%S') + " Connection lost! Course does not exist!")
       continue

    CourseLinkContent = responseCourseLink.read()

 
         

    if "text/html" in responseCourseLink.info().getheader('Content-Type'):

       CourseSoup = BeautifulSoup(CourseLinkContent, "lxml") 
       LoginStatusConntent = CourseSoup.find(class_="logininfo")
       if not LoginStatusConntent is None:
       
          print(datetime.now().strftime('%H:%M:%S') + " Checking login status.")  
          #Lookup in the Moodle source if it is standard (login / log in on every page)
          #Is a relogin needed ? Try to figure out when relogin is needed.
          if "Logout" not in str(LoginStatusConntent) and "logout" not in str(LoginStatusConntent):
             print(datetime.now().strftime('%H:%M:%S') + " Try to relogin, connection maybe lost.")
             
             try:
                responseLogin = urllib2.urlopen(req)
             except Exception:
                print(datetime.now().strftime('%H:%M:%S') + " Connection lost! It is not possible to connect to moodle!")
                continue
              
             LoginContents = responseLogin.read()
              
              
             if "errorcode=" in responseLogin.geturl():
                 print(datetime.now().strftime('%H:%M:%S') + "   Cannot login. Check your login data.")
                 continue
             
             #Lookup in the Moodle source if it is standard   ("Logout" on every Page)
             LoginSoup = BeautifulSoup(LoginContents, "lxml") 
             LoginStatusConntent = LoginSoup.find(class_="logininfo")
             if LoginStatusConntent is None or ("Logout" not in str(LoginStatusConntent) and "logout" not in str(LoginStatusConntent)):  
                 print(datetime.now().strftime('%H:%M:%S') + "   Cannot connect to moodle or Moodle has changed. Crawler is not logged in. Check your login data.")
                 continue
               
             #reload page  
             print(datetime.now().strftime('%H:%M:%S') + " Recheck Course: '" + course[0] + "'")
             try:
                responseCourseLink = urllib2.urlopen(course[1])
             except Exception:
                print(datetime.now().strftime('%H:%M:%S') + " Connection lost! Course does not exist!")
                continue
       
             CourseLinkContent = responseCourseLink.read()
          else:
             print(datetime.now().strftime('%H:%M:%S') + " Crawler is still loged in.")           

 

    course_links = CourseSoup.find(id="region-main").find_all('a')


    current_dir = root_directory + course[0] + "/"
    for link in course_links:
        hrefCourseFile = link.get('href')

        if hrefCourseFile is None or hrefCourseFile == "":
             print(datetime.now().strftime('%H:%M:%S') + " There went something wrong, this is an empty link.")
             continue
 

        # Checking only resources... Ignoring forum and folders, etc
        #if "/pluginfile.php/" in hrefCourseFile or "/resource/" in hrefCourseFile  or "/mod/page/" in hrefCourseFile or "/folder/" in hrefCourseFile:
        
        if not hrefCourseFile.startswith("https://") and not hrefCourseFile.startswith("http://") and not hrefCourseFile.startswith("www."):
           if hrefCourseFile.startswith('/'):
              hrefCourseFile = course[1][:(len(course[1]) - len(course[1].split('/')[-1])) - 1] + hrefCourseFile
           else:
              hrefCourseFile = course[1][:len(course[1]) - len(course[1].split('/')[-1])] + hrefCourseFile
        

        
        print(datetime.now().strftime('%H:%M:%S') + "  Found Link: " + hrefCourseFile)
        if usehistory == "true" and hrefCourseFile in logFile:
           print(datetime.now().strftime('%H:%M:%S') + " This link was crawled in the past. I will not recrawl it, change the setings if you want to recrawl it.")
           continue

        #print(datetime.now().strftime('%H:%M:%S') + "  found: " + hrefCourseFile + " in " + course[0])
        #cj1 = cookielib.CookieJar()
        #opener1 = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj1))
        #opener1.addheaders = [('User-agent', 'HeyThanksForWatchingThisAgenet')]
        #urllib2.install_opener(opener1)
        #req1 = urllib2.Request(authentication_url, data)
        #resp = urllib2.urlopen(req1)
 

        isexternlink = False

        if not domainMoodle in hrefCourseFile:
           print(datetime.now().strftime('%H:%M:%S') + " This is an external link. I will store it in the 'externel-links.log' file")
           print(datetime.now().strftime('%H:%M:%S') + " I will try to find more links on the external page! This will fail maybe.")
           externalLinkWriter = open(current_dir + "externel-links.log", 'ab')
           externalLinkWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " "+ hrefCourseFile + "\n")
           externalLinkWriter.close()
           isexternlink = True


        if crawlforum == "false" and "/forum/" in hrefCourseFile:
           print(datetime.now().strftime('%H:%M:%S') + " Ups this is a forum. I do not crawl this forum. Change the settings if you want to crawl forums.")
           continue

        #webFileCourseFile = urllib2.urlopen(hrefCourseFile)
        try:
           webFileCourseFile = urllib2.urlopen(hrefCourseFile)
        except Exception:
           print(datetime.now().strftime('%H:%M:%S') + " Connection lost! Link does not exist!")
           continue
        

        print(datetime.now().strftime('%H:%M:%S') + " Download has started.")

        webFileContent = ""

        try:
            total_size = webFileCourseFile.info().getheader('Content-Length').strip()
            header = True
        except Exception:
            print(datetime.now().strftime('%H:%M:%S') + " No Content-Length available.")
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
               print(datetime.now().strftime('%H:%M:%S') + " Downloaded %d bytes" % (bytes_so_far))
 
            else:
               percent = float(bytes_so_far) / total_size
               percent = round(percent*100, 2)
               print(datetime.now().strftime('%H:%M:%S') + " Downloaded %d of %d bytes (%0.2f%%)\r" % (bytes_so_far, total_size, percent))
 

        print(datetime.now().strftime('%H:%M:%S') + " Download complete.")  



        
        if "text/html" in webFileCourseFile.info().getheader('Content-Type'):

           print(datetime.now().strftime('%H:%M:%S') + " Debug -2")  
           webFileSoup = BeautifulSoup(webFileContent, "lxml") 
   
           if not isexternlink:
              LoginStatusConntent = webFileSoup.find(class_="logininfo")
              print(datetime.now().strftime('%H:%M:%S') + " Debug -1")  
   
              if not LoginStatusConntent is None:
                 print(datetime.now().strftime('%H:%M:%S') + " Checking login status.")  
              
                 #Lookup in the Moodle source if it is standard (login / log in on every page)
                 #Is a relogin needed ? Try to figure out when relogin is needed.
                 if "Logout" not in str(LoginStatusConntent) and "logout" not in str(LoginStatusConntent):
                    print(datetime.now().strftime('%H:%M:%S') + " Try to relogin, connection maybe lost.")
                    
                    try:
                       responseLogin = urllib2.urlopen(req)
                    except Exception:
                       print(datetime.now().strftime('%H:%M:%S') + " Connection lost! It is not possible to connect to moodle!")
                       continue
                     
                    LoginContents = responseLogin.read()
                     
                     
                    if "errorcode=" in responseLogin.geturl():
                        print(datetime.now().strftime('%H:%M:%S') + "   Cannot login. Check your login data.")
                        continue
                    
                    #Lookup in the Moodle source if it is standard   ("Logout" on every Page)
                    LoginSoup = BeautifulSoup(LoginContents, "lxml") 
                    LoginStatusConntent = LoginSoup.find(class_="logininfo")
                    if LoginStatusConntent is None or ("Logout" not in str(LoginStatusConntent) and "logout" not in str(LoginStatusConntent)):  
                        print(datetime.now().strftime('%H:%M:%S') + "   Cannot connect to moodle or Moodle has changed. Crawler is not logged in. Check your login data.")
                        continue
                      
                    #reload page
                    try:
                       webFileCourseFile = urllib2.urlopen(hrefCourseFile)
                    except Exception:
                       print(datetime.now().strftime('%H:%M:%S') + " Connection lost! Link does not exist!")
                       continue
                    
                      
                    print(datetime.now().strftime('%H:%M:%S') + " Download has restarted.")
                    #webFileContent = webFileCourseFile.read()
                    webFileContent = ""
   
                    try:
                        total_size = webFileCourseFile.info().getheader('Content-Length').strip()
                        header = True
                    except Exception:
                        print(datetime.now().strftime('%H:%M:%S') + " No Content-Length available.")
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
                           print(datetime.now().strftime('%H:%M:%S') + " Downloaded %d bytes" % (bytes_so_far))
             
                        else:
                           percent = float(bytes_so_far) / total_size
                           percent = round(percent*100, 2)
                           print(datetime.now().strftime('%H:%M:%S') + " Downloaded %d of %d bytes (%0.2f%%)\r" % (bytes_so_far, total_size, percent))
    
   
                    print(datetime.now().strftime('%H:%M:%S') + " Download complete.")  
                 else:
                    print(datetime.now().strftime('%H:%M:%S') + " Crawler is still loged in.")  





        webfileurlCourseFile = webFileCourseFile.geturl().split('/')[-1].split('?')[0].encode('ascii', 'ignore').replace('/', '|').replace('\\', '|').replace(' ', '_')

        trapscount = 0
         
        
        if "text/html" in webFileCourseFile.info().getheader('Content-Type') or webfileurlCourseFile[-4:] == ".php" or webfileurlCourseFile[-4:] == ".html":
          print(datetime.now().strftime('%H:%M:%S') + "  It is a  folder! Try to find more links!")
          
          trap_links = webFileSoup.find(id="region-main").find_all('a')
               
          myTitle = webFileSoup.title.string
          
          myTitle = myTitle.encode('ascii', 'ignore').replace('/', '|').replace('\\', '|').replace(' ', '_').replace('.', '_').replace(course[0] + ":_", '')

          sub_dir = root_directory + course[0] + "/" + myTitle + "/"
          if not os.path.isdir(root_directory + course[0] + "/" + myTitle):
             os.mkdir(root_directory + course[0] + "/" + myTitle)

          for traplink in trap_links:
            hrefT = traplink.get('href')
               
            if hrefT is None or hrefT == "":
                 print(datetime.now().strftime('%H:%M:%S') + " There went something wrong, this is an empty link.")
                 continue

            # Checking only resources... Ignoring forum and folders, etc
            #if "/pluginfile.php/" in hrefT or "/resource/" in hrefT:
            if not hrefT.startswith("https://") and not hrefT.startswith("http://") and not hrefT.startswith("www."):
               if hrefT.startswith('/'):
                  hrefT = hrefCourseFile[:(len(hrefCourseFile) - len(hrefCourseFile.split('/')[-1])) - 1] + hrefT
               else:
                  hrefT = hrefCourseFile[:len(hrefCourseFile) - len(hrefCourseFile.split('/')[-1])] + hrefT
            
               

            trapscount = trapscount + 1
            print(datetime.now().strftime('%H:%M:%S') + "  Found link in folder: " + hrefT)
            if usehistory == "true" and hrefT in logFile:
              print(datetime.now().strftime('%H:%M:%S') + " This link was crawled in the past. I will not recrawl it, change the setings if you want to recrawl it.")
              continue

            isexternLinkT = False

            if not domainMoodle in hrefT: 
               print(datetime.now().strftime('%H:%M:%S') + " This is an external link. I will store it in the 'externel-links.log' file")
               externalLinkWriter = open(sub_dir + "externel-links.log", 'ab')
               externalLinkWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " "+ hrefT + "\n")
               externalLinkWriter.close()
               isexternLinkT = True

            try:
               webFileTrap = urllib2.urlopen(hrefT)
            except Exception:
               print(datetime.now().strftime('%H:%M:%S') + " Connection lost! File does not exist!")
               continue

            print(datetime.now().strftime('%H:%M:%S') + " Download has started.")
           # webFileTrapContent = webFileTrap.read()


            webFileTrapContent = ""

            try:
                total_size = webFileTrap.info().getheader('Content-Length').strip()
                header = True
            except Exception:
                print(datetime.now().strftime('%H:%M:%S') + " No Content-Length available.")
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
                   print(datetime.now().strftime('%H:%M:%S') + " Downloaded %d bytes" % (bytes_so_far))
     
                else:
                   percent = float(bytes_so_far) / total_size
                   percent = round(percent*100, 2)
                   print(datetime.now().strftime('%H:%M:%S') + " Downloaded %d of %d bytes (%0.2f%%)\r" % (bytes_so_far, total_size, percent))
 

            print(datetime.now().strftime('%H:%M:%S') + " Download complete.")  

   

            if not isexternLinkT and "text/html" in webFileTrap.info().getheader('Content-Type'):  
               print(datetime.now().strftime('%H:%M:%S') + " Debug -2")  
               TrapSoup = BeautifulSoup(webFileTrapContent, "lxml") 
               LoginStatusConntent = TrapSoup.find(class_="logininfo")
               print(datetime.now().strftime('%H:%M:%S') + " Debug -1")  
               if not LoginStatusConntent is None:
                  print(datetime.now().strftime('%H:%M:%S') + " Checking login status.")  
                  #Lookup in the Moodle source if it is standard (login / log in on every page)
                  #Is a relogin needed ? Try to figure out when relogin is needed.
                  if "Logout" not in str(LoginStatusConntent) and "logout" not in str(LoginStatusConntent):
                     print(datetime.now().strftime('%H:%M:%S') + " Try to relogin, connection maybe lost.")
                     
                     try:
                        responseLogin = urllib2.urlopen(req)
                     except Exception:
                        print(datetime.now().strftime('%H:%M:%S') + " Connection lost! It is not possible to connect to moodle!")
                        continue
                      
                     LoginContents = responseLogin.read()
                      
                      
                     if "errorcode=" in responseLogin.geturl():
                         print(datetime.now().strftime('%H:%M:%S') + "   Cannot login. Check your login data.")
                         continue
                     
                     #Lookup in the Moodle source if it is standard   ("Logout" on every Page)
                     LoginSoup = BeautifulSoup(LoginContents, "lxml") 
                     LoginStatusConntent = LoginSoup.find(class_="logininfo")
                     if LoginStatusConntent is None or ("Logout" not in str(LoginStatusConntent)  and "logout" not in str(LoginStatusConntent) ):  
                         print(datetime.now().strftime('%H:%M:%S') + "   Cannot connect to moodle or Moodle has changed. Crawler is not logged in. Check your login data.")# 
                         continue
                       
                     #reload page
                     try:
                        webFileTrap = urllib2.urlopen(hrefT)
                     except Exception:
                        print(datetime.now().strftime('%H:%M:%S') + " Connection lost! File does not exist!")
                        continue
    
                     print(datetime.now().strftime('%H:%M:%S') + " Download has restarted.")
                     #webFileTrapContent = webFileTrap.read()
                     webFileTrapContent = ""
         
                     try:
                         total_size = webFileTrap.info().getheader('Content-Length').strip()
                         header = True
                     except Exception:
                         print(datetime.now().strftime('%H:%M:%S') + " No Content-Length available.")
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
                            print(datetime.now().strftime('%H:%M:%S') + " Downloaded %d bytes" % (bytes_so_far))
              
                         else:
                            percent = float(bytes_so_far) / total_size
                            percent = round(percent*100, 2)
                            print(datetime.now().strftime('%H:%M:%S') + " Downloaded %d of %d bytes (%0.2f%%)\r" % (bytes_so_far, total_size, percent))
           

                     print(datetime.now().strftime('%H:%M:%S') + " Download complete.")  
                  else:
                     print(datetime.now().strftime('%H:%M:%S') + " Crawler is still loged in.")  



 
            print(datetime.now().strftime('%H:%M:%S') + " Debug 0")  
            webfileTrapurl = webFileTrap.geturl().split('/')[-1].split('?')[0].encode('ascii', 'ignore').replace('/', '|').replace('\\', '|').replace(' ', '_')

 
            print(datetime.now().strftime('%H:%M:%S') + " Debug 1")  
            if webfileTrapurl == "":
               webfileTrapurl = "index.html"
                  
 
            print(datetime.now().strftime('%H:%M:%S') + " Debug 2")  
            url = sub_dir + webfileTrapurl
            file_name = url 
            if file_name[-4:] == ".php":
               file_name = file_name[:len(file_name) - 4] + ".html"

 
            print(datetime.now().strftime('%H:%M:%S') + " Debug 3")  
            if file_name.split('.')[-1] == file_name:
               file_name = file_name + ".html"

            #file_name = urllib.unquote(url).decode('utf8')
               
 
            print(datetime.now().strftime('%H:%M:%S') + " Debug 4")  
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
              
  
            print(datetime.now().strftime('%H:%M:%S') + "  Creating file: '" +  file_name + "'")
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
              print(datetime.now().strftime('%H:%M:%S') + " Ups no link was found in this folder!")
 
           print(datetime.now().strftime('%H:%M:%S') + "  Try to save the page: " + hrefCourseFile)

           if webfileurlCourseFile == "":
              webfileurlCourseFile = "index.html"

           print(datetime.now().strftime('%H:%M:%S') + " Debuga 1")
           url = current_dir + webfileurlCourseFile
           #file_name = urllib.unquote(url).decode('utf8')

           print(datetime.now().strftime('%H:%M:%S') + " Debuga 2")
           file_name = url
           if file_name[-4:] == ".php":
              file_name = file_name[:len(file_name) - 4] + ".html"
                 
           print(datetime.now().strftime('%H:%M:%S') + " Debuga 3")

           if file_name.split('.')[-1] == file_name:
              file_name = file_name + ".html"

           print(datetime.now().strftime('%H:%M:%S') + " Debuga 4")

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
                  
           print(datetime.now().strftime('%H:%M:%S') + " Debuga 5")
                
           print(datetime.now().strftime('%H:%M:%S') + "  Creating file: '" + file_name + "'")
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
    print(datetime.now().strftime('%H:%M:%S') + ' Scanning directory "%s"....' % current_dir)
    os.path.walk(current_dir, walker, filesBySize)

    print(datetime.now().strftime('%H:%M:%S') + ' Finding potential dupes...')
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
        print(datetime.now().strftime('%H:%M:%S') + ' Testing %d files of size %d...' % (len(inFiles), k))
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

    print(datetime.now().strftime('%H:%M:%S') + ' Found %d sets of potential dupes...' % potentialCount)
    print(datetime.now().strftime('%H:%M:%S') + ' Scanning for real dupes...')

    dupes = []
    for aSet in potentialDupes:
        outFiles = []
        hashes = {}
        for fileName in aSet:
            print(datetime.now().strftime('%H:%M:%S') + ' Scanning file "%s"...' % fileName)
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
        print(datetime.now().strftime('%H:%M:%S') + ' Original is %s' % d[0])
        for f in d[1:]:
            i = i + 1
            print(datetime.now().strftime('%H:%M:%S') + ' Deleting %s' % f)
            os.remove(f)
        print()


print(datetime.now().strftime('%H:%M:%S') + "  Update Complete")
