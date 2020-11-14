# flbscrp

A simplified version of [github.com/christopherkullenberg/fl\*shb\*ckscr\*per](https://github.com/christopherkullenberg/flashbackscraper).

*Note:* Use responsibly with regards to network usage and potential privacy aspects.

### Setup
```
$ git clone <this repo>
$ cd flbscrp
$ python3

>>> import flbscrp
```
### Get subforum urls
```
>>> flbscrp.get_subforum_threads("https://www.fl*shb*ck.org/f***")
```
Saves url list to *txt.

### Create db to store data
```
>>> flbscrp.createdatabase("my_data")
```
Creates empty *sqlite3.

### Get one thread
```
>>>> flbscrape.get_thread("https://www.fl*shb*ck.org/t******", "my_data.sqlite3")
```
Populates the db with thread data.

### Get threads from file with urls
```
>>> flbscrp.get_threads("f***_topic_urls.txt", "my_data.sqlite3")
```
Populates the db with data from threads in file.

### db to csv

```
>>> flbscrp.db_to_csv("my_data.sqlite3")
```

Saves db contents to *csv.

