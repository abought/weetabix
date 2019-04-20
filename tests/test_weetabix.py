"""Test simple key-based indexing of files"""

import json
import os
import shutil

import pytest

import weetabix

FIXTURE1 = os.path.join(os.path.dirname(__file__), 'fixtures/sample_icd10.csv')
FIXTURE2 = os.path.join(os.path.dirname(__file__), 'fixtures/sample.tab')


@pytest.fixture(scope='module')
def sample_data(tmpdir_factory):
    """Index a test CSV file"""
    fn = tmpdir_factory.getbasetemp() / 'sample.csv'
    shutil.copy(FIXTURE1, fn)

    # Index the file on exact contents of column 1
    writer = weetabix.Writer(fn, skip_lines=0, delimiter=',')
    writer.make_index(1)
    return fn


@pytest.fixture(scope='module')
def secondary_index(tmpdir_factory, sample_data):
    # Index the file on just the first letter of column 1 (a category code)
    writer = weetabix.Writer(sample_data, skip_lines=0, delimiter=',')
    second = tmpdir_factory.getbasetemp() / 'sample.csv.second.wtb'
    writer.make_index(1, index_fn=second, key_func=lambda v: v[0])
    return second


@pytest.fixture(scope='module')
def sample_data_tsv(tmpdir_factory):
    """Index a test TSV file"""
    fn = tmpdir_factory.getbasetemp() / 'sample.tab'
    shutil.copy(FIXTURE2, fn)
    return fn


def test_generates_index_in_default_location(sample_data):
    expected_fn = weetabix._default_index_name(sample_data)
    assert os.path.isfile(expected_fn), "Index file was created"


def test_writer_indexes_tsv(sample_data_tsv):
    # Index the file on exact contents of column 1
    writer = weetabix.Writer(sample_data_tsv, skip_lines=1, delimiter='\t')
    writer.make_index(1)
    keys = list(writer.get_keys())
    assert keys == ['2', '1'], 'Indexed correct keys for tab delimited file'

    reader = weetabix.Reader(sample_data_tsv)
    first_row = next(reader.fetch('2'))
    assert len(first_row) == 5, 'Reader was able to parse tab delimited file'


def test_index_has_all_column_values(sample_data):
    index_fn = weetabix._default_index_name(sample_data)

    with open(index_fn, 'rb') as f:
        contents = json.load(f)

    keys = contents['keys'].keys()
    assert len(keys) == 7, 'has expected number of keys'
    assert set(keys) == {'A010', 'A011', 'A012', 'A013', 'A014', 'A02', 'W5622'}, 'has correct set of unique keys'


def test_gets_correct_number_of_lines_for_each_key(sample_data):
    expected = (
        ('A010', 2),
        ('A011', 1),
        ('A012', 1),
        ('A013', 1),
        ('A014', 1),
        ('A02', 2),
        ('W5622', 1)
    )
    reader = weetabix.Reader(sample_data)
    for k, count in expected:
        rows = reader.fetch(k)
        assert len(list(rows)) == count, 'found expected number of rows for key {}'.format(k)


def test_uses_secondary_index(sample_data, secondary_index):
    reader = weetabix.Reader(sample_data, index_fn=secondary_index)
    keys = list(reader.get_keys())
    assert len(keys) == 2
    assert keys == ['A', 'W']


def test_fetches_line_content_for_key(sample_data):
    expected = [['A011', '', 'A011', 'Paratyphoid fever A', 'Paratyphoid fever A', 'Paratyphoid fever A']]
    reader = weetabix.Reader(sample_data)
    rows = list(reader.fetch('A011'))
    assert rows == expected, 'returned expected row content'


def test_strict_mode_fails_if_key_not_in_index(sample_data):
    with pytest.raises(KeyError):
        reader = weetabix.Reader(sample_data)
        reader.fetch('not_a_key', strict=True)


def test_nonstrict_mode_returns_empty_list_for_absent_key(sample_data):
    reader = weetabix.Reader(sample_data)

    result = reader.fetch('not_a_key', strict=False)
    assert result == []
