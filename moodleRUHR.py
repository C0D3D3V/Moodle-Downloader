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

root_directory = conf.get("dirs", "root_dir")
username = conf.get("auth", "username")
password = conf.get("auth", "password")
crawlforum = conf.get("crawl", "forum") #/forum/
usehistory = conf.get("crawl", "history") #do not recrawl

authentication_url = conf.get("auth", "url").strip('\'"')


cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
opener.addheaders = [('User-agent', 'TheBigBoy')]
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
   response = urllib2.urlopen(req)
except Exception:
   print(datetime.now().strftime('%H:%M:%S') + " It is not possible to connect to moodle!")
   exit(1)
contents = response.read()


if "index.php?errorcode=" in response.geturl():
    print(datetime.now().strftime('%H:%M:%S') + "   Cannot login")
    exit(1)

if "My courses" not in contents and "Meine Kurse" not in contents:
    print(datetime.now().strftime('%H:%M:%S') + "   Cannot connect to moodle or Moodle was changed")
    exit(1)


print(datetime.now().strftime('%H:%M:%S') + "  Logged in!")
print(datetime.now().strftime('%H:%M:%S') + "  Searching Courses...")

courses = contents.split('<div id="frontpage-course-list">')[1].split('<aside id="block-region-side-pre" ')[0]
#>Meine Kurse</h2>

regex = re.compile('class="coursename">(.*?)</h3>')
course_list = regex.findall(courses)
courses = []

#blockCourse = True

for course_string in course_list:
    soup = BeautifulSoup(course_string, "lxml")
    a = soup.find('a')
    course_name = a.text.encode('ascii', 'ignore').replace('/', '|').replace('\\', '|').replace(' ', '_').replace('.', '_')
    course_link = a.get('href')
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
       response1 = urllib2.urlopen(course[1])
    except Exception:
       print(datetime.now().strftime('%H:%M:%S') + "Course does not exist!")
       continue

    scrap = response1.read()
    soup = BeautifulSoup(scrap, "lxml")

    course_links = soup.find(class_="span8 pull-right").find_all('a')


    current_dir = root_directory + course[0] + "/"
    for link in course_links:
        href = link.get('href')
 

        # Checking only resources... Ignoring forum and folders, etc
        #if "/pluginfile.php/" in href or "/resource/" in href  or "/mod/page/" in href or "/folder/" in href:
        
        if not href.startswith("https://") and not href.startswith("http://") and not href.startswith("www."):
           if href.startswith('/'):
              href = course[1][:(len(course[1]) - len(course[1].split('/')[-1])) - 1] + href
           else:
              href = course[1][:len(course[1]) - len(course[1].split('/')[-1])] + href
        

        
        print(datetime.now().strftime('%H:%M:%S') + "  Found Link: " + href)
        if usehistory == "true" and href in logFile:
           print(datetime.now().strftime('%H:%M:%S') + " This link was crawled in the past. I will not recrawl it, change the setings if you want to recrawl it.")
           continue

        #print(datetime.now().strftime('%H:%M:%S') + "  found: " + href + " in " + course[0])
        cj1 = cookielib.CookieJar()
        opener1 = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj1))
        opener1.addheaders = [('User-agent', 'TheBigBoy')]
        urllib2.install_opener(opener1)
        req1 = urllib2.Request(authentication_url, data)
        #resp = urllib2.urlopen(req1)
        try:
           resp = urllib2.urlopen(req1)
        except Exception:
           print(datetime.now().strftime('%H:%M:%S') + " It is not possible to connect to moodle!")
           continue
        



        if not "moodle.ruhr-uni-bochum" in href:
           print(datetime.now().strftime('%H:%M:%S') + " This is an external link. I will store it in the 'externel-links.log' file")
           print(datetime.now().strftime('%H:%M:%S') + " I will try to find more links on the external page! This will fail maybe.")
           externalLinkWriter = open(current_dir + "externel-links.log", 'ab')
           externalLinkWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " "+ href + "\n")
           externalLinkWriter.close()


        if crawlforum == "false" and "/forum/" in href:
           print(datetime.now().strftime('%H:%M:%S') + " Ups this is a forum. I do not crawl this forum. Change the settings if you want to crawl forums.")
           continue

        #webFile = urllib2.urlopen(href)
        try:
           webFile = urllib2.urlopen(href)
        except Exception:
           print(datetime.now().strftime('%H:%M:%S') + "Link does not exist!")
           continue
        


        webfileurl = webFile.geturl().split('/')[-1].split('?')[0].encode('ascii', 'ignore').replace('/', '|').replace('\\', '|').replace(' ', '_')

        trapscount = 0
         
         
        if webfileurl[-4:] == ".php" or webfileurl[-4:] == ".html":
          print(datetime.now().strftime('%H:%M:%S') + "  It is a  folder! Try to find more links!")
          souptrap = BeautifulSoup(webFile, "lxml")
           

          trap_links = souptrap.find(class_="span8 pull-right").find_all('a')
               
          myTitle = souptrap.title.string
          
          myTitle = myTitle.encode('ascii', 'ignore').replace('/', '|').replace('\\', '|').replace(' ', '_').replace('.', '_').replace(course[0] + ":_", '')

          sub_dir = root_directory + course[0] + "/" + myTitle + "/"
          if not os.path.isdir(root_directory + course[0] + "/" + myTitle):
             os.mkdir(root_directory + course[0] + "/" + myTitle)

          for traplink in trap_links:
            hrefT = traplink.get('href')
              
            if hrefT == None:
               print(datetime.now().strftime('%H:%M:%S') + " Somthing bad happend!")
               continue

            # Checking only resources... Ignoring forum and folders, etc
            #if "/pluginfile.php/" in hrefT or "/resource/" in hrefT:
            if not hrefT.startswith("https://") and not hrefT.startswith("http://") and not hrefT.startswith("www."):
               if hrefT.startswith('/'):
                  hrefT = href[:(len(href) - len(href.split('/')[-1])) - 1] + hrefT
               else:
                  hrefT = href[:len(href) - len(href.split('/')[-1])] + hrefT
            
               

            trapscount = trapscount + 1
            print(datetime.now().strftime('%H:%M:%S') + "  Found link in folder: " + hrefT)
            if usehistory == "true" and hrefT in logFile:
              print(datetime.now().strftime('%H:%M:%S') + " This link was crawled in the past. I will not recrawl it, change the setings if you want to recrawl it.")
              continue


            if not "moodle.ruhr-uni-bochum" in hrefT: 
               print(datetime.now().strftime('%H:%M:%S') + " This is an external link. I will store it in the 'externel-links.log' file")
               externalLinkWriter = open(sub_dir + "externel-links.log", 'ab')
               externalLinkWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " "+ hrefT + "\n")
               externalLinkWriter.close()

            try:
               webFileT = urllib2.urlopen(hrefT)
            except Exception:
               print(datetime.now().strftime('%H:%M:%S') + " File does not exist!")
               continue


            webfileTurl = webFileT.geturl().split('/')[-1].split('?')[0].encode('ascii', 'ignore').replace('/', '|').replace('\\', '|').replace(' ', '_')

            if webfileTurl == "":
               webfileTurl = "index.html"
                  
            url = sub_dir + webfileTurl
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
              
                 
            print(datetime.now().strftime('%H:%M:%S') + "  Creating file: ", file_name)
            pdfFile = open(file_name, 'wb')
            pdfFile.write(webFileT.read())
            webFileT.close()
            pdfFile.close()
            logFileWriter = open(root_directory + course[0] + "/crawlhistory.log", 'ab')
            logFileWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " "+ hrefT + " saved to '" + file_name + "'\n")
            logFileWriter.close()
            logFileReader = open(root_directory + course[0] + "/crawlhistory.log", 'rb')
            logFile = logFileReader.read()
            logFileReader.close()
                    
                     
                   
                       
        if trapscount == 0:
           if webfileurl[-4:] == ".php" or webfileurl[-4:] == ".html":
              print(datetime.now().strftime('%H:%M:%S') + " Ups no link was found in this folder!")

           print(datetime.now().strftime('%H:%M:%S') + "  Try to save the page: " + href)

           if webfileurl == "":
              webfileurl = "index.html"

           url = current_dir + webfileurl
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
                  
                
           print(datetime.now().strftime('%H:%M:%S') + "  Creating file: ", file_name)
           pdfFile = open(file_name, 'wb')
           pdfFile.write(webFile.read())
           webFile.close()
           pdfFile.close()
           logFileWriter = open(root_directory + course[0] + "/crawlhistory.log", 'ab')
           logFileWriter.write(datetime.now().strftime('%d.%m.%Y %H:%M:%S') + " "+ href + " saved to '" + file_name + "'\n")
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
