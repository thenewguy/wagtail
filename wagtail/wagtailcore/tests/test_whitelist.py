from bs4 import BeautifulSoup

from django.test import TestCase
from wagtail.wagtailcore.whitelist import (
    check_url,
    attribute_rule,
    allow_without_attributes,
    Whitelister
)

class TestCheckUrl(TestCase):
    def test_allowed_url_schemes(self):
        for url_scheme in ['', 'http', 'https', 'ftp', 'mailto', 'tel']:
            url = url_scheme + "://www.example.com"
            self.assertTrue(bool(check_url(url)))

    def test_disallowed_url_scheme(self):
        self.assertFalse(bool(check_url("invalid://url")))


class TestAttributeRule(TestCase):
    def setUp(self):
        self.soup = BeautifulSoup('<b foo="bar">baz</b>')

    def test_no_rule_for_attr(self):
        """
        Test that attribute_rule() drops attributes for
        which no rule has been defined.
        """
        tag = self.soup.b
        fn = attribute_rule({'snowman': 'barbecue'})
        fn(tag)
        self.assertEqual(str(tag), '<b>baz</b>')

    def test_rule_true_for_attr(self):
        """
        Test that attribute_rule() does not change atrributes
        when the corresponding rule returns True
        """
        tag = self.soup.b
        fn = attribute_rule({'foo': True})
        fn(tag)
        self.assertEqual(str(tag), '<b foo="bar">baz</b>')

    def test_rule_false_for_attr(self):
        """
        Test that attribute_rule() drops atrributes
        when the corresponding rule returns False
        """
        tag = self.soup.b
        fn = attribute_rule({'foo': False})
        fn(tag)
        self.assertEqual(str(tag), '<b>baz</b>')

    def test_callable_called_on_attr(self):
        """
        Test that when the rule returns a callable,
        attribute_rule() replaces the attribute with
        the result of calling the callable on the attribute.
        """
        tag = self.soup.b
        fn = attribute_rule({'foo': len})
        fn(tag)
        self.assertEqual(str(tag), '<b foo="3">baz</b>')

    def test_callable_returns_None(self):
        """
        Test that when the rule returns a callable,
        attribute_rule() replaces the attribute with
        the result of calling the callable on the attribute.
        """
        tag = self.soup.b
        fn = attribute_rule({'foo': lambda x: None})
        fn(tag)
        self.assertEqual(str(tag), '<b>baz</b>')

    def test_allow_without_attributes(self):
        """
        Test that attribute_rule() with will drop all
        attributes.
        """
        soup = BeautifulSoup('<b foo="bar" baz="quux" snowman="barbecue"></b>')
        tag = soup.b
        allow_without_attributes(tag)
        self.assertEqual(str(tag), '<b></b>')


class TestWhitelister(TestCase):
    def test_clean_unknown_node(self):
        """
        Unknown node should remove a node from the parent document
        """
        soup = BeautifulSoup('<foo><bar>baz</bar>quux</foo>')
        tag = soup.foo
        Whitelister.clean_unknown_node('', soup.bar)
        self.assertEqual(str(tag), '<foo>quux</foo>')

    def test_clean_tag_node_cleans_nested_recognised_node(self):
        """
        <b> tags are allowed without attributes. This remains true
        when tags are nested.
        """
        soup = BeautifulSoup('<b><b class="delete me">foo</b></b>')
        tag = soup.b
        Whitelister.clean_tag_node(tag, tag)
        self.assertEqual(str(tag), '<b><b>foo</b></b>')

    def test_clean_tag_node_disallows_nested_unrecognised_node(self):
        """
        <foo> tags should be removed, even when nested.
        """
        soup = BeautifulSoup('<b><foo>bar</foo></b>')
        tag = soup.b
        Whitelister.clean_tag_node(tag, tag)
        self.assertEqual(str(tag), '<b>bar</b>')

    def test_clean_string_node_does_nothing(self):
        soup = BeautifulSoup('<b>bar</b>')
        string = soup.b.string
        Whitelister.clean_string_node(string, string)
        self.assertEqual(str(string), 'bar')

    def test_clean_node_does_not_change_navigable_strings(self):
        soup = BeautifulSoup('<b>bar</b>')
        string = soup.b.string
        Whitelister.clean_node(string, string)
        self.assertEqual(str(string), 'bar')

    def test_clean(self):
        """
        Whitelister.clean should remove disallowed tags and attributes from
        a string
        """
        string = '<b foo="bar">snowman <barbecue>Yorkshire</barbecue></b>'
        cleaned_string = Whitelister.clean(string)
        self.assertEqual(cleaned_string, '<b>snowman Yorkshire</b>')
