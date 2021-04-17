import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup

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

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation requred.
    #TODO: Check resp.status codes
        #If resp.status is between [200-599] response is in resp.raw_response
        #If resp.status is [600-606] reason for error is in resp.error
    #TODO: parse resp.raw_response (could use beautifulsoup)
        #Extract all urls
        #This also might be the area to get all the info for our report
    if resp.status == 200:
        soup = BeautifulSoup(resp.raw_response,'html.parser')
        for link in soup.find_all('a'):
            print(link.get('href'))
    return list()

def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
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