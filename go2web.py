#!/usr/bin/env python
import socket
import ssl
import re
import argparse
import sys
import html
import urllib.parse
import os
import hashlib
import time
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta

class HTTPClient:
    def __init__(self):
        self.socket = None
        self.ssl_context = ssl.create_default_context()
        self.cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cache')
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def parse_url(self, url):
        """Parse URL into components"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        parsed = urlparse(url)
        protocol = 'https' if parsed.scheme == 'https' else 'http'
        host = parsed.netloc
        path = parsed.path if parsed.path else '/'
        if parsed.query:
            path += '?' + parsed.query

        port = 443 if protocol == 'https' else 80

        return protocol, host, path, port

    def connect(self, host, port, use_ssl=True):
        """Establish connection to host"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(10)

        try:
            self.socket.connect((host, port))
            if use_ssl:
                self.socket = self.ssl_context.wrap_socket(self.socket, server_hostname=host)
            return True
        except (socket.timeout, socket.error) as e:
            print(f"Connection error: {e}")
            return False

    def get_cache_key(self, url, accept_header):
        """Generate a cache key based on URL and content type"""
        return hashlib.md5(f"{url}_{accept_header}".encode()).hexdigest()

    def is_cached_response_valid(self, cache_file):
        """Check if a cached response is still valid based on cache control headers"""
        if not os.path.exists(cache_file):
            return False

        try:
            with open(cache_file, 'r', encoding='utf-8', errors='replace') as f:
                cached_response = f.read()

            # Extract headers from cached response
            headers_part = cached_response.split('\r\n\r\n', 1)[0]
            if not headers_part:
                headers_part = cached_response.split('\n\n', 1)[0]

            # Check for expiration headers
            max_age_match = re.search(r'Cache-Control:.*?max-age=(\d+)', headers_part, re.IGNORECASE)
            if max_age_match:
                max_age = int(max_age_match.group(1))
                file_modified_time = os.path.getmtime(cache_file)
                if time.time() - file_modified_time > max_age:
                    return False

            expires_match = re.search(r'Expires:\s*(.*?)[\r\n]', headers_part, re.IGNORECASE)
            if expires_match:
                expires_str = expires_match.group(1).strip()
                try:
                    # Parse the expiration date
                    expires_date = datetime.strptime(expires_str, '%a, %d %b %Y %H:%M:%S %Z')
                    if datetime.now() > expires_date:
                        return False
                except ValueError:
                    # If we can't parse the date, we assume the cache is invalid
                    return False

            # Check for conditional headers to use in validation
            etag_match = re.search(r'ETag:\s*(.*?)[\r\n]', headers_part, re.IGNORECASE)
            last_modified_match = re.search(r'Last-Modified:\s*(.*?)[\r\n]', headers_part, re.IGNORECASE)

            if etag_match or last_modified_match:
                return True  # We have validators to use for revalidation

            # Default cache lifetime if no explicit expiration
            file_modified_time = os.path.getmtime(cache_file)
            default_ttl = 3600  # 1 hour
            return (time.time() - file_modified_time) < default_ttl

        except Exception as e:
            print(f"Cache validation error: {e}")
            return False

    def get_cached_validators(self, cache_file):
        """Extract validators from cached response for revalidation"""
        validators = {}

        if not os.path.exists(cache_file):
            return validators

        try:
            with open(cache_file, 'r', encoding='utf-8', errors='replace') as f:
                cached_response = f.read()

            headers_part = cached_response.split('\r\n\r\n', 1)[0]
            if not headers_part:
                headers_part = cached_response.split('\n\n', 1)[0]

            etag_match = re.search(r'ETag:\s*(.*?)[\r\n]', headers_part, re.IGNORECASE)
            if etag_match:
                validators['If-None-Match'] = etag_match.group(1).strip()

            last_modified_match = re.search(r'Last-Modified:\s*(.*?)[\r\n]', headers_part, re.IGNORECASE)
            if last_modified_match:
                validators['If-Modified-Since'] = last_modified_match.group(1).strip()

            return validators
        except Exception as e:
            print(f"Error extracting validators: {e}")
            return validators

    def should_cache_response(self, response_headers):
        """Determine if a response should be cached based on its headers"""
        # Don't cache responses with Cache-Control: no-store
        if re.search(r'Cache-Control:.*?no-store', response_headers, re.IGNORECASE):
            return False

        # Don't cache private responses
        if re.search(r'Cache-Control:.*?private', response_headers, re.IGNORECASE):
            return False

        # Don't cache if explicitly told not to
        if re.search(r'Cache-Control:.*?no-cache', response_headers, re.IGNORECASE):
            return False

        # Default to caching GET responses that are successful
        status_match = re.search(r'HTTP/[\d.]+\s+(\d+)', response_headers)
        if status_match and status_match.group(1) == '200':
            return True

        return False

    def send_request(self, host, path, method="GET", headers=None, body=None):
        """Send HTTP request"""
        if headers is None:
            headers = {}

        headers.update({
            "Host": host,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": headers.get("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"),
            "Connection": "close"
        })

        request_lines = [f"{method} {path} HTTP/1.1"]
        for key, value in headers.items():
            request_lines.append(f"{key}: {value}")

        request = "\r\n".join(request_lines) + "\r\n\r\n"
        if body:
            request += body

        try:
            self.socket.sendall(request.encode())
            return True
        except Exception as e:
            print(f"Request error: {e}")
            return False

    def receive_response(self):
        """Receive and parse HTTP response"""
        response = b''
        try:
            while True:
                data = self.socket.recv(4096)
                if not data:
                    break
                response += data

            return response.decode('utf-8', errors='replace')
        except Exception as e:
            print(f"Response error: {e}")
            return None

    def close(self):
        """Close the connection"""
        if self.socket:
            self.socket.close()

    def request(self, url, method="GET", headers=None, body=None, follow_redirects=True, max_redirects=5, use_cache=True):
        """Make HTTP request and handle redirects with caching"""
        if headers is None:
            headers = {}

        protocol, host, path, port = self.parse_url(url)

        # Set default Accept header if not provided
        accept_header = headers.get("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
        headers["Accept"] = accept_header

        cache_key = self.get_cache_key(url, accept_header)
        cache_file = os.path.join(self.cache_dir, cache_key)

        # Check cache for GET requests
        if method == "GET" and use_cache:
            if self.is_cached_response_valid(cache_file):
                print(f"Using cached response for {url}")

                # Get validators for conditional request
                validators = self.get_cached_validators(cache_file)
                if validators:
                    # Add validation headers
                    headers.update(validators)

                    # Make conditional request
                    if not self.connect(host, port, use_ssl=(protocol == 'https')):
                        print("Connection failed, using cached response")
                        with open(cache_file, 'r', encoding='utf-8', errors='replace') as f:
                            return f.read()

                    if not self.send_request(host, path, method, headers, body):
                        self.close()
                        print("Request failed, using cached response")
                        with open(cache_file, 'r', encoding='utf-8', errors='replace') as f:
                            return f.read()

                    response = self.receive_response()
                    self.close()

                    if response:
                        status_match = re.search(r'HTTP/[\d.]+\s+(\d+)', response)
                        if status_match and status_match.group(1) == '304':  # Not Modified
                            print("Resource not modified, using cached version")
                            with open(cache_file, 'r', encoding='utf-8', errors='replace') as f:
                                return f.read()
                        else:
                            # Update cache with new response
                            if self.should_cache_response(response.split('\r\n\r\n', 1)[0]):
                                try:
                                    with open(cache_file, 'w', encoding='utf-8') as f:
                                        f.write(response)
                                except Exception as e:
                                    print(f"Warning: Failed to cache response: {e}")
                            return response
                else:
                    # No validators, but cache is still valid
                    with open(cache_file, 'r', encoding='utf-8', errors='replace') as f:
                        return f.read()

        # No valid cache, make a new request
        if not self.connect(host, port, use_ssl=(protocol == 'https')):
            return None

        if not self.send_request(host, path, method, headers, body):
            self.close()
            return None

        response = self.receive_response()
        self.close()

        if not response:
            return None

        # Check HTTP status code
        status_match = re.search(r'HTTP/[\d.]+\s+(\d+)', response)
        if status_match:
            status_code = status_match.group(1)
            if status_code.startswith('4') or status_code.startswith('5'):
                print(f"Server returned error status: {status_code}")
                # Continue processing as response may contain error details

        # Cache the response if appropriate
        if method == "GET" and use_cache and self.should_cache_response(response.split('\r\n\r\n', 1)[0]):
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    f.write(response)
            except Exception as e:
                print(f"Warning: Failed to cache response: {e}")

        # Handle redirects
        if follow_redirects and max_redirects > 0:
            status_match = re.search(r'HTTP/[\d.]+\s+(\d+)', response)
            if status_match and status_match.group(1) in ('301', '302', '303', '307', '308'):
                location_match = re.search(r'Location:\s*(.*?)[\r\n]', response, re.IGNORECASE)
                if location_match:
                    redirect_url = location_match.group(1).strip()
                    if not redirect_url.startswith(('http://', 'https://')):
                        redirect_url = f"{protocol}://{host}{redirect_url}"

                    print(f"Redirecting to: {redirect_url}")
                    return self.request(redirect_url, method, headers, body, follow_redirects, max_redirects - 1, use_cache)
        return response


def extract_html_content(response):
    """Extract HTML body from response and clean it"""
    # Check if response is empty
    if not response:
        return "Empty response received."

    # Split headers and body
    parts = response.split('\r\n\r\n', 1)
    if len(parts) < 2:
        # Try alternative delimiter
        parts = response.split('\n\n', 1)
        if len(parts) < 2:
            return "No content found in response."

    body = parts[1]

    # Remove HTML tags
    clean_text = re.sub(r'<head>.*?</head>', '', body, flags=re.DOTALL)
    clean_text = re.sub(r'<script.*?>.*?</script>', '', clean_text, flags=re.DOTALL)
    clean_text = re.sub(r'<style.*?>.*?</style>', '', clean_text, flags=re.DOTALL)
    clean_text = re.sub(r'<.*?>', ' ', clean_text)

    # Decode HTML entities
    clean_text = html.unescape(clean_text)

    # Replace multiple spaces and newlines
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    return clean_text


def extract_search_results(response, search_engine):
    """Extract and parse search results based on the search engine"""
    if search_engine == "duckduckgo":
        # Debug response to file for troubleshooting
        print("=== DEBUGGING DUCKDUCKGO RESPONSE ===")
        header_part = response.split('\r\n\r\n', 1)[0]
        if not header_part:
            header_part = response.split('\n\n', 1)[0]
        print(header_part[:1000])  # Print first 1000 chars of headers
        print("================================")

        # Extract organic search results
        results = []

        # DuckDuckGo uses JavaScript to load results, but we can try to find links in the initial HTML
        links = re.findall(r'<a.*?href="(https?://(?!duckduckgo\.com).*?)".*?>(.*?)</a>', response, re.DOTALL)

        seen_urls = set()
        for url, title in links:
            # Skip duplicates and internal links
            if url in seen_urls or 'duckduckgo.com' in url or not url.startswith(('http://', 'https://')):
                continue

            # Clean the title
            clean_title = re.sub(r'<.*?>', '', title)
            clean_title = html.unescape(clean_title).strip()

            if clean_title and len(clean_title) > 5:  # Avoid very short or empty titles
                results.append({'title': clean_title, 'url': url})
                seen_urls.add(url)

                if len(results) >= 10:
                    break

        if not results:
            return "No results found. Please check your query or DuckDuckGo's page structure."

        output = []
        for i, result in enumerate(results, 1):
            output.append(f"{i}. {result['title']}\n   URL: {result['url']}")

        return "\n\n".join(output)

    elif search_engine == "google":
        results = []

        # Try to extract Google search results
        links = re.findall(r'<a href="(/url\?q=|)(https?://(?!google\.com).*?)(?:&amp;|")', response)
        titles = re.findall(r'<h3.*?>(.*?)</h3>', response)

        seen_urls = set()
        result_count = 0

        for link_match in links:
            url = link_match[1]
            if '&' in url:
                url = url.split('&')[0]

            if url in seen_urls or 'google.com' in url:
                continue

            # Try to find a corresponding title
            title = f"Result {result_count + 1}"
            if result_count < len(titles):
                clean_title = re.sub(r'<.*?>', '', titles[result_count])
                clean_title = html.unescape(clean_title).strip()
                if clean_title:
                    title = clean_title

            results.append({'title': title, 'url': url})
            seen_urls.add(url)
            result_count += 1

            if result_count >= 10:
                break

        if not results:
            return "No results found. Please check your query or Google's page structure."

        output = []
        for i, result in enumerate(results, 1):
            output.append(f"{i}. {result['title']}\n   URL: {result['url']}")

        return "\n\n".join(output)

    return "Unsupported search engine."


def fetch_url(url):
    """Fetch content from specified URL"""
    client = HTTPClient()
    response = client.request(url)

    if not response:
        return "Failed to fetch URL."

    return extract_html_content(response)


def search(term, engine="duckduckgo"):
    """Search using specified search engine"""
    client = HTTPClient()

    if engine == "duckduckgo":
        url = f"https://duckduckgo.com/html/?q={urllib.parse.quote_plus(term)}"
        headers = {
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://duckduckgo.com/"
        }
    elif engine == "google":
        url = f"https://www.google.com/search?q={urllib.parse.quote_plus(term)}"
        headers = {
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/"
        }
    else:
        return "Unsupported search engine."

    response = client.request(url, headers=headers)
    if not response:
        return "Failed to get search results."

    return extract_search_results(response, engine)


def open_result(result_number, search_results):
    """Open a specific search result"""
    lines = search_results.strip().split('\n\n')
    if 0 < result_number <= len(lines):
        result = lines[result_number - 1]
        url_match = re.search(r'URL: (https?://.*?)$', result, re.MULTILINE)
        if url_match:
            url = url_match.group(1)
            return fetch_url(url)
        else:
            return "Could not find URL in search result."
    else:
        return f"Invalid result number. Please specify a number between 1 and {len(lines)}."


def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(prog='go2web', description='Web request and search tool')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-u', '--url', help='Make an HTTP request to the specified URL')
    group.add_argument('-s', '--search', help='Search the term using DuckDuckGo and print top 10 results')
    group.add_argument('-o', '--open', type=int, help='Open the specified search result')
    parser.add_argument('--no-cache', action='store_true', help='Disable HTTP caching for this request')
    parser.add_argument('--clear-cache', action='store_true', help='Clear all cached responses')
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    # Store last search results for -o option
    last_search_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.last_search')

    # Handle cache clearing
    if args.clear_cache:
        client = HTTPClient()
        cache_dir = client.cache_dir
        if os.path.exists(cache_dir):
            for file in os.listdir(cache_dir):
                os.remove(os.path.join(cache_dir, file))
            print(f"Cache cleared: {cache_dir}")
        else:
            print("No cache directory found.")

    if args.url:
        use_cache = not args.no_cache
        result = fetch_url(args.url)
        print(result)
    elif args.search:
        result = search(args.search)
        print(result)

        # Save search results for later access
        with open(last_search_file, 'w', encoding='utf-8') as f:
            f.write(result)
    elif args.open is not None:
        # Check if we have saved search results
        if os.path.exists(last_search_file):
            with open(last_search_file, 'r', encoding='utf-8') as f:
                last_search = f.read()
            result = open_result(args.open, last_search)
            print(result)
        else:
            print("No previous search results found. Please run a search first using the -s option.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()