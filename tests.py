"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from models import Word

import views 

class SimpleTest(TestCase):
    def test_adding_words(self):
        """when adding a word it doesn't have to exist.
        but if it does, increment it. It will always be stored in 
        lower case.
        """
        
        assert Word.objects.filter(word='foo').count() == 0
        views.incr_word('foo')
        assert Word.objects.filter(word='foo').count() == 1
        assert Word.objects.get(word='foo').count == 1
        
        views.incr_word('Foo')
        assert Word.objects.filter(word='foo').count() == 1
        assert Word.objects.get(word='foo').count == 2
        
        # but you can split it by different languages
        views.incr_word('foo', language='es')
        assert Word.objects.filter(word='foo', language='es').count() == 1
        assert Word.objects.get(word='foo', language='es').count == 1
        
    def test_removing_words(self):
        """removing words is as simple as adding. 
        It's case insensitive and defaults to language en
        """
        assert Word.objects.filter(word='foo').count() == 0
        # if you try to decrement a word that doesn't exist
        # it doesn't barf
        views.decr_word('foo')
        assert Word.objects.filter(word='foo').count() == 0
        
        # add some
        views.incr_word('foo')
        views.incr_word('bar')
        views.incr_word('foo')
        
        assert Word.objects.get(word='foo').count == 2
        assert Word.objects.get(word='bar').count == 1
        
        views.decr_word('FOo')
        assert Word.objects.get(word='foo').count == 1
        
        views.decr_word('BaR')
        
        assert Word.objects.filter(word='bar').count() == 0
        
    def test_static_class_method_get_count(self):
        """the static class method Word.get_count() makes it possible to 
        conveiently ask the model for a count."""
        # defaults to 0 when it doesn't exist
        self.assertEqual(Word.get_count('foo'), 0)
        self.assertEqual(Word.get_count('foo', language='es'), 0)
        
        views.incr_word('foo')
        self.assertEqual(Word.get_count('foo'), 1)
        self.assertEqual(Word.get_count('foo', language='es'), 0)
        
        views.incr_word('foo', language='es')
        self.assertEqual(Word.get_count('foo'), 1)
        self.assertEqual(Word.get_count('foo', language='es'), 1)
        
    def test_tokenize_text(self):
        """it should split on real words"""
        func = views.tokenize_text
        
        self.assertEqual(func('peter bengtsson'),
                         ['peter', 'bengtsson'])
        
        self.assertEqual(func('peter (bracket) bengtsson'),
                         ['peter', 'bracket', 'bengtsson'])        
        
        self.assertEqual(func('  peter \tbengtsson  '),
                         ['peter', 'bengtsson'])
        
        
        

        
        
        
