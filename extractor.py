#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Extracts the main text content of online news articles using the density
sum algorithm.

TODO
====
- Write documentation

"""

import re

from lxml.etree import tostring
from lxml.html import document_fromstring
from lxml.html.clean import Cleaner
import matplotlib.pyplot as plt
import numpy as np

KILL_CSS_CLASSES = ['hidden', 'visually-hidden']

class NewsExtractor(object):
    """ DOC STRING"""

    def __init__(self, remove_class=None):
        self.cleaner = Cleaner(javascript=True, style=True, scripts=True,
                               comments=True, meta=True, embedded=True,
                               forms=True, processing_instructions=True)
        self.kill_css_classes = (remove_class if remove_class is not None else
                                 KILL_CSS_CLASSES)
        self.node_scores = None

    def extract(self, raw_html):
        """ Main function
        """
        body_elements = self.body_from_string(raw_html)
        nodes = self.split_nodes(body_elements)

        lc_b = self.count_link_chars(body_elements)
        c_b = self.count_chars(body_elements)

        self.node_scores = [self.calc_comp_density(node, lc_b, c_b) for node
                            in nodes]

        best_nodes_ix = self.get_best_nodes(self.node_scores)
        best_nodes = []
        for i, score in enumerate(self.node_scores):
            if score >= best_nodes_ix:
                best_nodes.append(i)

        content_nodes = [tostring(nodes[i].getparent()) for i in best_nodes]
        content = '\n\n'.join(content_nodes)
        return content

    def calc_comp_density(self, node, lc_b, c_b):
        """ Main algorithm function"""
        lc_b, c_b = float(lc_b), float(c_b)
        n_chars = self.count_chars(node)
        n_tags = self.count_tags(node)
        n_link_tags = self.count_link_tags(node)
        n_link_chars = self.count_link_chars(node)
        density = n_chars / n_tags
        end = (n_chars / n_link_chars) * (n_tags / n_link_tags)
        n_not_link_chars = n_chars - n_link_chars
        if n_not_link_chars <= 0:
            n_not_link_chars = 1
        base1 = (n_chars / n_not_link_chars) * n_link_chars
        base2 = (lc_b / c_b) * n_chars
        base = np.log(base1 + base2 + np.exp(1))
        ctd = density * self.log_n(end, base)
        if np.isnan(ctd):
            ctd = 0
        return ctd

    @staticmethod
    def get_best_nodes(scores):
        """ Implements a nearest neighbhor-style algorithm similar to decision
        trees to return the nodes.

        Minimize variance."""
        best_split = scores[0]
        best_variance = np.inf

        for score_i in scores:
            right = []
            left = []
            for score_j in scores:
                if score_j <= score_i:
                    right.append(score_j)
                else:
                    left.append(score_j)
            right_variance = np.var(right) / len(right)
            left_variance = np.var(left) / len(left)
            avg_variance = np.mean([right_variance, left_variance])
            if avg_variance < best_variance:
                best_variance = avg_variance
                best_split = score_i

        return best_split

    def body_from_string(self, raw_html):
        """ Converts string of HTML into lxml.html.HtmlElement and returns the
        body (without problematic CSS classes) for further manipulation."""

        def remove_css_class(css_class, html_element):
            """ Returns an lxml.html.HtmlElement object but with all elements
            of CSS class css_class removed."""
            for node in html_element.find_class(css_class):
                node.getparent().remove(node)
            return html_element

        cleaned = self.clean_html(raw_html)
        doc = document_fromstring(cleaned)
        body = doc.xpath('//body')[0]
        return [remove_css_class(css, body) for css in self.kill_css_classes]

    def plot(self):
        """ Plots node scores."""
        if self.node_scores is None:
            raise 'Extract text before plotting'
        else:
            plt.plot(self.node_scores)
            plt.xlabel('Nodes')
            plt.ylabel('Composite Text Density')
            plt.show()

    def clean_html(self, raw_html):
        """ Cleans HTML using lxml HTML cleaner and replaces all whitespace
        with a single space. """
        no_ws = self.remove_whitespace(raw_html)
        cleaned = self.cleaner.clean_html(no_ws)
        return cleaned

    def count_chars(self, html_element):
        """ Counts the characters in an lxml.html.HtmlElement. All whitespace
        characters are replaced by a single space."""
        no_ws = self.remove_whitespace(html_element.text_content())
        n_chars = len(no_ws)
        return float(n_chars)

    @staticmethod
    def count_tags(html_element):
        """ Counts the number of tags in an lxml.html.HtmlElement. Returns 1
        if no tags are present."""
        tag_count = len([node for node in html_element.iterdescendants()])
        if tag_count == 0:
            return 1.
        else:
            return float(tag_count)

    @staticmethod
    def count_link_tags(html_element):
        """ Counts the number of <a> tags in an lxml.html.HtmlElement. Returns
        1 if no tags are present."""
        link_tag_counts = len([node for node in html_element.iterlinks()])
        if link_tag_counts == 0:
            return 1.
        else:
            return float(link_tag_counts)

    @staticmethod
    def count_link_chars(html_element):
        """ Count the number of characters within an lxml.html.HtmlElement's
        <a> tags. Returns 1 if no tags are present."""
        link_chars = sum([len(node[0].text_content()) for node in
                          html_element.iterlinks()])
        if link_chars == 0:
            return 1.
        else:
            return float(link_chars)

    @staticmethod
    def remove_whitespace(raw_html):
        """clean_whitespace() function"""
        return re.sub(r'\s+', ' ', raw_html)

    @staticmethod
    def split_nodes(html_element):
        """ Splits an lxml.html.HtmlElement into a list of its HTML node
        descendants. Removes the initial element that contains all nodes."""
        nodes = [node for node in html_element.iterdescendants()]
        return nodes.pop(0)

    @staticmethod
    def log_n(x, base):
        """ Returns the log base b of x."""
        return np.log(x) / np.log(base)


if __name__ == '__main__':

    html = open('../density_sum/korea.html', 'r').read()

    extractor = NewsExtractor()
    content = extractor.extract(html)
    print(content)
    extractor.plot()

