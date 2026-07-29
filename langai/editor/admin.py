from django.contrib import admin
from .models import Document, EditHistory, PlagiarismResult
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display  = ('title', 'user', 'language', 'word_count', 'created_at')
    list_filter   = ('language', 'created_at')
    search_fields = ('title', 'user__username', 'content')


@admin.register(EditHistory)
class EditHistoryAdmin(admin.ModelAdmin):
    list_display  = ('operation', 'user', 'created_at')
    list_filter   = ('operation', 'created_at')
    search_fields = ('user__username',)


@admin.register(PlagiarismResult)
class PlagiarismResultAdmin(admin.ModelAdmin):
    list_display  = ('user', 'similarity_score', 'is_plagiarized', 'created_at')
    list_filter   = ('is_plagiarized',)