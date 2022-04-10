from pathlib import Path
import time
from os.path import getsize
import hashlib
import argparse
import logging 

files = {}

parser = argparse.ArgumentParser()
parser.add_argument('-l', '--minimum-size', help='Minimum size in bytes to look for. Defaults to 1024', default=1024, type=int)
parser.add_argument('-u', '--maximum-size', help='Maximum size in bytes to look for. Defaults to ', default=None, type=int)
parser.add_argument('-p', '--path', help='Where to look for duplicatas, defaults to current working directory.', default='.')
parser.add_argument('-c', '--comparison-type', help=' current working directory.', choices=['name_and_hash', 'name_and_size'], default='name_and_size')
parser.add_argument('-d', '--debug', help='', default=False, action='store_true')
arguments = parser.parse_args()

def human_readable_size(size_in_bytes: int):
    if size_in_bytes >= 1024*1024*1024:
        return f'{size_in_bytes / (1024*1024*1024):.2f} Gigabytes'
    elif size_in_bytes >= 1024*1024:
        return f'{size_in_bytes / (1024*1024):.2f} Megabytes'
    elif size_in_bytes >= 1024:
        return f'{size_in_bytes / 1024:.2f} Kilobytes'
    else:
        return f'{size_in_bytes} bytes'

logger = logging.getLogger(__name__)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s')
stream_handler.setFormatter(formatter)

logger.addHandler(stream_handler)
logger.setLevel(logging.INFO if not arguments.debug else logging.DEBUG)


t = time.time()
files_processed = 0
files_seen = 0
bytes_processed = 0


for p in Path(arguments.path).rglob('*'):
    if not p.is_file():
        continue

    files_seen += 1
    fullpath = p.absolute()

    size = getsize(fullpath)
    if size < arguments.minimum_size or (arguments.maximum_size and size > arguments.maximum_size):
        continue

    if arguments.comparison_type == 'name_and_size':
        key = f'{p.name}:{size}'
            
    elif arguments.comparison_type == 'name_and_hash':
        h = hashlib.md5()
        try:
            with open(fullpath, 'rb') as f:
                while True:
                    chunk = f.read(1024*1024)
                    if not chunk:
                        break

                    bytes_processed += len(chunk)

                    h.update(chunk)
        except:
            continue
        hash = h.hexdigest()
        hash = str(size)
        key = f'{p.name}:{hash}'

    if key not in files:
        files[key] = []
    files[key].append(str(fullpath))

    files_processed += 1

    if files_processed % 1000 == 0:
        logger.debug(f'Have processed {files_processed} files so far.')

execution_time = time.time() - t
logger.debug(f'Processed {files_processed} (out of {files_seen} number of files seen) in {execution_time:.2f} seconds! {((bytes_processed / (1024*1024)) * 8) / execution_time:.2f} Mbit/s')

for k, v in {k:v for k,v in files.items() if len(files[k]) > 1}.items():
    size = int(k.split(':')[1])

    logger.info(f'Found match of potential duplicate! Size: {human_readable_size(size)}')
    print('\n'.join(v))
    print('')
    print('')