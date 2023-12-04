#!/bin/env python3

import argparse
import os.path
import sys

import requests


def main():
    parser = argparse.ArgumentParser('Downloads latest HRP file (by default port 443 can be changed with http flag')
    parser.add_argument('--http', action='store_true', help='Download port 80 HRPs')
    parser.add_argument('-o', '--output-dir', required=True, type=str, help='Output directory')
    args = parser.parse_args()

    port = 443 if not args.http else 80
    baseurl = f'https://github.com/hrp-stats/hrp-stats.github.io/tree/main/hrps/{port}'
    response = requests.get(baseurl)
    if response:
        responsej = response.json()
        items = [file['path'] for file in responsej['payload']['tree']['items'] if file['contentType'] == 'file']
        items.sort()
        print(f'Downloading {os.path.basename(items[-1])}')
        response = requests.get(f'https://github.com/hrp-stats/hrp-stats.github.io/raw/main/{items[-1]}')
        if response:
            with open(os.path.join(args.output_dir, os.path.basename(items[-1])), 'wb') as outfile:
                outfile.write(response.content)
        else:
            print('Error ocurred while downloading file via HTTP request', file=sys.stderr)
    else:
        print('Error ocurred while performing HTTP request', file=sys.stderr)


if __name__ == '__main__':
    main()
