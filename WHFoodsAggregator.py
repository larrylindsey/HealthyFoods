from HTMLParser import HTMLParser
from httplib import HTTPConnection

class IndexParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.__food_page_map = dict()
        self.__ahref = False
        self.__current_link = ''

    def handle_starttag(self, tag, attrs):
        # attrs come in as a list of tuples like (key, value). Convert it into a dict
        attr_dict = dict(attr for attr in attrs)

        if tag == 'ul' and 'class' in attr_dict and attr_dict['class'] == 'blist':
            self.__ahref = True
        elif self.__ahref and tag == 'a' and 'href' in attr_dict:
            self.__current_link = attr_dict['href']

    def handle_endtag(self, tag):
        if tag == 'ul':
            self.__ahref = False

    def handle_data(self, data):
        if data.strip() and self.__ahref and self.__current_link:
            self.__food_page_map[data] = self.__current_link
            self.__current_link = ''

    def get_link_table(self):
        return self.__food_page_map


class FoodParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.__in_table = False

        self.__nutrient_table = dict()
        self.__nutrient_row = dict()
        self.__header_table = dict()

        self.__nutrient_key = ''
        self.__next_nutrient_key = {'name': 'amount',
                                    'amount': 'dri/dv',
                                    'dri/dv': 'density',
                                    'density': 'rating',
                                    'rating': '',
                                    '': ''}

        self.__header_key = ''
        self.__next_header_key = {'name': 'size',
                                  'size': 'weight',
                                  'weight': 'calories',
                                  'calories': 'GI',
                                  'GI': '',
                                  '': ''}

    def handle_starttag(self, tag, attrs):
        # attrs come in as a list of tuples like (key, value). Convert it into a dict
        attr_dict = dict(attr for attr in attrs)

        if not self.__in_table:
            if tag == "td" and 'bgcolor' in attr_dict:
                self.__in_table = True
                self.__header_key = 'name'
        else:
            if tag == 'tr' and 'style' in attr_dict and attr_dict['style'].startswith('background-color'):
                self.__nutrient_key = 'name'
                self.__nutrient_row = dict()

    def handle_data(self, data):
        if self.__nutrient_key is not '':
            if self.__nutrient_key == 'name':
                self.__nutrient_table[data] = self.__nutrient_row
                print data

            self.__nutrient_row[self.__nutrient_key] = data
            self.__nutrient_key = self.__next_nutrient_key[self.__nutrient_key]
        elif self.__header_key is not '':
            self.__header_table[self.__header_key] = data
            self.__header_key = self.__next_header_key[self.__header_key]

    def get_nutrient_table(self):
        return self.__nutrient_table

    def get_header_table(self):
        return self.__header_table


class Aggregator:
    def __init__(self):
        self.__nutrition_table = dict()
        self.__index_page = '/foodstoc.php'
        self.__server = 'www.whfoods.com'
        self.__hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
                      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                      'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                      'Accept-Encoding': 'none',
                      'Accept-Language': 'en-US,en;q=0.8',
                      'Connection': 'keep-alive'}
        self.__conn = None

    def __read_url(self, page):
        self.__conn.request('GET', page, headers=self.__hdr)
        res = self.__conn.getresponse()
        if res.status is not 200:
            raise Exception('Well, shit: ' + res.reason)
        return res.read()

    def go(self):
        index_parser = IndexParser()
        self.__conn = HTTPConnection(self.__server)
        index_parser.feed(self.__read_url(self.__index_page))

        link_table = index_parser.get_link_table()

        for food in link_table:
            food_parser = FoodParser()
            food_parser.feed(self.__read_url('/' + link_table[food]))
            food_dict = dict()
            self.__nutrition_table[food] = food_dict

            food_dict['header'] = food_parser.get_header_table()
            food_dict['nutrition'] = food_parser.get_nutrient_table()

        self.__conn.close()

    def get_nutrition_table(self):
        return self.__nutrition_table


