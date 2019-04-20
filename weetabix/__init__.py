"""
Given a delimited flat text file, with a specified "key" column, generate an index specifying where to find
    rows with a given value

This is useful for, eg, looking up all information associated with a given phenotype ID

"""
import csv
from distutils.version import LooseVersion
import json
import os
import typing as ty

__version__ = '0.1.0'
__version_info__ = tuple(LooseVersion(__version__).version)


def _default_index_name(filename):
    return '{}.wtb'.format(filename)


class Writer:
    def __init__(self, source_filename: str, *,
                 skip_lines: int = 1,
                 delimiter: str = '\t'):
        """

        :param source_filename: The file to index
        :param skip_lines: Number of headers/other lines to skip
        :param delimiter: The character used to separate fields
        """
        self._source = source_filename
        self._skip_lines = skip_lines
        self._delimiter = delimiter

        self._index = None

    def make_index(self, key_col, *, key_func=None, index_fn=None) -> str:
        """

        :param key_col: Specify which column to use in building the categories (1-based index)
        :param key_func: (optional) Specify any transforms to apply to the key value. Eg, to convert "City, state" to
            "state" (for a more coarse-grained index).
        :param index_fn: (optional) Specify where to write the index file. Eg, to create multiple indices on the same
        dataset.
        :return:
        """

        index_fn = index_fn or _default_index_name(self._source)
        if self._source == index_fn:
            raise Exception('Index and source filename must not be the same')

        # The resulting index will have the following format: { delimiter: '\t', keys: { cat: (start, end) } }
        byte_index = {'delimiter': self._delimiter, 'keys': {} }
        last_key = None

        key_col = key_col - 1  # 0-based index

        with open(self._source, 'r') as f:
            for r in range(self._skip_lines):
                f.readline()

            span_start = last_line_end = f.tell()

            # Bypass the read-ahead buffer, allowing f.tell to be (reliably) used in indexing, at the cost of some
            # performance. Other methods (such as checking bytes read in) can be unreliable because python will do
            # things like auto-translate line separators.  TODO: Can we find a better way?
            # See: https://stackoverflow.com/questions/14145082/file-tell-inconsistency/14145118#14145118
            reader = csv.reader(iter(f.readline, ''), delimiter=self._delimiter)

            for row in reader:
                key = row[key_col]
                if key_func:
                    key = key_func(key)

                position = f.tell()

                if last_key is None:
                    last_key = key

                if key != last_key:
                    byte_index['keys'][last_key] = (span_start, last_line_end)
                    span_start = last_line_end

                # Advance the iteration
                last_key = key
                last_line_end = position

            if last_key not in byte_index:
                # In case file has no newline at end
                byte_index['keys'][last_key] = (span_start, last_line_end)  # type: ignore

        with open(index_fn, 'w') as f:
            json.dump(byte_index, f, separators=(',', ':'), allow_nan=False)

        self._index = byte_index
        return index_fn

    def get_keys(self):
        if self._index is None:
            raise Exception('You must generate the index before inspecting its values')
        return self._index['keys'].keys()


class Reader:
    def __init__(self, source_filename: str, *, index_fn: str = None):
        """

        :param source_filename: Path to the actual data of interest
        :param index_fn: (optional) Specify path to the index file of interest
        """
        self._source = source_filename
        index_fn = index_fn or _default_index_name(source_filename)
        if not os.path.isfile(index_fn):
            raise FileNotFoundError

        with open(index_fn, 'rb') as f:
            byte_index = json.load(f)

        self._delimiter = byte_index['delimiter']
        self._keys = byte_index['keys']

    def fetch(self, value: str, *, strict: bool = False) -> ty.Iterator:
        """
        Fetch all lines that reference the specified key, from a previously indexed file
        :param value:
        :param strict: (optional) Throw a KeyError if the desired value is not in the file
        :return: An array of strings, one per line of the file
        """

        if value not in self._keys and not strict:
            # Sometimes the file may not have any information about the user's query, and that is usually ok
            return []

        start, end = self._keys[value]

        with open(self._source, 'r') as f:  # type: ignore
            # Note: Fetches all the data requested, even if it's a lot. Don't request a lot.
            f.seek(start, 0)
            return csv.reader(f.read(end - start).splitlines(), delimiter=self._delimiter)

    def get_keys(self):
        return self._keys.keys()
