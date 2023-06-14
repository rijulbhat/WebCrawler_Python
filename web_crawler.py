import requests, sys, os, argparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import urllib.request
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

orig_stdout = sys.stdout

parser=argparse.ArgumentParser()
parser.add_argument('-u', '--url', nargs='+', required=True, action='store', dest='url', default=False, help="provide url")
parser.add_argument('-t', '--threshold', nargs=1, required=False, action='store', dest='threshold', default=False, help="provide threshold")
parser.add_argument('-o', '--output', nargs='+', required=False, action='store', dest='output', default=False, help="provide output file")
parser.add_argument('-d', '--download', nargs='*', required=False, action='store', dest='download', default=False, help="provide extension of file which you want to download or do not specify any arguments to download every file directory wise")
parser.add_argument('-s', '--size', action='store_true', help="flag for file size")
parser.add_argument('-x', '--sort', action='store_true', help="flag for sorting with respect to file size")
args=parser.parse_args()

if args.output:
    if len(args.output) != len(args.url):
        parser.print_help()
        sys.exit(1)
    else:
        flag = True
else:
    flag = False

if args.threshold:
    flag_th = True

else:
    flag_th = False 

downloaded = []

#Returns File Extension
def get_file_extension(link):
    parsed_link = urlparse(link)
    path = parsed_link.path
    return os.path.splitext(path)[1]

#Downloads file present in the given url
def download_file(url):
    if url in downloaded:
        return
    else:
        downloaded.append(url)

    if url[-1] == '/':
        url = url[:-1]
    
    parsed_link = urlparse(url)


    destination = parsed_link.path
    destination = f"./{parsed_link.netloc}{destination}"
    parent_directory = "/".join(destination.split("/")[:-1])
    os.makedirs(parent_directory, exist_ok=True)
    
    try:
        if get_file_extension(url) == "": 
            urllib.request.urlretrieve(url, destination+".html")
        else:
            urllib.request.urlretrieve(url, destination)

        print(url, "File downloaded successfully.")
        
    except Exception as e:
        print(url, "Error occurred while downloading the file:", str(e))

#Returns file size in KB
def get_file_size(url):
    try:
        response = requests.head(url, allow_redirects=True)
        if 'Content-Length' in response.headers:
            size_in_bytes = int(response.headers['Content-Length'])
            size_in_kb = size_in_bytes / 1024
            return size_in_kb
        else:
            return float(-1)

    except requests.exceptions.RequestException as e:
        return float(-1)

# Recursive Function which crawls the link given as arguments in the form of url and anchor and takes attribute as argument which determines which attribute to look into
def attribute_crawler(url, i, anchor, attribute, level=0, max_level=None, visited_pages=None, visited_pages_wo_level=None):
    href = anchor.get(attribute)
    absolute_url = urljoin(url, href)

    # This line does not iterate websites again even if a slash has been added at the end but here it only saves time as even if it crawls again it will not give any addiitonal output as 2 same files/pages arem't allowed

    same_absolute_url = absolute_url

    if same_absolute_url[-1] == '/':
        same_absolute_url = same_absolute_url[:-1]
    
    if absolute_url not in visited_pages_wo_level and same_absolute_url not in visited_pages_wo_level and (urlparse(absolute_url).netloc == urlparse(args.url[i]).netloc):
        crawl_website(absolute_url, i, level+1, max_level, visited_pages, visited_pages_wo_level)

    elif absolute_url not in visited_pages_wo_level and same_absolute_url not in visited_pages_wo_level:
        visited_pages.append((absolute_url, level+1))
        visited_pages_wo_level.append(absolute_url)

    if args.download:    
        if get_file_extension(absolute_url) in args.download:
                    download_file(absolute_url)
        if ".html" in args.download and get_file_extension(absolute_url) == "":
            download_file(absolute_url)
    elif args.download == []:
        download_file(absolute_url)

# This function gets all the links corresponding to src and href in the url provided 
def crawl_website(url, i, level=0, max_level=None, visited_pages=None, visited_pages_wo_level=None):
    if visited_pages is None:
        visited_pages = []

    if visited_pages_wo_level is None:
        visited_pages_wo_level = []

    if level!=0:
        visited_pages.append((url,level))
        visited_pages_wo_level.append(url)

    if max_level is not None:
        if level >= max_level:
            return visited_pages

    try:
        response = requests.get(url, verify=False)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Process the page content here if needed
            # ...

            # Find all anchor tags and extract their href attribute
            anchors = soup.find_all(href=True)
            for anchor in anchors:
                attribute_crawler(url, i, anchor, 'href', level, max_level, visited_pages, visited_pages_wo_level)


            anchors = soup.find_all(src=True)
            for anchor in anchors:
                attribute_crawler(url, i, anchor, 'src', level, max_level, visited_pages, visited_pages_wo_level)                 

    except requests.exceptions.RequestException as e:
        pass

    return visited_pages


# File Handling and generating the output file in the desired format
for i in range(len(args.url)):
    # Specify the starting URL of the website you want to crawl
    start_url = args.url[i]

    if flag_th:
        max_level = int(args.threshold[0])
        result = crawl_website(start_url, i, max_level=max_level)
        
    else:
        result = crawl_website(start_url, i)


    # Sort the visited pages based on the recursive level, file extension (or size if -x is provided)

    if args.sort:
        sorted_result = sorted(result, key=lambda x: (x[1], get_file_extension(x[0]), get_file_size(x[0])))
    else:
        sorted_result = sorted(result, key=lambda x: (x[1], get_file_extension(x[0])))
    if sorted_result != []:
        count_arr = [0 for _ in range(sorted_result[-1][1]+1)]
    ext_dict = dict()
    internal_links_count = dict()
    external_links_count = dict()
    page_size_dict = dict()
    for x in sorted_result:
        count_arr[x[1]] += 1
        if x[1] not in internal_links_count:
            internal_links_count[x[1]] = 0
        if x[1] not in external_links_count:
            external_links_count[x[1]] = 0

        if urlparse(x[0]).netloc == urlparse(args.url[i]).netloc:
            internal_links_count[x[1]] +=1
        else:
            external_links_count[x[1]] +=1


    if flag:
        sys.stdout = open(f"./{args.output[i]}", 'w')

    # Print the list of visited pages with their recursive level
    prev_level = 0
    level = 0
    
    prev_ext = "-1"
    curr_ext = "-1"
    
    unique_pages = set()
    for page, level in sorted_result:
        unique_pages.add(page)
        if prev_level != level:
            if prev_ext != "-1":
                print(f"\n\n{ext_dict[prev_ext]} files found")
            print(f"\n\nAt recursion level {level}")
            print(f"\nTotal files found: {count_arr[level]}")
            print(f"\nInternal links: {internal_links_count[level]}")
            print(f"\nExternal links: {external_links_count[level]}")
            prev_ext = "-1"
            curr_ext = "-1"
            ext_dict = dict()

        curr_ext = get_file_extension(page)

        if curr_ext in ext_dict:
            ext_dict[curr_ext] += 1
        else:
            ext_dict[curr_ext] = 1

        if prev_ext != curr_ext:
            if prev_ext!="-1":    
                print(f"\n\n{ext_dict[prev_ext]} files found\n")
            if curr_ext != "":
                print(f"\n\n\n{curr_ext} files:")
            else:
                print(f"\n\n\nWebpages or Miscellaneous files:")
        
        if args.size:
            if page not in page_size_dict:
                page_size_dict[page] = get_file_size(page)
            if page_size_dict[page] != -1:
                print(f"\n{page}, size: {round(page_size_dict[page], 2)} KB")
            else:
                print(f"\n{page}, size: Not Found")
        else:
            print(f"\n{page}")
        
        prev_ext = curr_ext
        prev_level = level

    # Print the total number of pages visited
    if curr_ext != "-1":
        print(f"\n\n{ext_dict[prev_ext]} files found\n")
    total_internal_links_count = 0
    total_external_links_count = 0
    for link in unique_pages:
        if urlparse(link).netloc == urlparse(args.url[i]).netloc:
            total_internal_links_count +=1 
        else:
            total_external_links_count += 1
    #Print the total unique internal links
    print(f"\nTotal unique internal links found: {total_internal_links_count}")
    #Print the total unique external links
    print(f"\nTotal unique external links found: {total_external_links_count}")
    total_pages = len(result)
    print(f"\nTotal files Found: {total_pages}")
    if sys.stdout != orig_stdout:
        sys.stdout = orig_stdout
        print(f"Total files Found: {total_pages}")