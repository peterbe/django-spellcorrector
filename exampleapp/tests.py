from django.test import TestCase

from models import Document
from views import spellcorrector_instance, retrain_all_documents

class SimpleTest(TestCase):
    def test_adding_document(self):
        spellcorrector_instance.reset() # necessary because it's a global instance
        assert not spellcorrector_instance._trained_words
        
        # impossible to correct
        self.assertEqual(spellcorrector_instance.correct('totle'), 'totle')
        
        # add a document should add some new words to the spellcorrector
        document = Document.objects.create(title=u"Some title",
                                           body=u"Some document body")
        
        # now it should be loaded
        self.assertEqual(spellcorrector_instance.correct('totle'), 'title')
        self.assertEqual(spellcorrector_instance.correct('same'), 'some')
        
        # Change the document
        document.title = u"Different header"
        document.save()
        
        # that should have removed/untrained "Some title" and trained on
        # "Different header" instead
        # XXX: Unfortunately I don't know how to get rid of words that have
        # been removed. That's why this is commented out:
        #self.assertEqual(spellcorrector_instance.correct('totle'), 'totle')
        
        self.assertEqual(spellcorrector_instance.correct('heeder'), 'header')
        
    def test_searching_document(self):
        spellcorrector_instance.reset()
        
        # I've made a simple browse page
        response = self.client.get('/documents/')
        assert response.status_code == 200
        self.assertTrue('No documents yet' in response.content)
        
        # add some
        document1 = Document.objects.create(title=u"Some title",
                                            body=u"Some document body")

        document2 = Document.objects.create(title=u"Different title",
                                            body=u"This is different")

        
        response = self.client.get('/documents/')
        assert response.status_code == 200
        self.assertTrue('No documents yet' not in response.content)
        
        self.assertTrue('Some title' in response.content)
        self.assertTrue('Different title' in response.content)
        
        # search for something that only 1 can be found
        
        response = self.client.get('/documents/?q=Some')
        assert response.status_code == 200
        self.assertTrue('Some title' in response.content)
        self.assertTrue('Different title' not in response.content)

        response = self.client.get('/documents/?q=different')
        assert response.status_code == 200
        self.assertTrue('Some title' not in response.content)
        self.assertTrue('Different title' in response.content)

        # now it should be possible to get the same results with
        # the search query being mispelled.
        response = self.client.get('/documents/?q=Somme')
        assert response.status_code == 200
        self.assertTrue('Some title' in response.content)
        self.assertTrue('Different title' not in response.content)
        self.assertTrue('assuming you meant' in response.content and\
                        'some' in response.content)

        response = self.client.get('/documents/?q=diferent')
        assert response.status_code == 200
        self.assertTrue('Some title' not in response.content)
        self.assertTrue('Different title' in response.content)
        self.assertTrue('assuming you meant' in response.content and\
                        'different' in response.content)
        
        
    def test_retrain_all_documents(self):
        """the function retrain_all_documents() resets the spellcorrector
        and retrains on all existing documents."""
        spellcorrector_instance.reset()
        
        assert not spellcorrector_instance._trained_words
        assert not Document.objects.all().count()
        
        # you can run it without having any documents
        retrain_all_documents(spellcorrector_instance)
        
        spellcorrector_instance.train(u'Peter')
        self.assertEqual(spellcorrector_instance._trained_words, [u'peter'])
        retrain_all_documents(spellcorrector_instance)
        self.assertEqual(spellcorrector_instance._trained_words, [])
        