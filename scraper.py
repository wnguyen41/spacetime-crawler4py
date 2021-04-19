import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import pickle

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
#list of explored pages
explored_urls = list()

#for question (2)
#list to store the longest page, first element is url and second is the length
max_page = ["", 0]

#TODO: for question (1) add set for all unique urls found (use .split('#')[0] it remove fragment part)

#TODO: add dictionary of words scrapped from sites
#for question (3)
explored_words = {} #key is the words, and the value is the number of occurrence

#TODO: add dictionary to keep track of ics.uci.edu subdomains
#for question (4)
explored_subdomains = {} #key is the subdomain, and the value is the number of pages

def scraper(url, resp):
    print("Initializing scapper.")

    #if the url ends with a /, remove the / then added it to explored_urls
    if(url[-1] == "/"):
        explored_urls.append(url[:-1])
    else:
        explored_urls.append(url)

    links = extract_next_links(url, resp)
    print([link for link in links if is_valid(link)])

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
        #Extract all urls
        #This also might be the area to get all the info for our report
        for link in soup.find_all('a'):
            link = (link.get('href').split('#'))[0]
            links_list.append(link)
            #print(link.get('href'))
    else:
        #If resp.status is between [200-599] response is in resp.raw_response
        #If resp.status is [600-606] reason for error is in resp.error
        print(url,"returned response code:",resp.status)
    
        
    
    return links_list

# valid status codes are from 200-399, and 204 means no content
def is_valid_status(resp):
    if(resp.status < 200 or resp.status >= 400 or resp.status == 204):
        return False
    else:
        return True

def is_valid(url):
    #valid domains for the purpose of this assignment
    valid_urls = set(["ics.uci.edu","ics.uci.edu","informatics.uci.edu","stat.uci.edu","today.uci.edu/department/information_computer_sciences"])
    try:
        parsed = urlparse(url)
        
        if parsed.scheme not in set(["http", "https"]):
            return False
        #check if the url is in one of the given domain
        for valid_url in valid_urls:
            if valid_url in url:
                #if the url has already been explored, it is no longer valid
                if (url[:-1] if (url[-1] == "/") else url) in explored_urls:
                    print("ALREADY EXPLORED", url)
                    return False
                else:
                    print("CORRECT Domain:",url)
                    #if the url is in given domain, return if it is a valid url or not
                    return not re.match(
                        r".*\.(css|js|bmp|gif|jpe?g|ico"
                        + r"|png|tiff?|mid|mp2|mp3|mp4"
                        + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                        + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
                        + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
                        + r"|epub|dll|cnf|tgz|sha1"
                        + r"|thmx|mso|arff|rtf|jar|csv"
                        + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise