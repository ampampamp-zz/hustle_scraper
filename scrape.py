"""
This script scrapes URLs for phone numbers.
"""
import argparse
import csv
import logging
import re
import time

#TODO(amp): implement me!
from multiprocessing.pool import ThreadPool

import requests
from bs4 import BeautifulSoup

PHONE_NUMBER_PATTERNS = (
    re.compile('[1]?\s*?\(\d{3}\)\s*?\d{3}\s*?-\s*?\d{4}'),
    #TODO(amp): validate these patterns
    #re.compile('\+?[1]?\d{10}'),
    #re.compile('(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'),
    #re.compile('(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})'),
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-urls_file_path',
        '--urls_file_path',
        help='Uses URLs found in a file',
    )
    parser.add_argument(
        '-seed_urls',
        '--seed_urls',
        nargs='*',
        help='URL to start (seed) the list of URLs to scrape',
    )
    parser.add_argument(
        '-t',
        '--test',
        action='store_true',
        help='Does not store, only prints results',
    )
    parser.add_argument(
        '--timeout',
        default=10,
        type=int,
        help='Default page response timeout in seconds',
    )
    parser.add_argument(
        '--page_link_limit',
        type=int,
        help='Number of links to limit link scraping to',
    )
    parser.add_argument(
        '--total_scrape_time',
        default=3600,
        type=int,
        help='Number of seconds to scrape for',
    )
    parser.add_argument(
        '--max_links',
        default=100,
        type=int,
        help='Max number of links to scrape'
    )
    return parser.parse_args()


def get_urls_from_file(path):
    urls = set()
    with open(path) as f:
        for line in f:
            urls.add(line.strip())
    return urls


def is_url(url):
    return url.startswith('http')


def get_url_response_text(url, **kwargs):
    response = requests.get(url, **kwargs)
    response.raise_for_status()
    return response.text


def clean_phone_number(number):
    """
    Cleans a phone number into an integer.

    :param str number: raw phone number text
    :return int: cleaned phone number
    """
    return int(''.join(char for char in number.strip() if char.isdigit()))


def extract_phone_numbers(text):
    """
    Finds and cleans phone numbers in raw text.

    :param str text: raw text to search
    :return set numbers: set of cleaned phone numbers
    """
    numbers = set()
    for pattern in PHONE_NUMBER_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            for match in matches:
                numbers.add(clean_phone_number(match))
    return numbers


def extract_links(text, limit=None):
    """
    Extracts links from page text.
    
    :param str text: raw text to search
    :param int limit: number of links to limit extaction to
    :return set links: links from page
    """
    soup = BeautifulSoup(text, 'lxml')

    links = set()
    for tag in soup.find_all('a'):
        link = tag.get('href')
        if link and is_url(link):
            links.add(link)
            
        if limit and len(links) == limit:
            break

    return links


def write_phone_numbers(numbers):
    with open('phone_numbers.csv', mode='w') as f:
        writer = csv.writer(f, delimiter=',')
        for mapping in numbers.items():
            writer.writerow(mapping)


def main():
    args = parse_args()

    if args.seed_urls:
        urls = set(args.seed_urls)
    elif args.urls_file_path:
        urls = get_urls_from_file(args.urls_file_path)
    else: 
        raise RuntimeError('Must specify either --seed_urls or --urls_file_path!')

    if args.max_links and len(urls) > args.max_links:
        add_new_links = False
    else:
        add_new_links = True

    #TODO(amp):make logging work!
    logger = logging.getLogger()
    logger.setLevel('INFO')
    logger.info('Starting to process %s URL(s)', len(urls))

    phone_numbers = {}
    now = time.time()
    while urls and time.time() < now + args.total_scrape_time:
        url = urls.pop()

        if not is_url(url):
            logger.warning('%s is not a valid URL, must supply HTTP schema', url)
            continue

	logger.info('Scraping %s', url)
        try:
            url_text = get_url_response_text(url, timeout=args.timeout)
        except Exception as exc:
            logger.error('Encountered error getting response txt from %s', url)
            logger.error(repr(exc))
            continue

        numbers = extract_phone_numbers(url_text)
        logger.info('Found %s phone number(s)', len(numbers))
        for number in numbers:
            phone_numbers[number] = url

	if add_new_links:
            links = extract_links(url_text, limit=args.page_link_limit)
            urls.update(links)

	if args.max_links and len(urls) > args.max_links:
            add_new_links = False

    if not args.test:
        write_phone_numbers(phone_numbers)
    else:
        logging.info(phone_numbers)


if __name__ == '__main__':
    main()

