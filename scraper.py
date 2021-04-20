import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import pickle
from utils import get_logger

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

#TODO: change into a set, and change method if inserting
#set of explored pages
explored_urls = set()

#for question (2)
#list to store the longest page, first element is url and second is the length
longest_page = ["", 0]

#TODO: for question (1) add set for all unique urls found (use .split('#')[0] it remove fragment part)
#set of unique urls
found_urls = set()

#TODO: add dictionary of words scrapped from sites
#for question (3)
found_words = {} #key is the words, and the value is the number of occurrence

#TODO: add dictionary to keep track of ics.uci.edu subdomains
#for question (4)
found_subdomains = {} #key is the subdomain, and the value is the number of pages

#logger for our scraper
logger = get_logger("SCRAPER")

def scraper(url, resp):
    print("\nInitializing scapper.")
    logger.info(f"Scraping {url}")

    #if the url ends with a /, remove the / then added it to explored_urls
    if(url[-1] == "/"):
        explored_urls.add(url[:-1])
        found_urls.add(url[:-1])
    else:
        explored_urls.add(url)
        found_urls.add(url)

    links = extract_next_links(url, resp)
    valid_links = [link for link in links if is_valid(link)]

    # #add all the valid lings into found_urls
    for link in valid_links:
        found_urls.add(link)
        
    #sort the found_words dict
    keys_sorted_value = sorted(found_words, key=found_words.get, reverse=True)
    sorted_dict = {}
    for k in keys_sorted_value:
        sorted_dict[k] = found_words[k]
        #print statement for the word dictionary
        print(f"{k}: {sorted_dict[k]}")

    #print statement for the word dictionary (moved printing into the sorting part above)
    # for word in found_words:
    #     print(f"{word}: {found_words[word]}")

    print(f"\nThe longest page is {longest_page[0]}: {longest_page[1]}")
    #print("--VALID LINKS--",len(valid_links), valid_links) #may contain duplicates
    logger.info(f"{len(set(valid_links))} valid links found")
    #print("--TOTAL FOUND URLS--", len(found_urls), found_urls) #the total set of urls found
    logger.info(f"total of {len(found_urls)} urls found")
    #print("--EXPLORED URLS--", explored_urls)
    logger.info(f"{len(explored_urls)} urls explored")

    #Commented line below for testing purposes
    #return [link for link in links if is_valid(link)]
    return list() #TODO: return the actual list of exracted urls

def extract_next_links(url, resp):
    links_list = []
    print("Extracting links from",url)
    # Implementation requred.
    #TODO: Check resp.status codes
    if is_valid_status(resp):
        #parse resp.raw_response (could use beautifulsoup)
        soup = BeautifulSoup(resp.raw_response.content,'html.parser')

        #for question 2, and no words are ignored here
        if(len(soup.get_text())>longest_page[1]):
            longest_page[0] = url
            longest_page[1] = len(soup.get_text())

        #for question 3
        extract_text(soup)
        #Extract all urls
        #This also might be the area to get all the info for our report
        for link in soup.find_all('a'):
            defragged_link = link.get('href').split('#')[0]
            if defragged_link:
                links_list.append(defragged_link)
            #print(defragged_link)
            #print(link.get('href'))
    
    return links_list


## This function add words to the dict found_words
## For question 3
def extract_text(soup):
    #stopwords is a file which contains all words that should be ignored
    #add stopword, if found some words should be ignored during tests

    stopwords = []
    with open('stopwords.txt') as f:
        stopwords = f.read().split()
    
    #re to extract text; can be replaced with a more powerful tokenizer
    #regex no accepts words with apostrophes in them
    text = re.findall(r"[a-zA-Z0-9-.@\/:]+[a-zA-Z0-9']+", soup.get_text())

    for word in text:
        word = word.lower()
        if (word not in stopwords) and len(word) >2:
            if(found_words.get(word) != None):
                found_words[word] += 1
            else:
                found_words[word] = 1
            


# valid status codes are from 200-399, and 204 means no content
def is_valid_status(resp):
    if(resp.status < 200 or resp.status >= 400 or resp.status == 204):
        print("INVALID STATUS:",resp.status,resp.url)
        logger.warning(f"{resp.url} returned INVALID status code: {resp.status}")
        return False
    elif(resp.status != 200):
        print("VALID non-200 STATUS:",resp.status,resp.url)
        logger.info(f"{resp.url} returned VALID NON-200 status code: {resp.status}")
        return True
    else:
        return True

#TODO: implement methods that invalidated pages that are listed in crawler behavior requirements
# Detect and avoid infinite traps
# Detect and avoid sets of similar pages with no information
# Detect and avoid dead URLs that return a 200 status but no data (click here to see what the different HTTP status codes mean (Links to an external site.))
# Detect and avoid crawling very large files, especially if they have low information value
def is_valid(url):
    #valid domains for the purpose of this assignment
    valid_urls = set(["ics.uci.edu","cs.uci.edu","informatics.uci.edu","stat.uci.edu","today.uci.edu/department/information_computer_sciences"])
    try:
        parsed = urlparse(url)
        
        if parsed.scheme not in set(["http", "https"]):
            logger.warning(f"INCORRECT SCHEME: {url} - parsed.scheme = {parsed.scheme}")
            return False
        #check if the url is in one of the given domain
        for valid_url in valid_urls:
            if valid_url in url:
                #if the url has already been explored, it is no longer valid
                #NOTE: this method of checking urls could be replaced with string matching (something i found was fuzzywuzzy)
                #FuzzyWuzzy has methods that calculates the similarities between two strings and returns a percentage
                if (url[:-1] if (url[-1] == "/") else url) in explored_urls:
                    print("ALREADY EXPLORED", url)
                    logger.info(f"ALREADY EXPLORED: {url}")
                    return False
                else:
                    # print("CORRECT Domain:",url)
                    #if the url is in given domain, return if it is a valid url or not
                    if re.match(
                        r".*\.(css|js|bmp|gif|jpe?g|ico"
                        + r"|png|tiff?|mid|mp2|mp3|mp4"
                        + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                        + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
                        + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
                        + r"|epub|dll|cnf|tgz|sha1"
                        + r"|thmx|mso|arff|rtf|jar|csv"
                        + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
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
        print ("TypeError for ", parsed)
        logger.error(f"TypeError for {parsed}")
        raise