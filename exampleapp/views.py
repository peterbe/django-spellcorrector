from urllib import quote as url_quote
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render_to_response

from django.template import RequestContext


from spellcorrector.views import Spellcorrector, tokenize_text, remove_stopwords

spellcorrector_instance = Spellcorrector()
spellcorrector_instance.load()

from models import Document


def document_to_words(document):
    all_words = tokenize_text(document.title + ' ' + document.body)
    all_words = remove_stopwords(list(set(all_words)))
    return all_words
    
from django.db.models.signals import post_save, post_delete, pre_save



def train_on_document(sender, instance, created, **__):
    all_words = document_to_words(instance)
    spellcorrector_instance.train(all_words)
    spellcorrector_instance.save()
post_save.connect(train_on_document, sender=Document)


def untrain_on_document(sender, instance, **kwargs):
    all_words = document_to_words(instance)
    spellcorrector_instance.untrain(all_words)
    spellcorrector_instance.save()
post_delete.connect(untrain_on_document, sender=Document)


def retrain_all_documents(instance):
    """handy function for when you've fiddled too much with you model data with the
    risk of the train words not being up to date.
    Also, if you change a document, it will just train on the new stuff not 
    untrain on the old stuff. Admittedly, if you typed it once you're most 
    likely right the first time and that doesn't hurt to count.
    
    In a more realistic app you might want to put this under protection since
    it's a slow process and you don't want to allow anonymous calls dos your 
    site.
    """
    instance.reset()
    all_words = set()
    for document in Document.objects.all():
        all_words.update(document_to_words(document))
    instance.train(all_words)
    instance.save()
    

def documents(request):
    documents = Document.objects.all()
    if request.GET.get('q'):
        q = request.GET.get('q')
        q_corrected = spellcorrector_instance.correct(q)
        if q != q_corrected:
            documents = documents.filter(Q(title__icontains=q_corrected) \
                                       | Q(body__icontains=q_corrected))
        else:
            documents = documents.filter(Q(title__icontains=q) | Q(body__icontains=q))
            
        
    return render_to_response('documents.html', locals(),
                              context_instance=RequestContext(request))
    
def documents_a_la_google(request):
    """put in a link that says _Did you mean: *correction*_"""
    documents = Document.objects.all()
    if request.GET.get('q'):
        q = request.GET.get('q')
        documents = documents.filter(Q(title__icontains=q) | Q(body__icontains=q))
        
        corrected = spellcorrector_instance.correct(q)
        print "corrected", repr(corrected)
        if corrected != q:
            correction = {'query_string': url_quote(corrected),
                          'correction': corrected}
        
    return render_to_response('documents-a-la-google.html', locals(),
                              context_instance=RequestContext(request))