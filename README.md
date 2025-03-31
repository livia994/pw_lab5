## **Report Laboratory Work 5**
A simple command-line web request and search tool built using Python **without third-party HTTP libraries**.  
Supports fetching web pages, searching DuckDuckGo or Google, handling redirects, caching responses and opening search results.  

## **Features**  
✅ Fetch a webpage using `-u`  
✅ Search using `-s` (DuckDuckGo/Google)  
✅ Clean HTML output (no tags, just readable text)  
✅ Follow redirects automatically  
✅ Open a specific search result with `-o`  
✅ Caching mechanism for improved performance
✅ Content negotiation with Accept headers
✅ Handles ETag and Last-Modified headers for efficient revalidation
✅ Specify content type (html or json) with -t
✅ Disable caching per request with --no-cache
✅ Clear all cached responses with --clear-cache

### **Usage**  
```bash
python go2web.py -h               # Show help  
python go2web.py -u <URL>         # Fetch and display a webpage  
python go2web.py -s <search-term> # Search and display results  
python go2web.py -o <number>      # Open a search result  
python go2web.py -t <type>        # Specify content type (html/json)  
python go2web.py --no-cache       # Disable caching for this request  
python go2web.py --clear-cache    # Clear all cached responses  
```

### **Example Usage**  
#### **Fetching a webpage:**  
```bash
python go2web.py -u https://floralsoul.com
```
#### **Searching:**  
```bash
python go2web.py -s "open source AI"
```
#### **Opening the first search result:**  
```bash
python go2web.py -o 1
```
#### **Fetching JSON response (if available):**  
```bash
python go2web.py -u https://api.github.com/repos/python/cpython -t json --no-cache
```
#### **Disabling cache for a request:**  
```bash
python go2web.py -u https://999.md --no-cache
```
#### **Clearing all cached responses:**  
```bash
python go2web.py --clear-cache
```

## **Requirements**  
- Python 3  
- No external libraries (only built-in modules)  

## **How it Works**  
- Uses **raw TCP sockets** to send HTTP requests.  
- Parses HTML responses to extract **only readable text**.  
- Handles **redirects (301, 302, etc.)** automatically.  
- Saves **search results** to a file so they can be accessed later. 
- Implements HTTP caching for optimized performance. 
- Uses ETag and Last-Modified headers for conditional requests. 
- Supports content negotiation (e.g., JSON, text, or specific MIME types).

## **Bonus Features**  
✔ Redirect handling (automatically follows redirects)  
✔ Can open search results directly
✔ Implement **HTTP caching** to improve performance 
✔ Add **JSON support** (content negotiation)  


## **Demo**  

Demonstration of fetching and displaying the content of an website
https://youtu.be/n9i4uPSiwc4

Demonstration of showing the -h help menu options, displaying top 10 results using -s, and opening one of them using -o
https://youtu.be/6Z4S-Jx5zjY

Demonstration of fetching the json response
https://youtu.be/3llwQolELbc

Demonstration of cashing responses
https://youtu.be/TLEHuNC3CgA

Demonstration of --no-cache functionality
https://youtu.be/ct9-TC466AQ

## **Screenshots**

**Function -u**
![Captură de ecran 2025-03-17 184254](https://github.com/user-attachments/assets/bc63e65d-e83f-41be-8a39-e5cf55e28a43)
**Function -s & -h**
![Captură de ecran 2025-03-17 184355](https://github.com/user-attachments/assets/1c5fa66b-dbf3-4f21-b619-163de46436f4)
![Captură de ecran 2025-03-17 184437](https://github.com/user-attachments/assets/9fd5429b-64f7-4407-a0bb-4e3ead71dc78)
**Function -o**
![Captură de ecran 2025-03-17 184454](https://github.com/user-attachments/assets/6c3f3d2a-c92c-43f9-8311-1b36d955ee77)

