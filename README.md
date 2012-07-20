# Friend Graph Crawler 

A tool to crawl Facebook friend lists to construct as much of a "hidden"
person's social network as possible without their friends list being publicly
visible.

## Description

This code was written to answer the question, "how much of my friend graph
could someone who doesn't know me construct?"

Imagine a third party, Eve, views the friends list of my close friend, Alice
(either because Alice's friends list is public or because Eve and Alice are
friends). Eve could determine that Alice and I are friends, and has therefore
found one piece of my friends list, *despite my friends list being hidden*.

This script takes the place of Eve viewing many friends lists in a fairly
small graph with the aim of trying to construct as much of my friends list
as she can. Results are printed out as a DOT file (see
[Graphviz](http://www.graphviz.org/) if you aren't familiar).

This does not use the Facebook Open Graph API, since that requires this being
treated as an "app" where each user gives permission for that app to view its
friends list. This would defeat the purpose of answering the question.

## How to use

This script has several options that are briefly described by running:

    python crawler.py --help

Note that several of them are required to get started.

## Dependencies

As listed in `requirements.txt`, this project depends on `requests` and
`python-memcached`. You can ensure you have the requirements by executing the
following:

    pip install -r requirements.txt

## License

Copyright (c) 2012 Jesse Gunsch

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
