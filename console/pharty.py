#!/usr/bin/env python3.6

import argparse


def main():
    command_line = argparse.ArgumentParser(
        prog='phart',
        description='This script downloads web page by specified URL and '
                    'store it as a .mff (mozilla file format) format.')

    command_line.add_argument('-u', '--url', help='specify URL of site to archive',
                        required=True)
    command_line.add_argument('-o', '--output', help="name of MAFF archive", required=True)
    command_line.add_argument('-r', '--reg-list', nargs='+', default=[], required=False)
    args = command_line.parse_args()

    print(command_line)


if __name__ == "__main__":
    main()
