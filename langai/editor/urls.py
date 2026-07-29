from django.urls import path
from . import views

urlpatterns = [
    path('',                          views.editor_view,              name='editor'),
    path('trial/',                    views.trial_editor_view,        name='trial'),
    path('dashboard/',                views.dashboard_view,           name='dashboard'),
    path('history/',                  views.history_view,             name='history'),
    path('save/',                     views.save_document,            name='save_document'),
    path('saved/<int:pk>/',           views.document_saved_view,      name='document_saved'),
    path('documents/',                views.my_documents_view,        name='my_documents'),
    path('download/<int:pk>/txt/',    views.download_document,        name='download_document'),
    path('download/<int:pk>/pdf/',    views.download_document_pdf,    name='download_document_pdf'),
    path('delete/<int:pk>/',          views.delete_document,          name='delete_document'),
    path('speech/save/',              views.save_speech_history,      name='save_speech'),
    path('speech/transcribe/',        views.transcribe_audio,         name='transcribe_audio'),
    path('document/',                 views.process_document,         name='process_document'),
    path('export/',                   views.export_result,            name='export_result'),
    path('save-result/',              views.save_result_as_document,  name='save_result_as_document'),
]