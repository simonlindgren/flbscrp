"""
FLBSCRAPE

Assumes tor proxy running on port 9050

$ sudo apt-get install tor
$ sudo service tor start
$ sudo service tor restart

"""

import requests
from bs4 import BeautifulSoup
import re
import sqlite3
import datetime
from fake_useragent import UserAgent
import pandas as pd
from time import sleep
import random
import os


def get_thread(thread_url, db_name, startpage):
    page = startpage
    current_url = thread_url + "p" + str(page)
    previouslyaddedpageposts = []

    with open("flbscrp.log", "a") as logfile:
        logfile.write("Running get_thread()\n")

    while True:
        postidlist = []
        userlist = []
        datelist = []
        timelist = []
        bodylist = []
        inreplylist = []

        headers = {'User-Agent': UserAgent().random}
        current_url = thread_url + "p" + str(page)
        with open("flbscrp.log", "a") as logfile:
            logfile.write("Getting " + current_url + "\n")

        try:
            # r = requests.get(current_url, headers=headers) # to run without tor
            proxies = {'http': 'socks5://127.0.0.1:9050',
                       'https': 'socks5://127.0.0.1:9050'}  # to run with tor
            r = requests.get(current_url, proxies=proxies, headers=headers)  # to run with tor
        except:
            with open("flbscrp.log", "a") as logfile:
                logfile.write("There was an error. Proceeding to next url. Check 'failed_urls.txt'\n")
            with open("failed_urls.txt", "a") as failfile:
                failfile.write(current_url + "\n")  # record failed urls
            return(9000)
            page += 1

        html = r.content
        soup = BeautifulSoup(html, "lxml")

        """
        Get a list of posts and their headings
        """
        postsoup = soup.findAll("div", class_="post_message")
        heading = soup.findAll("div", class_="post-heading")

        """
        Check the page length
        """
        # If length == 12 it is a full page:
        with open("flbscrp.log", "a") as logfile:
            logfile.write("---> Length of page: " + str(len(postsoup)) + " posts.\n")

        """
        Handle the problem with scraper stopping at 'moderator messages'
        """
        modsoup = soup.findAll("div", class_="panel panel-warning panel-form")
        try:
            titlediv = soup.find("div", class_="page-title")
            title = re.sub(r"[\n\t]*", "", titlediv.text)  # clean out tab, newlines
            with open("flbscrp.log", "a") as logfile:
                logfile.write("---> Thread title:"+ title + "\n")
        except:
            title = "<error getting title>"  # if title extraction fails.
            with open("flbscrp.log", "a") as logfile:
                logfile.write("---> Thread title:" + title + "\n")

        """
        Extract the data add add to lists
        """

        # Get post ids
        for p in postsoup:
            postid = re.findall("(?<=id\=\"post\_message\_).*?(?=\"\>)", str(p),
                                re.IGNORECASE)
            if postid:
                postidlist.append(postid[0])

        # Get usernames
        username = soup.findAll("li", class_="dropdown-header")
        for u in username:
            if u.text == "Ämnesverktyg":  # exclude false positive.
                continue
            else:
                userlist.append(u.text)

        # Get datetime
        for h in heading:
            yesterday = datetime.date.today() - datetime.timedelta(1)
            todaymatch = re.findall("Idag,\s\d\d\:\d\d", h.text, re.IGNORECASE)
            yesterdaymatch = re.findall("Igår,\s\d\d\:\d\d", h.text, re.IGNORECASE)
            match = re.findall("\d\d\d\d\-\d\d\-\d\d,\s\d\d\:\d\d", h.text,
                               re.IGNORECASE)
            if todaymatch:
                datelist.append(datetime.date.today())
                timelist.append(todaymatch[0][6:])
            elif yesterdaymatch:
                datelist.append(yesterday)
                timelist.append(yesterdaymatch[0][6:])
            elif match:
                datelist.append(match[0][:10])
                timelist.append(match[0][12:])

        # Get postbody
        for p in postsoup:
            postbody = re.sub(r"[\n\t]*", "", p.text)  # clean out tab, newlines
            bodylist.append(postbody)
        page += 1

        # Get replies
        for p in postsoup:
            match = re.findall("(?<=Ursprungligen postat av ).*", p.text,
                               re.IGNORECASE)
            if match:
                inreplylist.append(match[0])
            else:
                inreplylist.append("none")

        """
        Check if thread end is reached, dump to db, continue or stop
        """

        if len(postsoup) < 12:  # then it is the last page of the thread, dump and stop
            db = sqlite3.connect(db_name)
            cursor = db.cursor()
            for n in range(0, len(bodylist)):
                try:
                    cursor.execute('''
                    INSERT INTO fb(idnumber, user, date, time, body,
                                   inreply, title, path)
                    VALUES(?,?,?,?,?,?,?,?)''',
                                   (postidlist[n], userlist[n], datelist[n], timelist[n],
                                    bodylist[n], inreplylist[n], title, str(parseforumstructure(soup)))
                                   )
                    db.commit()
                except (IndexError, sqlite3.IntegrityError) as e:
                    pass
            break

        if len(postsoup) >= 12:  # it may still happen to be the last page, if page contains the exact last 12 posts
            if previouslyaddedpageposts == bodylist:  # if this page is identical to the previous, the last page was exactly 12 posts, so stop
                break
            else:  # otherwise it is a regular full page, so dump to db and continue
                db = sqlite3.connect(db_name)
                cursor = db.cursor()
                for n in range(0, len(bodylist)):
                    try:
                        cursor.execute('''
                        INSERT INTO fb(idnumber, user, date, time, body,
                                   inreply, title, path)
                        VALUES(?,?,?,?,?,?,?,?)''',
                                       (postidlist[n], userlist[n], datelist[n], timelist[n],
                                        bodylist[n], inreplylist[n], title, str(parseforumstructure(soup)))
                                       )
                        db.commit()
                    except (IndexError, sqlite3.IntegrityError) as e:
                        pass
                        previouslyaddedpageposts = bodylist

        with open("flbscrp.log", "a") as logfile:
            logfile.write("Done\n")


def get_subforum_threads(subforum_url):
    page = 1
    current_url = subforum_url + "p" + str(page)
    filename = subforum_url.split("/")[3]

    with open("flbscrp.log", "a") as logfile:
        logfile.write("Running get_subforum_threads()\n")

    with open(filename + "_topic_urls.txt", "w") as outfile:
        while True:
            headers = {'User-Agent': UserAgent().random}
            with open("flbscrp.log", "a") as logfile:
                logfile.write("Getting " + current_url + "\n")

            # r = requests.get(current_url, headers=headers) # to run without tor
            proxies = {'http': 'socks5://127.0.0.1:9050',
                       'https': 'socks5://127.0.0.1:9050'}  # to run with tor
            r = requests.get(current_url, proxies=proxies, headers=headers)  # to run with tor

            html = r.content
            soup = BeautifulSoup(html, "lxml")
            topics = soup.findAll('a', id=re.compile("thread_title_\d"))

            if len(topics) >= 50:

                with open("flbscrp.log", "a") as logfile:
                    logfile.write(str(len(topics)) + " threads\n")
                for t in topics:
                    threadurl = "https://flashback.org" + t.get("href")
                    outfile.write(threadurl + "\n")
                page += 1
                current_url = subforum_url + "p" + str(page)

            if len(topics) < 50:
                for t in topics:
                    threadurl = "https://flashback.org" + t.get("href")
                    outfile.write(threadurl + "\n")
                break
        with open("flbscrp.log", "a") as logfile:
            logfile.write("Done\n")


def createdatabase(projectname):
    try:
        db = sqlite3.connect(projectname + '.sqlite3')
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE fb(id INTEGER PRIMARY KEY, idnumber TEXT UNIQUE,\
            user TEXT, date TEXT, time TEXT, body TEXT, inreply TEXT,\
             title TEXT, path TEXT)
            ''')
        db.commit()
    except sqlite3.OperationalError:
        print("The file", projectname +
              ".sqlite3 already exists. Use a different name, or delete it.")


def parseforumstructure(soup):
    pathdiv = soup.find("div", class_="form-group")
    pathdata = pathdiv.findAll("option")
    pathlist = []
    for p in pathdata:
        if p.text != "Detta ämne":
            pathlist.append(p.text)
    return (pathlist)


def get_threads(file_with_urls, db_name):
    with open("flbscrp.log", "a") as logfile:
        logfile.write("Running get_threads()\n")

    with open(file_with_urls, "r") as urlfile:
        urls = urlfile.readlines()
    for c,url in enumerate(urls):
        url = url.strip("\n")
        with open("flbscrp.log", "a") as logfile:
            logfile.write("\n==== Thread " + str(c+1) + " --out of-- " + str(len(urls)) + "\n")
        try:
            get_thread(url, db_name, 1)
            pause = random.randint(2,7) # increase this if script crashes; (2,20) seems to avoid crashes, but must evaluate how low to go
            with open("flbscrp.log", "a") as logfile:
                logfile.write("Sleeping " + str(pause) + " sec ...\n")
            sleep(pause) # sleep a random number of seconds between 2 and 20
        except:
            with open("flbscrp.log", "a") as logfile:
                ("There was an error. Proceeding to next url. Check 'failed_urls.txt'\n")
            with open("failed_urls.txt", "a") as failfile:
                failfile.write(current_url + "\n")  # record failed urls
            continue

def rescrape_failed_threads(failfile, db_name):

    with open("flbscrp.log", "a") as logfile:
        logfile.write("Running rescrape_failed_threads()\n")

    with open(failfile, "r") as urlfile:
        urls = urlfile.readlines()
        os.rename(failfile, "old_" + failfile)
        for c,u in enumerate(urls):
            u = u.split("://")
            u = u[1].split("\n")[0]
            u = u.split("p")
            if len(u) < 2:
                startpage = 1
            else:
                startpage = u[1]
            url = "https://" + u[0]

            with open("flbscrp.log", "a") as logfile:
                logfile.write("\n==== Thread " + str(c+1) + "  --out of-- " + str(len(urls)) + "\n")

            try:
                get_thread(url, db_name, startpage)
                with open("flbscrp.log", "a") as logfile:
                    logfile.write("\n==== Rescraping " + url + " starting at page " + str(startpage) + "\n")
                pause = random.randint(2,7)
                with open("flbscrp.log", "a") as logfile:
                    logfile.write("Sleeping " + str(pause) + " sec ...\n")
                sleep(pause) # sleep a random number of seconds between 2 and 20
            except:
                with open("flbscrp.log", "a") as logfile:
                    ("There was an error. Proceeding to next url. Check 'failed_urls.txt'\n")
                with open("failed_urls.txt", "a") as failfile:
                    failfile.write(current_url + "\n")  # record failed urls
                continue
    with open("flbscrp.log", "a") as logfile:
        logfile.write("\nDone!")


def check_ip():
    headers = {'User-Agent': UserAgent().random}
    test_r = requests.get("https://api.ipify.org/?format=text", headers=headers)
    print("actual ip --> " + str(test_r.text) + "\n")


def check_tor():
    headers = {'User-Agent': UserAgent().random}
    proxies = {'http': 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'}
    test_r = requests.get("https://api.ipify.org/?format=text", proxies=proxies, headers=headers)
    print("tor ip -----> " + str(test_r.text) + "\n")

def sql2csv(filepath):
    conn = sqlite3.connect(filepath)
    df = pd.read_sql_query("SELECT * FROM fb", conn)
    print(str(len(df)) + " items")
    df.to_csv("data.csv", index = False)
