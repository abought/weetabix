"""Command line utility for indexing a file"""

import argparse
import itertools

import weetabix


def parse_args():
    parser = argparse.ArgumentParser(description='Generate an index')
    parser.add_argument('source_filename',
                        help='The datafile to be indexed')
    parser.add_argument('key_col',
                        type=int,
                        help='Specify which column to use in building the categories (1-based index)')

    parser.add_argument('-S', '--skip-lines', dest='skip',
                        type=int, default=0,
                        help='The number of header rows to exclude from indexing')
    parser.add_argument('-d', '--delimiter', dest='delimiter',
                        default='\t',
                        help='The character used to distinguish between fields')

    parser.add_argument('-o', '--index-name', dest='index_fn',
                        help='The name of the index file to be written')

    return parser.parse_args()


def run_cli():
    args = parse_args()

    writer = weetabix.Writer(args.source_filename, skip_lines=args.skip, delimiter=args.delimiter)
    index_fn = writer.make_index(args.key_col, index_fn=args.index_fn)

    print('Indexing complete. To verify your delimiter and parsing options, here are three sample values from the index: ')
    for row in itertools.islice(writer.get_keys(), 3):
        print('-', row)

    print('Index written to: ', index_fn)
