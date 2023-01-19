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
WAIT = 2

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--base-dir', type=str, help='Working directory [${HOME}/print]')
parser.add_argument('-l', '--log-level', type=str, help='Logging level (info|warning|error) [info]')
parser.add_argument('-p', '--purge', action='store_true', help='Purge downloaded wallpaper')
parser.add_argument('-s', '--skip-print', action='store_true', help='Skip printing')
parser.add_argument('-m', '--memes', action='store_true', help='Using memes instead of wallpapers')
args = parser.parse_args()

if args.base_dir:
    base_dir = args.base_dir
else:
    base_dir = os.path.join(os.getenv('HOME'), 'print')

if not os.path.isdir(base_dir):
    os.mkdir(base_dir)

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

if args.memes:
    CONTENT = 'meme'
else:
    CONTENT = 'wallpaper'

API_URL = f'https://www.reddit.com/r/{CONTENT}s.json?limit={LIMIT}'

content_dir = os.path.join(base_dir, f'{CONTENT}s')
if not os.path.isdir(content_dir):
    os.mkdir(content_dir)

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(log_level)

cache_file = os.path.join(base_dir, 'cache', f'{CONTENT}s.json')

content_json = None

# Using cache
if os.path.isfile(cache_file) and os.path.getctime(cache_file) >= datetime.timestamp(datetime.now() - timedelta(hours=1)):
    logger.info('using cache')
    with open(cache_file) as f:
        content_json = json.load(f)
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

        content_json = r.json()
        with open(cache_file, 'w') as f:
            json.dump(content_json, f)

    else:

        logger.error(f'reddit {CONTENT} api failed')
        logger.error(json.dumps(r.json()))
        os._exit(1)

content_url = None

# Get rundom content url
if content_json is not None:
    logger.info(f'get random {CONTENT} url')
    while True:
        num = int(random.random() * (LIMIT - 1))
        data = content_json['data']['children'][num]['data']

        if 'is_video' in data and data['is_video']:
            continue
        if 'is_gallery' in data and data['is_gallery']:
            continue
        if data['url'].endswith('/'):
            continue

        content_url = data['url']
        break

# Download image
if content_url is not None:

    content_filename = os.path.basename(urlparse(content_url).path)

    logger.info(f'download {CONTENT} {content_url}')
    r = requests.get(content_url, stream=True)

    if r.status_code == 200:
        content_path = os.path.join(content_dir, content_filename)
        r.raw.decode_content = True

        logger.info(f'save {CONTENT} {content_path}')
        with open(content_path, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

        if not skip_print:
            logger.info(f'print {CONTENT} {content_path}')
            subprocess.run(['lp', content_path], stdout=subprocess.PIPE, universal_newlines=True)
        else:
            logger.info(f'skip printing {CONTENT} {content_path}')

        if purge:
            logger.info(f'remove {CONTENT} {content_path}')
            os.remove(content_path)

    else:
        logger.error(f'{CONTENT} downloading failed')
