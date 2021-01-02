# flbscrp

A version of [github.com/christopherkullenberg/fl\*shb\*ckscr\*per](https://github.com/christopherkullenberg/flashbackscraper).

*Note:* Use responsibly with regards to network usage and potential privacy aspects.

### Setup
```
$ git clone <this repo>
$ cd flbscrp
$ python3

>>> import flbscrp
```
### Check tor
```
>>> flbscrp.check_ip()
>>> flbscrp.check_tor()
```

### Get subforum urls
```
>>> flbscrp.get_subforum_threads("https://www.fl*shb*ck.org/f***")
```
Saves url list to \*txt.

### Create db to store data
```
>>> flbscrp.createdatabase("my_data")
```
Creates empty \*sqlite3.

### Get one thread
```
>>> flbscrp.get_thread("https://www.fl*shb*ck.org/t******", "my_data.sqlite3")
```
Populates the db with thread data.

### Get threads from file with urls
```
>>> flbscrp.get_threads("f***_topic_urls.txt", "my_data.sqlite3")
```
Populates the db with data from threads in file.

### Logfile

While jobs are running, inspect the logfile by e.g:

```
$ tail flbscrp.log
```

See the progress of `get_threads()` by:

```
$ cat flbscrp.log | grep " --out of-- "
```

### Failed urls

URLs that could not be scraped will be saved to `failed_urls.txt`.

Use `rescrape_failed_threads()` to try to rescrape the full threads in which any page failed in the previous run:

```
>>> flbscp.rescrape_failed_threads("failed_urls.txt", "my_data.sqlite3")
```

The above will also rename `failed_urls.txt` to `_failed_urls.txt`. If no new `failed_urls.txt` is created, the rescrape was completely successful. Otherwise iterate.


### Convert database to csv

```
>>> flbscrp.sql2csv("my_data.sqlite3")
```
Creates `data.csv`.
