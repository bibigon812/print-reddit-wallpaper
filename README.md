# Print Reddit Wallpaper

This scrip

* downloads a random wallpaper from reddit
* prints the donwloaded wallpaper using `lp`

``` text
usage: print-reddit-wallpaper.py [-h] [-d BASE_DIR] [-l LOG_LEVEL] [-p] [-s]

options:
  -h, --help            show this help message and exit
  -d BASE_DIR, --base-dir BASE_DIR
                        Working directory [${HOME}/print]
  -l LOG_LEVEL, --log-level LOG_LEVEL
                        Logging level (info|warning|error) [info]
  -p, --purge           Purge downloaded wallpaper
  -s, --skip-print      Skip printing
```
