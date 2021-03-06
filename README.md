[![Build Status](https://travis-ci.org/abought/weetabix.svg?branch=master)](https://travis-ci.org/abought/weetabix)

# Weetabix

Incremental random access to plaintext columnar data, based on simple byte-range indexing. 

## Installation and usage

Install from pypi:

`pip install weetabix`

This library requires Python >= 3.4.

Quickly generate an index of an existing CSV file from the command line (writes to filename.wtb):

` $  weetabix yourdata.csv 1 --delimiter ',' --skip-lines 1`

For full command details, see: 
`weetabix --help`


Or, use from python for more fine-grained control:
```python
import weetabix

# Index on the exact contents of column 1, eg "City, state"
writer = weetabix.Writer('sample.csv', delimiter=',')
writer.make_index(1)

# Create a second, more coarse grained index on the same column, but just using the "state" part
writer.make_index(1, index_fn='secondary.wtb', key_func=lambda v: v.rsplit(',')[-1].strip())

# Read part of a file, using the first index generated
reader = weetabix.Reader('sample.csv')
for row in reader.fetch('Portland, Oregon'):
    print(row)
    
# Read part of a file, using the second index (coarse grained)
reader = weetabix.Reader('sample.csv', index_fn='secondary.wtb')
for row in reader.fetch('Oregon'):
    print(row)    
```


## Purpose
Many data-intensive applications can read and write plaintext delimited data, and it is common to find very large 
datasets in formats such as [CSV](https://tools.ietf.org/html/rfc4180) or
[TSV](https://www.iana.org/assignments/media-types/text/tab-separated-values).

However, it is difficult to naively explore such large files through the web browser, to answer such trivial questions 
as "show only the records from 1991". 

Weetabix is a tool to create small *byte range indices* that identify the unique segments of your data, and allow 
querying just the subset of records of interest. This allows you to retrieve only a small amount of data from a much 
larger file, **without needing to write a separate web server or load your data into a database**. 

## Can my data use this tool?

Weetabix is designed to give you just the part of a file that references a particular unique value. This means that it
 works best with *categorical* data, in which the categories are well defined, and all the lines for that category 
 are stored in a continuous block.
 
 Good (contiguous categories):
> Category1, Value1  
Category1, Value2  
Category2, Value3
 
Bad (non-contiguous categories):  
> Category1, Value1  
Category2, Value2  
Category1, Value3

Bad (no obvious blocks of related records):    
> Anteater  
Sweater  
Blog


"Bad"* (categories are continuous instead of discrete):
> 1990  
1991  
1992


* There are many possible (and reasonable!) ways to index your data, but this tool only provides a single strategy. 
Even if that strategy is not the right fit, feel free to experiment and find the type (and format) of index that best 
suits your data.


## Development

We highly recommend that you conduct your work inside a virtualenv, though this is not an absolute requirement.

Install as a locally editable package, including the dependencies required for unit testing.

`$ pip install -e '.[test]'`

To run code quality and unit tests locally:

`$ pytest tests/ --flake8 --mypy`


## See also
[weetabix-client]() allows you to use the index file to make requests from a web browser, using JavaScript.

This project was inspired by [Tabix](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3042176/), a specialized tool used 
in bioinformatics to retrieve interesting regions from tab-delimited genomic data.

## Notes on deployment
Your web host must support Range requests. Many, but not all, do so. See: 
[Checking if a server supports partial requests](https://developer.mozilla.org/en-US/docs/Web/HTTP/Range_requests#Checking_if_a_server_supports_partial_requests).

Even if your server declares basic support, details vary widely across hosts, and depends on many factors- in 
particular, some CDNs have [issues](https://github.com/whatwg/fetch/issues/747) due to aggressive caching/compression 
that results in an unreadable response. If you encounter problems, consider simple file hosts such as 
Amazon S3 or Google Cloud Storage (see [CORS instructions](https://docs.cancergenomicscloud.org/docs/enabling-cross-origin-resource-sharing-cors#CORS) 
if you have trouble loading the file in your browser).

### Common problems
Though GitHub pages as host will work in Google Chrome, you may see a "decoding error" when serving your 
partial CSV file on GitHub pages to Firefox. The difference is due to a specification change that has not yet been 
implemented (see [open ticket](https://bugzilla.mozilla.org/show_bug.cgi?id=1467010)).

Many local development servers (eg Python SimpleHTTPServer) are not very robust, and do not support range 
requests at all. See [npm http-server](https://www.npmjs.com/package/http-server) for an example of one server that 
supports this feature.
 

## Acknowledgments
The bundled example file is public data courtesy of 
[DOHMH New York City Restaurant Inspection Results](https://data.cityofnewyork.us/Health/DOHMH-New-York-City-Restaurant-Inspection-Results/43nn-pn8j),
retrieved April 22, 2019.
