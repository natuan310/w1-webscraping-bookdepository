from bs4 import BeautifulSoup
from flask import Flask, render_template, url_for, redirect, request
import requests
import re

app = Flask(__name__)

base_url = 'https://www.bookdepository.com/'
search_url = 'https://www.bookdepository.com/search?searchTerm='

def get_url(url):
    r = requests.get(url)
    return BeautifulSoup(r.text, 'html.parser')


def crawl_bookrepo(url):
    soup = get_url(url)
    books = soup.find_all('div', class_='book-item')
    
    data = []
    for book in books:
        b = {'id': '', 'title': '', 'author': '', 'author_url': '',
             'price': '', 'img_url': '', 'link': ''}
        try:
            b['id'] = re.findall(r'\d{13}', book.a['href'])[0]
            b['title'] = book.img['alt']
            b['author'] = book.select_one('span[itemprop=name]').string
            b['author_url'] = book.select_one('a[itemprop=url]')['href'].replace('/author/', '')
            b['price'] = book.select_one('p[class=price]').string
            b['img_url'] = book.img['data-lazy']
            b['link'] = book.a['href']
        except:
            pass
        if b['price'] and b['img_url']:
            data.append(b)
    return data

def crawl_search(url):
    soup = get_url(url)
    books = soup.find_all('div', class_='book-item')
    
    data = []
    for book in books:
        b = {'id': '', 'title': '', 'author': '', 'author_url': '',
            'price': '', 'price-save': '', 'img_url': '', 'link': ''}
        # https://www.shareicon.net/data/256x256/2016/01/24/708046_document_512x512.png  uploading photo 
        try:
            b['id'] = re.findall(r'\d{13}', book.a['href'])[0]
            b['title'] = book.img['alt']
            b['author'] = book.select_one('a[itemprop=author]').get_text()
            b['author_url'] = book.select_one('a[itemprop=author]')[
                'href'].replace('/author/', '')
            b['price'] = book.select_one('p[class=price]').get_text().strip().split('\n                            \xa0')[0]
            b['price-save'] = b['price'] = book.select_one('p[class=price]').get_text().strip().split('\n                            \xa0')[1]
            b['img_url'] = book.img['data-lazy']
            if b['img_url'] == '':
                b['img_url'] = book.img['src']
            b['link'] = book.select_one('a[itemprop=url]')['href']
        except:
            pass
        if b['img_url']:
            data.append(b)
    return data

def crawl_category(url):
    soup = get_url(url)
    categories = soup.find_all('li', class_='top-category')
    category = []
    for cat in categories:
        c = {'category': '', 'cate_url': ''}
        c['category'] = cat.a.get_text().strip()
        c['cate_url'] = cat.a['href'][1:]
        if c['category'] and c['cate_url']:
            category.append(c)
    return category


def crawl_book_detail(url):
    soup = get_url(url)
    details = soup.find('div', class_='item-block')
    data = []
    d = {'title': '', 'author': '', 'price': '', 'img_url': '',
         'link': '', 'description': '', 'language': ''}
    d['title'] = details.img['alt']
    d['author'] = details.select_one('span[itemprop=author]')['itemscope']
    d['price'] = details.select_one('span[class=sale-price]').get_text()
    d['img_url'] = details.img['src']
    d['link'] = details.a['href']
    d['description'] = soup.find(itemprop='description').get_text()
    d['language'] = details.select_one('span[itemprop=inLanguage]').get_text()
    data.append(d)
    # for i in data:
    #     print(i)
    return data

category = crawl_category(base_url)

@app.route('/')
def index():
    books = crawl_bookrepo(base_url)
    # category = crawl_category(base_url)
    return render_template('index.html', books=books[:20], categories = category)


@app.route('/detail/<int:id>', methods=['POST', 'GET'])
def detail(id):
    print(id)
    # detail_url = base_url + '*/' + str(id)
    detail_url = base_url + '*/' + str(id)
    details = crawl_book_detail(detail_url)
    
    return render_template('book_details.html', details=details, categories=category)


@app.route('/author/<author>', methods=['POST', 'GET'])
def author(author):
    url = base_url + 'author/' + str(author)
    books = crawl_bookrepo(url)
    author_name = author.replace('-', ' ')
    return render_template('search_author.html', author_name=author_name, books=books, categories=category)

@app.route('/booktype/<path:btype>')
def booktype(btype):
    
    # category = crawl_category(base_url)
    if btype == 'bestsellers':
        cate = 'Bestsellers'
        url = 'https://www.bookdepository.com/bestsellers'
    elif btype == 'top-new-releases':
        cate = 'New Release'
        url = 'https://www.bookdepository.com/top-new-releases'
    elif btype == 'comingsoon':
        cate = 'Coming Soon'
        url = 'https://www.bookdepository.com/comingsoon'
    else:
        cate = btype[btype.rfind('/') + 1:].replace('-', ' ')
        url = base_url + str(btype)
    books = crawl_bookrepo(url)
    return render_template('search_type.html', cate=cate, books=books, categories=category)

@app.route('/navtype/<btype>')
def navtype(btype):
    # category = crawl_category(base_url)
    if btype == 'bestsellers':
        cate = 'Bestsellers'
        # url = 'https://www.bookdepository.com/bestsellers'
    elif btype == 'top-new-releases':
        cate = 'New Release'
        # url = 'https://www.bookdepository.com/top-new-releases'
    elif btype == 'comingsoon':
        cate = 'Coming Soon'
        # url = 'https://www.bookdepository.com/comingsoon'
    url = base_url + str(btype)
    books = crawl_search(url)
    return render_template('search_type.html', cate=cate, books=books, categories=category)

@app.route('/search', methods=['POST'])
def search():
    keyword = request.form['search']
    print(keyword)
    # https://www.bookdepository.com/search?searchTerm=Machine+LEArning&search=Find+book
    url = search_url + keyword.replace(' ', '+') + '&search=Find+book'
    books = crawl_bookrepo(url)
    cate = 'Search result for "%s"'%keyword
    return render_template('search_type.html', cate=cate, books=books[:20], categories = category)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
