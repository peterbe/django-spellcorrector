from django.contrib import admin
from models import Document

class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title','add_date')
    ordering = ('add_date',)


admin.site.register(Document, DocumentAdmin)
