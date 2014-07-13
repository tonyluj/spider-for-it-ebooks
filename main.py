#!/usr/bin/env python 
# 
# Copyright (C) 2014 copyright holder
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""
 This a spider for it-ebooks.

"""

import sqlite3
import requests
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool as ThreadPool

class Request:
    def __init__(self):
        self.original_url = 'http://it-ebooks.info/book/'

    def get_book_html(self, id):
        res = requests.get(self.original_url + str(id) + '/')
        print "get the " + str(id) + " book"
        return res.text


class DB:
    """ for sqlite3 db operation """
    def __init__(self, url):
        self.conn = sqlite3.connect(url) 

    def insert(self, info):
        c = self.conn.cursor()
        try:
            c.execute('insert into books values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     info)
            self.conn.commit()
        except:
            print "DB Error " + info[0]

    def close(self):
        self.conn.close()


class Books:
    """ book """
    def __init__(self, book_html = None):
        self.books = []
        if book_html != None:
            book_info = self.__get_book_info(book_html)    
            self.books.append(book_info)
    
    def add_book(self, book_html):
        self.books.append(self.__get_book_info(book_html))

    def add_books(self, book_html_list):
        """ add more than one books """
        pool = ThreadPool(4)
        results = pool.map(self.__get_book_info, book_html_list)
        self.books.extend(results)

    def get(self):
        return self.books.pop()

    def get_books(self):
        """ return all the books """
        return tuple(self.books)

    def __get_book_info(self, book_html):
        """ get book's info from html using BeautifulSoup 
        
            return a dict of book's info ordered by
            title, publisher, author, isbi, 
            year, pages, language, download_url, description
        """
        if book_html is None:
            return

        result = ()
        soup = BeautifulSoup(book_html)
        try: 
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
            
            book_info = [title]
            book_info.extend(extra_info)
            book_info.append(download_url)
            book_info.append(description)
            print "get a book named " + title
            result =  tuple(book_info)
        except TypeError:
            print "Counld not be None"
        except:
            print "Unknown error"
        finally:
            return result


class Spider:
    def __init__(self, start = 1, end = 3549):
        self.req = Request()
        self.db = DB('books.db')
        self.book = Books()
        self.start = start
        self.end = end

    def begin(self):
        print "start analysising..."
        books, order_list = self.__get_book_info()
        print "get all books' info"
        print "save to db..."
        self.__insert_into_db(books, order_list)
        print "done"

    def __get_book_info(self):
        pool = ThreadPool(4)
        order_list = xrange(self.start, self.end)
        results = pool.map(self.req.get_book_html, order_list)
        print "get all books' html"
        self.book.add_books(results)
        pool.close()
        pool.join()
        return tuple(self.book.get_books()), order_list

    def __insert_into_db(self, books, order_list):
        for book, order in zip(books, order_list):
            book_temp = list(book)
            book_temp.insert(0, order)
            self.db.insert(book_temp)
        self.db.close()

if __name__ == "__main__":
    spider = Spider(start = 1, end = 10)
    spider.begin()
