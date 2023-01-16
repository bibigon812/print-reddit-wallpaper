#!/usr/bin/env python

import argparse
import json
import logging
import os
import random
import requests
import shutil
import subprocess
import time
from urllib.parse import urlparse
from datetime import datetime
from datetime import timedelta

LIMIT = 100
API_URL = f'https://www.reddit.com/r/wallpapers.json?limit={LIMIT}'
BASE_DIR = '/opt/print'
WAIT = 2

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--base-dir', type=str, help='Working directory [/opt/print]')
parser.add_argument('-l', '--log-level', type=str, help='Logging level (info|warning|error) [info]')
parser.add_argument('-p', '--purge', action='store_true', help='Purge downloaded wallpaper')
parser.add_argument('-s', '--skip-print', action='store_true', help='Skip printing')
args = parser.parse_args()

if args.base_dir:
    base_dir = args.base_dir
else:
    base_dir = BASE_DIR

if not os.path.isdir(base_dir):
    os.mkdir(base_dir)

wallpaper_dir = os.path.join(base_dir, 'wallpappers')
if not os.path.isdir(wallpaper_dir):
    os.mkdir(wallpaper_dir)

purge = args.purge
skip_print = args.skip_print

log_levels = {
    'debug':    logging.DEBUG,
    'info':     logging.INFO,
    'werning':  logging.WARNING,
    'error':    logging.ERROR,
    'critical': logging.CRITICAL,
}

if args.log_level in log_levels.keys():
    log_level = log_levels[args.log_level]
else:
    log_level = logging.INFO

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(log_level)

cache_file = os.path.join(base_dir, 'cache', 'wallpapers.json')

wallpapers_json = None

# Using cache
if os.path.isfile(cache_file) and os.path.getctime(cache_file) >= datetime.timestamp(datetime.now() - timedelta(hours=1)):
    logger.info('using cache')
    with open(cache_file) as f:
        wallpapers_json = json.load(f)
else:
    logger.warning("cache is stale or not found")

    r = None

    # handle "too many requests"
    while True:
        r = requests.get(API_URL)
        if r.status_code == 429:
            logger.warning(f'too many requests, sleeping {WAIT} seconds')
            time.sleep(WAIT);
        else:
            break

    if r.ok:

        if not os.path.isdir(os.path.dirname(cache_file)):
            os.mkdir(os.path.dirname(cache_file))

        wallpapers_json = r.json()
        with open(cache_file, 'w') as f:
            json.dump(wallpapers_json, f)

    else:

        logger.error('reddit wallpapers api failed')
        logger.error(json.dumps(r.json()))
        os._exit(1)

wallpaper_url = None

# Get rundom wallpaper url
if wallpapers_json is not None:
    logger.info('get random wallpaper url')
    while True:
        num = int(random.random() * (LIMIT - 1))
        data = wallpapers_json['data']['children'][num]['data']

        if 'is_video' in data and data['is_video']:
            continue
        if 'is_gallery' in data and data['is_gallery']:
            continue
        if data['url'].endswith('/'):
            continue

        wallpaper_url = data['url']
        break

# Download image
if wallpaper_url is not None:

    wallpaper_filename = os.path.basename(urlparse(wallpaper_url).path)

    logger.info(f'download wallpaper {wallpaper_url}')
    r = requests.get(wallpaper_url, stream=True)

    if r.status_code == 200:
        wallpaper_path = os.path.join(wallpaper_dir, wallpaper_filename)
        r.raw.decode_content = True

        logger.info(f'save wallpaper {wallpaper_path}')
        with open(wallpaper_path, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

        if not skip_print:
            logger.info(f'print wallpaper {wallpaper_path}')
            subprocess.run(['lp', wallpaper_path], stdout=subprocess.PIPE, universal_newlines=True)
        else:
            logger.info(f'skip printing wallpaper {wallpaper_path}')

        if purge:
            logger.info(f'remove wallpapper {wallpaper_path}')
            os.remove(wallpaper_path)

    else:
        logger.error('wallpaper downloading failed')
