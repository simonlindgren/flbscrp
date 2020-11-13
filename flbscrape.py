#!/usr/bin/env python3

"""
FLBSCRAPE
"""

import requests
import random
from bs4 import BeautifulSoup
import re
import sqlite3
import datetime


def get_thread(thread_url,db_name):
    user_agent_list = []
    page = 1
    current_url = thread_url + "p" + str(page)

    with open("user_agents.txt", "r") as uafile:
        agents = uafile.readlines()
        for a in agents:
            user_agent_list.append(a.strip("\n"))

    postidlist = []
    userlist = []
    datelist = []
    timelist = []
    bodylist = []
    inreplylist = []


    while True:
        user_agent = random.choice(user_agent_list)
        headers = {"User-Agent": user_agent}

        current_url = thread_url + "p" + str(page)
        print("Getting " + current_url)

        r = requests.get(current_url, headers=headers)
  
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
        print("---> Length of page: " + str(len(postsoup)) + " posts.")

        """
        Handle the problem with scraper stopping at 'moderator messages'
        """
        modsoup = soup.findAll("div", class_="panel panel-warning panel-form")
        try:
            titlediv = soup.find("div", class_="page-title")
            title = re.sub(r"[\n\t]*", "", titlediv.text)  # clean out tab, newlines
        except:
            title = "<error getting title>"  # if title extraction fails.
        print("---> Thread title:", title)


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
        page +=1

        # Get replies
        for p in postsoup:
            match = re.findall("(?<=Ursprungligen postat av ).*", p.text,
                               re.IGNORECASE)
            if match:
                inreplylist.append(match[0])
            else:
                inreplylist.append("none")

        """
        Dump to database
        """

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

        if len(postsoup) < 12:
            break

    print("Done")

def get_subforum_threads(subforum_url):
    user_agent_list = []
    page = 1
    current_url = subforum_url + "p" + str(page)

    with open("user_agents.txt", "r") as uafile:
        agents = uafile.readlines()
        for a in agents:
            user_agent_list.append(a.strip("\n"))

    filename = subforum_url.split("/")[3]

    with open(filename + "_topic_urls.txt", "w") as outfile:
        while True:
            user_agent = random.choice(user_agent_list)
            headers = {"User-Agent": user_agent}

            print("Getting " + current_url)
            r = requests.get(current_url, headers=headers)
            html = r.content
            soup = BeautifulSoup(html, "lxml")
            topics = soup.findAll('a', id=re.compile("thread_title_\d"))

            if len(topics) >= 50:

                print(str(len(topics)) + " threads")
                for t in topics:
                    threadurl = "https://flashback.org" + t.get("href")
                    outfile.write(threadurl + "\n")
                page+=1
                current_url = subforum_url + "p" + str(page)

            if len(topics) < 50:
                for t in topics:
                    threadurl = "https://flashback.org" + t.get("href")
                    outfile.write(threadurl + "\n")
                break
        print("Done")

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




def get_threads(file_with_urls,db_name):
    with open(file_with_urls, "r") as urlfile:
        urls = urlfile.readlines()
    for url in urls:
        url = url.strip("\n")
        get_thread(url, db_name)
