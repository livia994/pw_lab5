## **Report Laboratory Work 5**
A simple command-line web request and search tool built using Python **without third-party HTTP libraries**.  
Supports fetching web pages, searching DuckDuckGo or Google, handling redirects, and opening search results.  

## **Features**  
✅ Fetch a webpage using `-u`  
✅ Search using `-s` (DuckDuckGo/Google)  
✅ Clean HTML output (no tags, just readable text)  
✅ Follow redirects automatically  
✅ Open a specific search result with `-o`  

### ** Usage**  
```bash
python go2web.py -h               # Show help  
python go2web.py -u <URL>         # Fetch and display a webpage  
python go2web.py -s <search-term> # Search and display results  
python go2web.py -o <number>      # Open a search result  
```

### **Example Usage**  
#### **Fetching a webpage:**  
```bash
python go2web.py -u https://floralsoul.con
```
#### **Searching:**  
```bash
python go2web.py -s "open source AI"
```
#### **Opening the first search result:**  
```bash
python go2web.py -o 1
```

## **Requirements**  
- Python 3  
- No external libraries (only built-in modules)  

## **How it Works**  
- Uses **raw TCP sockets** to send HTTP requests.  
- Parses HTML responses to extract **only readable text**.  
- Handles **redirects (301, 302, etc.)** automatically.  
- Saves **search results** to a file so they can be accessed later.  

## **Bonus Features**  
✔ Redirect handling (automatically follows redirects)  
✔ Can open search results directly  

## **To-Do (Possible Improvements)**  
🔲 Implement **HTTP caching** to improve performance  
🔲 Add **JSON support** (content negotiation)  

## **Demo**  

Demonstration of fetching and displaying the content of an website
https://youtu.be/n9i4uPSiwc4

Demonstration of showing the -h help menu options, displaying top 10 results using -s, and opening one of them using -o
https://youtu.be/6Z4S-Jx5zjY
