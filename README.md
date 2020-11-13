# flbscrp

A simplified version of [github.com/christopherkullenberg/fl\*shb\*ckscr\*per](https://github.com/christopherkullenberg/flashbackscraper).

#### Setup
```
$ git clone <this repo>
$ cd flbscrp
$ python3

>>> import flbscrp
```
#### Get subforum urls
```
>>> flbscrp.get_subforum_threads("https://www.fl*shb*ck.org/f***")
```
Saves url list to *txt.

#### Create db to store data
```
>>> flbscrp.createdatabase("my_data")
```
Creates empty *sqlite3.
