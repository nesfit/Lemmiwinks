#!/usr/bin/env python3.6

import getpage
import argparse


def main():
    parser = argparse.ArgumentParser(
        prog='wpd',
        description='This script downloads web page by specified URL and '
                    'store it as a .mff (mozilla file format) format.')

    parser.add_argument('-u', '--url', help='specify URL of site to archive', required=True)
    parser.add_argument('-o', '--output', help="name of MAFF archive", required=True)
    parser.add_argument('-r', '--reg-list', nargs='+', default=[], required=False)
    args = parser.parse_args()
    print(args.reg_list)
    #try:
    page = getpage.GetPage([args.url, "screen", "metainfo"], args.output, args.reg_list)
    page.save_page()
    #except Exception:
    #    print("Unexpected ERROR")
    #    return -20

if __name__ == "__main__":
    main()
