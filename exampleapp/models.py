import datetime
from django.db import models


class Document(models.Model):
    
    title = models.CharField(max_length=100)
    body = models.TextField()
    add_date = models.DateTimeField('date added', default=datetime.datetime.now)
    
    def __unicode__(self):
        return self.title[:20]
    
    
