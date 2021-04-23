import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import pickle
from utils import get_logger
from packages.hashes.simhash import simhash

''' Report Questions

    1) How many unique pages did you find? Uniqueness for the purposes of this assignment
        is ONLY established by the URL, but discarding the fragment part. So, for example,
        http://www.ics.uci.edu#aaa and http://www.ics.uci.edu#bbb are the same URL. Even if
        you implement additional methods for textual similarity detection, please keep considering
        the above definition of unique pages for the purposes of counting the unique pages in this assignment.

    2) What is the longest page in terms of the number of words? (HTML markup doesn’t count as words)

    3) What are the 50 most common words in the entire set of pages crawled under these domains?
        (Ignore English stop words, which can be found, for example, here (Links to an external site.))
        Submit the list of common words ordered by frequency.

    4) How many subdomains did you find in the ics.uci.edu domain?
        Submit the list of subdomains ordered alphabetically and the number of unique pages detected in each subdomain.
        The content of this list should be lines containing URL, number, for example:
        http://vision.ics.uci.edu, 10 (not the actual number here)

'''

# replace this with a flag which mark the end of the crawlling
save_frequency = 0

# set of explored pages
explored_urls = dict()  # key is the url, value is the simhash value

# for question (2)
# list to store the longest page, first element is url and second is the length
longest_page = ["", 0]

# set of unique urls
found_urls = set()

# for question (3)
found_words = {}  # key is the words, and the value is the number of occurrence

# for question (4)
found_subdomains = {}  # key is the subdomain, and the value is the number of pages

# logger for our scraper
logger = get_logger("SCRAPER")
processing_logger = get_logger("PROCESSING")


def scraper(url, resp):
    global save_frequency
    print("\nInitializing scapper.")
    logger.info(f"Scraping {url}")

    # if the url ends with a /, remove the / then added it to explored_urls
    # if(url[-1] == "/"):
    #     explored_urls[url[:-1]] = 0
    #     # explored_urls.add(url[:-1])
    #     found_urls.add(url[:-1])
    # else:
    #     explored_urls[url] = 0
    #     # explored_urls.add(url)
    #     found_urls.add(url)
    explored_urls[url] = simhash("")  # default simhash to 0
    found_urls.add(url)

    links = extract_next_links(url, resp)
    # process the links without schemes
    valid_links = [link for link in links if is_valid(link)]

    # #add all the valid lings into found_urls
    for link in valid_links:
        found_urls.add(link)

    if (save_frequency == 100):
        save_frequency = 0
        save_results()
    save_frequency += 1

    ##for Problem#4 !!!Currently doesn't check for unique pages!!!
    # Checking only in the ICS domain
    split_url = url.split(".", 3)
    if (split_url[1] == "ics"):
        # splitting url for subdomain comparison
        currentSubdomain = split_url[0] + ".ics.uci.edu"

        # Checking if the subdomain is new or not, and incrementing it accordingly
        # I deleted the check for https://www part, since the process function
        # has already add https or domains to the beginning of every url
        if (found_subdomains.get(currentSubdomain) == None):
            found_subdomains[currentSubdomain] = 1
        else:
            found_subdomains[currentSubdomain] += 1
        # Sorting the found subdomains by alphabetical order, and setting their keys to the value found
        sorted_subdomains = {}
        sorted_subdomains = sorted(found_subdomains.items(), key=lambda x: x[0], reverse=False)
        for subdomain in sorted_subdomains:
            # printing out in format "https://www.stat.uci.edu , 1"
            print(subdomain[0], ",", subdomain[1])

    # print(f"\nThe longest page is {longest_page[0]}: {longest_page[1]}")
    # print("--VALID LINKS--",len(valid_links), valid_links) #may contain duplicates
    logger.info(f"{len(set(valid_links))} valid links found")
    # print("--TOTAL FOUND URLS--", len(found_urls), found_urls) #the total set of urls found
    logger.info(f"total of {len(found_urls)} urls found")
    # print("--EXPLORED URLS--", explored_urls)
    logger.info(f"{len(explored_urls)} urls explored")

    # Commented line below for testing purposes
    # return [link for link in links if is_valid(link)]
    set_valid_links = set(valid_links)  # this is to remove duplicate valid_links extracted from the url
    # turn it back into a list
    return list(set_valid_links)


def extract_next_links(url, resp):
    links_list = []
    print("Extracting links from", url)

    if is_valid_status(resp):
        # parse resp.raw_response (could use beautifulsoup)
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')

        # Any file with text shorter than 800 will be omitted due to lacking valued content
        if (len(soup.get_text()) <= 800):
            return list()

        # for question 3
        duplicate_flag = extract_text(soup, url)

        # if a duplicate was detected we don't extract links
        if not duplicate_flag:
            return list()

        # Extract all urls
        # This also might be the area to get all the info for our report
        for link in soup.find_all('a'):
            if link.get('href'):
                defragged_link = link.get('href').split('#')[0]
                if defragged_link:
                    links_list.append(defragged_link)
            # print(defragged_link)
            # print(link.get('href'))
        # completed extraction of links now we process them
        return process_links(url, links_list)

    return links_list


# process links that have no schemes.
# links that start with 1 slash need the domain concatenated
# links with 2 slashes can have https: added to the front
def process_links(url: str, links: list) -> list:
    processing_logger.info(f"Processing extracted links from {url}")
    new_list = list()
    for link in links:
        if link[:2] == "//":
            https_link = "https:" + link
            processing_logger.info(f"ADDING HTTPS: {link} => {https_link}")
            new_list.append(https_link)
        elif link[:1] == "/":
            url_link = url + link
            processing_logger.info(f"ADDING DOMAIN {link} => {url_link}")
            new_list.append(url_link)
        else:
            new_list.append(link)
    return new_list


## This function add words to the dict found_words
## For question 3
# returns false if there is a nearly identical simhash that exists otherwise true
def extract_text(soup, url) -> bool:
    # stopwords is a file which contains all words that should be ignored
    # add stopword, if found some words should be ignored during tests

    stopwords = []
    with open('stopwords.txt') as f:
        stopwords = f.read().split()

    # re to extract text; can be replaced with a more powerful tokenizer
    # regex no accepts words with apostrophes in them
    text = re.findall(r'[a-zA-Z0-9][\'-.@\/:a-zA-Z0-9]+[a-zA-Z0-9]', soup.get_text())

    # checking current hash vs explore_urls hash
    hash = simhash(text)
    # logger.info(f"{hash} = simhash for {url}")

    for explored_url, url_simhash in explored_urls.items():
        # logger.info(f"COMPARING SIMHASH: {hash.similarity(url_simhash)}")
        if hash.similarity(url_simhash) > 0.90:
            logger.warning(f"DUPLICATE FOUND: {url} & {explored_url}")
            return False

    explored_urls[url] = simhash(text)

    # for question 2
    if (len(text) > longest_page[1]):
        longest_page[0] = url
        longest_page[1] = len(text)

    for word in text:
        word = word.lower()
        if (word not in stopwords):
            if (found_words.get(word) != None):
                found_words[word] += 1
            else:
                found_words[word] = 1

    return True


# write results to text files
def save_results():
    urls_file = open("found_urls.txt", "w+")
    words_file = open("common_words.txt", "w+")
    longest_page_file = open("longest_page.txt", "w+")
    domains_file = open("domains.txt", "w+")

    urls_file.write("Total url: " + str(len(found_urls)))
    longest_page_file.write(str(longest_page))

    # sort the found_words dict
    keys_sorted_value = sorted(found_words, key=found_words.get, reverse=True)
    sorted_dict = {}
    count = 0
    for k in keys_sorted_value:
        if (count == 50):
            break
        sorted_dict[k] = found_words[k]
        words_file.write(k + ': ' + str(sorted_dict[k]) + '\n')
        count += 1

    for word in found_subdomains:
        domains_file.write(str(word) + ': ' + str(found_subdomains[word]) + '\n')


# valid status codes are from 200-399, and 204 means no content
def is_valid_status(resp):
    if (resp.status < 200 or resp.status >= 400 or resp.status == 204):
        print("INVALID STATUS:", resp.status, resp.url)
        logger.warning(f"INVALID STATUS: <{resp.status}> from {resp.url}")
        return False
    elif (resp.status != 200):
        print("VALID non-200 STATUS:", resp.status, resp.url)
        logger.info(f"NON-200 STATUS <{resp.status}> from {resp.url}")
        return True
    else:
        return True


# TODO: implement methods that invalidated pages that are listed in crawler behavior requirements
# Detect and avoid infinite traps
# Detect and avoid crawling very large files, especially if they have low information value
def is_valid(url):
    # valid domains for the purpose of this assignment
    valid_urls = set(["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu",
                      "today.uci.edu/department/information_computer_sciences"])
    try:
        parsed = urlparse(url)

        if parsed.scheme not in set(["http", "https"]):
            logger.warning(f"INCORRECT SCHEME: {url} - parsed.scheme = {parsed.scheme}")
            return False
        # check if the url is in one of the given domain
        for valid_url in valid_urls:
            if valid_url in url:
                # if the url has already been explored, it is no longer valid
                # NOTE: this method of checking urls could be replaced with string matching (something i found was fuzzywuzzy)
                # FuzzyWuzzy has methods that calculates the similarities between two strings and returns a percentage
                if (url[:-1] if (url[-1] == "/") else url) in explored_urls:
                    print("ALREADY EXPLORED", url)
                    logger.info(f"ALREADY EXPLORED: {url}")
                    return False
                else:
                    # checking explored urls' simhash
                    # print("CORRECT Domain:",url)
                    # if the url is in given domain, return if it is a valid url or not
                    if re.match(
                            r".*\.(css|js|bmp|gif|jpe?g|ico"
                            + r"|png|tiff?|mid|mp2|mp3|mp4"
                            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
                            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
                            + r"|epub|dll|cnf|tgz|sha1"
                            + r"|thmx|mso|arff|rtf|jar|csv"
                            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|calendar)$", parsed.path.lower()):
                        logger.warning(f"INVALID PATH: {url} - parsed.path {parsed.path}")
                        return False
                    else:
                        return True
                    # return not re.match(
                    #     r".*\.(css|js|bmp|gif|jpe?g|ico"
                    #     + r"|png|tiff?|mid|mp2|mp3|mp4"
                    #     + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                    #     + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
                    #     + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
                    #     + r"|epub|dll|cnf|tgz|sha1"
                    #     + r"|thmx|mso|arff|rtf|jar|csv"
                    #     + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print("TypeError for ", parsed)
        logger.error(f"TypeError for {parsed}")
        raise
