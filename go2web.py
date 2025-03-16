#!/usr/bin/env python
import argparse

def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(prog='go2web', description='Web request and search tool')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-u', '--url', help='Make an HTTP request to the specified URL')
    group.add_argument('-s', '--search', help='Search the term using DuckDuckGo and print top 10 results')
    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()

    if args.url:
        print(f"URL feature not implemented yet. You requested: {args.url}")
    elif args.search:
        print(f"Search feature not implemented yet. You searched for: {args.search}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()