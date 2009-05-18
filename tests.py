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
        
        
    def test_spellcorrector_basic(self):
        """test the Spellcorrector class without loading or saving"""
        
        sc = views.Spellcorrector()
        
        sc.train('peter')
        self.assertEqual(sc.correct('peter'), 'peter')
        self.assertEqual(sc.correct('petter'), 'peter')
        
        sc.train('petter')
        # 'petter' is newer but 'peter' was trained on deliberately
        self.assertEqual(sc.correct('peter'), 'peter')
        # should definitely not be corrected
        self.assertEqual(sc.correct('petter'), 'petter')
        
        # 2 edit distances from 'petter' but 1 from 'peter'
        self.assertEqual(sc.suggestions('peterr'), ['peter'])
        
        # 1 edit distaince from 'petter'
        self.assertEqual(sc.suggestions('petterr'), ['petter'])
        
        # for the curious type
        self.assertEqual(sc.suggestions('eter', detailed=True), 
          [{'count': 1, 'percentage': 100.0, 'word': u'peter'}])
        
        self.assertEqual(sc.count_trained_words(), 2)
        
    def test_spellcorrector_swedish(self):
        """test the Spellcorrector class without loading or saving and
        don't use the English alphabet"""
        
        sc = views.Spellcorrector(language='sv')
        # by the language it's able to guess the alphabet
        self.assertEqual(len(sc.alphabet), 26+3)
        self.assertTrue(u'\xe5' in sc.alphabet)
        self.assertTrue(u'\xe4' in sc.alphabet)
        self.assertTrue(u'\xf6' in sc.alphabet)
        
        sc.train(u'r\xe5d')
        self.assertEqual(sc.correct('rad'), u'r\xe5d')
        sc.train(u'r\xf6d')
        # ambiguous! There is no reason u'r\xe5d' is any better than u'r\xf6d'
        self.assertEqual(sc.correct('rad'), u'rad') # fall back
        
        
    def test_spellcorrector_loading_basic(self):
        """test the Spellcorrector after loading from the database"""
        
        sc = views.Spellcorrector()
        # when not trained on anything it won't get this right
        self.assertEqual(sc.correct('petxr'), 'petxr')
        
        Word.objects.create(word='peter', count=1, 
                            language=sc.language)
        
        sc.load()
        self.assertEqual(sc.correct('petxr'), 'peter')
        
        # spellcorrecting the word 'petxr' would be ambiguous with
        # the loaded 'peter' but if we have since loading trained
        # on a new "more important" word 'petxa' then that wins
        sc.train(u'petxa')
        self.assertEqual(sc.correct('petxr'), 'petxa')
        

    def test_spellcorrector_saving_basic(self):
        """test the Spellcorrector after saving to the database and loading
        which should be able to pick up from previous sessions"""
        
        
        sc = views.Spellcorrector()
        
        # when not trained on anything it won't get this right
        self.assertEqual(sc.correct('petxr'), 'petxr')
        # it won't help if we load
        sc.load()
        self.assertEqual(sc.correct('petxr'), 'petxr')
        
        
        # but if we train on it should work
        sc.train('peter')
        self.assertEqual(sc.correct('petxr'), 'peter')
        
        # now save it
        sc.save()
        
        # create new instance
        sc2 = views.Spellcorrector()
        # totally new blank
        self.assertEqual(sc2.correct('petxr'), 'petxr')
        # but should work if we load
        sc2.load()
        self.assertEqual(sc2.correct('petxr'), 'peter')
        
        
    def test_spellcorrector_untrain(self):
        """you reverse trained words by untraining"""
        
        sc = views.Spellcorrector()
        
        # first it can do nothing
        self.assertEqual(sc.correct('petxr'), 'petxr')
        
        sc.train(u'peter')
        self.assertEqual(sc.correct('petxr'), 'peter')
        
        # change your mind
        sc.untrain(u'peter')
        self.assertEqual(sc.correct('petxr'), 'petxr')
        
        # but if you train a word more than once, 
        # untraining only means that you're going to remove it a little
        
        # first it can't know
        self.assertEqual(sc.correct('bangt'), 'bangt')
        sc.train(u'bengt')
        sc.train(u'bengt')
        sc.train(u'bang')
        self.assertEqual(sc.correct('bangt'), 'bengt')
        # but if we untrain, we don't know if it should 'bang' or 'bengt'
        sc.untrain(u'bengt')
        self.assertEqual(sc.correct('bangt'), 'bangt')
        sc.untrain(u'bengt')
        self.assertEqual(sc.correct('bangt'), 'bang')
        
        

        

        
        

        
        
        
