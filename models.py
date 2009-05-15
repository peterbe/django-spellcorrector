from django.db import models

# Create your models here.

class Word(models.Model):
    word = models.CharField(max_length=40)
    count = models.IntegerField(default=1)
    language = models.CharField(max_length=5, default='en')
    
    def __unicode__(self):
        return self.word
    
#    def __init__(self, *args, **kwargs):
#        super(Word, self).__init__(*args, **kwargs)
    
    @staticmethod
    def get_count(word, language='en'):
        try:
            return Word.objects.get(word=word.lower(), language=language).count
        except Word.DoesNotExist:
            return 0
        
    @staticmethod
    def set_word(word, count, language='en'):
        try:
            word = Word.objects.get(word=word.lower(), language=language)
        except Word.DoesNotExist:
            word = Word.objects.create(word=word.lower(), language=language)
        if word.count != count:
            word.count = count
            word.save()
    
        
    
