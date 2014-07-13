#!/usr/bin/env python 
# 
# Copyright (C) 2014 copyright holder
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
 This a spider for it-ebooks.

"""

import sqlite3
import requests
from bs4 import BeautifulSoup

class Request:
    def __init__(self):
        self.original_url = 'http://it-ebooks.info/book/'

    def get_book_html(self, id):
        res = requests.get(self.original_url + str(id) + '/')
        return res.text


class DB:
    """ for sqlite3 db operation """
    def __init__(self, url):
        self.conn = sqlite3.connect(url) 

    def insert(self, info, id):
        c = self.conn.cursor()
        book_info = list(info)
        book_info.insert(0, id)
        c.execute('insert into books values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                 book_info)
        self.conn.commit()

    def close(self):
        self.conn.close()


class Books:
    """ book """
    def __init__(self, book_html = None):
        self.books = []
        if book_html != None:
            book_info = self.__get_book_info(book_html)    
            self.books.append(book_info)
    
    def add(self, book_html):
        self.books.append(self.__get_book_info(book_html))

    def get(self):
        return self.books.pop()

    def __get_book_info(self, book_html):
        """ get book's info from html using BeautifulSoup 
        
            return a dict of book's info ordered by
            title, publisher, author, isbi, 
            year, pages, language, download_url, description
        """
        if book_html is None:
            return

        soup = BeautifulSoup(book_html)
    
        # publisher, by, isbn, year, pages, language
        content = []
        for item in soup.find_all('b')[4:11]:
            content.append(item.string)
        extra_info = []
        extra_info.append(content[0])
        extra_info.extend(content[2:])
    
        # title
        title = soup.title.string.split('-')[0].strip()
    
        # download url
        download_url = ''
        for item in soup.find_all('a'):
            if item.string == title:
                download_url = item.get('href')
                break
    
        # description
        description = soup.span.text
        
        # dict of book's info
        # book_info = dict([['title', title],['publisher', book_info[0]],
        #                 ['author', book_info[1]],['isbn', book_info[2]],
        #                 ['year', book_info[3]],
        #                 ['pages', book_info[4]],
        #                 ['language', book_info[5]],
        #                 ['download_url', download_url],
        #                 ['description', description]])
        book_info = [title]
        book_info.extend(extra_info)
        book_info.append(download_url)
        book_info.append(description)

        return tuple(book_info)


if __name__ == "__main__":
    req = Request()
    db = DB('books.db')
    book = Books()

    for i in xrange(1, 100):
       book_html = req.get_book_html(i)
       book.add(book_html)
       book_info = book.get()
       db.insert(book_info, i)
       print "added " + str(i) + " book, name: " + book_info[0]
    db.close()
