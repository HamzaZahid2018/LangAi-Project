import os
import json
import pymupdf
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

from .models import Document, EditHistory, PlagiarismResult
from .forms import DocumentForm, TextProcessForm
from .ai_engine import (
    check_grammar, translate_text, check_plagiarism,
    summarize_text, SUPPORTED_LANGUAGES
)

# Get Groq API key from environment variable (secure - no hardcoding)
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')


def landing_view(request):
    """Landing page for unauthenticated users"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'editor/landing.html')


def trial_editor_view(request):
    """Trial users use the same editor but with limited features"""
    return editor_view(request, is_trial=True)


@login_required
def dashboard_view(request):
    """User dashboard with statistics and activity"""
    user = request.user
    now = timezone.now()
    
    # Stats
    total_docs = Document.objects.filter(user=user).count()
    total_edits = EditHistory.objects.filter(user=user).count()
    today_edits = EditHistory.objects.filter(user=user, created_at__date=now.date()).count()
    week_edits = EditHistory.objects.filter(user=user, created_at__gte=now - timedelta(days=7)).count()

    # Operation breakdown
    ops = EditHistory.objects.filter(user=user).values('operation').annotate(count=Count('id'))
    op_data = {o['operation']: o['count'] for o in ops}

    # Recent activity
    recent_history = EditHistory.objects.filter(user=user).select_related('document')[:8]
    recent_docs = Document.objects.filter(user=user)[:5]

    context = {
        'total_docs': total_docs,
        'total_edits': total_edits,
        'today_edits': today_edits,
        'week_edits': week_edits,
        'op_data': json.dumps(op_data),
        'recent_history': recent_history,
        'recent_docs': recent_docs,
    }
    return render(request, 'editor/dashboard.html', context)


def editor_view(request, is_trial=False):
    """Main AI editor interface with text processing operations"""
    # If not authenticated and not explicitly in trial mode, redirect to landing
    if not request.user.is_authenticated and not is_trial:
        return redirect('landing')

    trial_remaining = None
    form = TextProcessForm()
    result = None
    active_op = None

    if request.method == 'POST':
        form = TextProcessForm(request.POST)

        if form.is_valid():
            text = form.cleaned_data['text']
            operation = form.cleaned_data['operation']
            active_op = operation

            if operation == 'grammar':
                result = check_grammar(text)
                op_label = 'grammar'

            elif operation == 'translate':
                target = form.cleaned_data['target_language']
                result = translate_text(text, target)
                op_label = 'translate'

            elif operation == 'plagiarism':
                if request.user.is_authenticated:
                    docs = Document.objects.exclude(user=request.user)
                else:
                    docs = Document.objects.all()
                result = check_plagiarism(text, list(docs))
                if result.get('success') and request.user.is_authenticated:
                    PlagiarismResult.objects.create(
                        user=request.user,
                        input_text=text,
                        similarity_score=result['similarity_score'],
                        is_plagiarized=result['is_plagiarized'],
                        details=result.get('details', []),
                    )
                op_label = 'plagiarism'

            elif operation == 'summarize':
                sentences = form.cleaned_data.get('sentences', 3)
                result = summarize_text(text, sentences)
                op_label = 'summarize'

            # Save to history if logged in
            if request.user.is_authenticated:
                # Extract output text properly based on operation and result type
                output_text = None
                
                if isinstance(result, dict):
                    if operation == 'grammar':
                        output_text = result.get('corrected') or result.get('original') or ''
                    elif operation == 'translate':
                        output_text = result.get('translated') or ''
                    elif operation == 'plagiarism':
                        output_text = f"Similarity: {result.get('similarity_score', 0)}%"
                    elif operation == 'summarize':
                        output_text = result.get('summary') or ''
                    else:
                        output_text = json.dumps(result)
                else:
                    output_text = str(result) if result else ''
                
                # Only save if output_text is not None/empty
                if output_text and output_text.strip():
                    EditHistory.objects.create(
                        user=request.user,
                        operation=operation,
                        input_text=text,
                        output_text=output_text,
                        metadata=result if isinstance(result, dict) else {},
                    )

    context = {
        'form': form,
        'result': result,
        'active_op': active_op,
        'is_trial': is_trial,
        'trial_remaining': trial_remaining,
        'supported_languages': SUPPORTED_LANGUAGES,
    }
    return render(request, 'editor/editor.html', context)


@login_required
def history_view(request):
    """User's operation history"""
    user = request.user
    history = EditHistory.objects.filter(user=user).select_related('document')
    
    context = {'history': history}
    return render(request, 'editor/history.html', context)


@login_required
def my_documents_view(request):
    """User's saved documents"""
    user = request.user
    documents = Document.objects.filter(user=user)
    
    context = {'documents': documents}
    return render(request, 'editor/my_documents.html', context)


@login_required
def save_document(request):
    """Save document from editor"""
    if request.method == 'POST':
        form = DocumentForm(request.POST)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.user = request.user
            doc.save()
            messages.success(request, 'Document saved successfully!')
            return redirect('document_saved', pk=doc.pk)
    else:
        form = DocumentForm()
    
    return render(request, 'editor/save_document.html', {'form': form})


@login_required
def document_saved_view(request, pk):
    """Show confirmation after document saved"""
    document = get_object_or_404(Document, pk=pk, user=request.user)
    return render(request, 'editor/document_saved.html', {'document': document})


@login_required
def download_document(request, pk):
    """Download document as TXT"""
    document = get_object_or_404(Document, pk=pk, user=request.user)
    response = HttpResponse(document.content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{document.title}.txt"'
    return response


@login_required
def download_document_pdf(request, pk):
    """Download document as PDF"""
    document = get_object_or_404(Document, pk=pk, user=request.user)
    
    try:
        doc = pymupdf.open()
        page = doc.new_page()
        
        # RTL detection for Arabic/Urdu
        rtl_langs = ['ar', 'ur']
        is_rtl = document.language in rtl_langs
        
        page.insert_text(
            (50, 50),
            f"{document.title}\n\n{document.content}",
            fontsize=11,
        )
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{document.title}.pdf"'
        doc.write(response)
        return response
    except Exception as e:
        messages.error(request, f'Error generating PDF: {str(e)}')
        return redirect('my_documents')


@login_required
def delete_document(request, pk):
    """Delete a document"""
    document = get_object_or_404(Document, pk=pk, user=request.user)
    
    if request.method == 'POST':
        document.delete()
        messages.success(request, 'Document deleted!')
        return redirect('my_documents')
    
    return render(request, 'editor/document_saved.html', {'document': document, 'delete_mode': True})


@login_required
def process_document(request):
    """Upload and process document files (PDF, DOCX, TXT)"""
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        content = ''
        
        try:
            if file.name.endswith('.pdf'):
                pdf = pymupdf.open(stream=file.read(), filetype='pdf')
                content = ''.join([page.get_text() for page in pdf])
            elif file.name.endswith('.txt'):
                content = file.read().decode('utf-8')
            elif file.name.endswith('.docx'):
                import docx2txt
                content = docx2txt.process(file)
            else:
                messages.error(request, 'Unsupported file type')
                return redirect('process_document')
            
            context = {'content': content, 'filename': file.name}
            return render(request, 'editor/process_document.html', context)
        
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
            return redirect('process_document')
    
    return render(request, 'editor/process_document.html')


@csrf_exempt
@login_required
def save_result_as_document(request):
    """AJAX endpoint to save operation result as document"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            doc = Document.objects.create(
                user=request.user,
                title=data.get('title', 'Untitled'),
                content=data.get('content', ''),
                language=data.get('language', 'en'),
            )
            return JsonResponse({'success': True, 'id': doc.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False}, status=405)


@csrf_exempt
def transcribe_audio(request):
    """Transcribe audio using Groq Whisper API with fallbacks"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'})
    
    try:
        # Get audio file from request
        audio_file = request.FILES.get('audio')
        if not audio_file:
            return JsonResponse({'status': 'error', 'message': 'No audio file provided'})
        
        # Try Groq API if key is available
        if GROQ_API_KEY:
            try:
                import requests
                files = {'file': ('audio.webm', audio_file.read(), 'audio/webm')}
                headers = {'Authorization': f'Bearer {GROQ_API_KEY}'}
                response = requests.post(
                    'https://api.groq.com/openai/v1/audio/transcriptions',
                    files=files,
                    headers=headers,
                    data={'model': 'whisper-large-v3-turbo'}
                )
                if response.status_code == 200:
                    return JsonResponse({
                        'status': 'success',
                        'text': response.json().get('text', '')
                    })
            except Exception as e:
                print(f"Groq API failed: {e}")
        
        # Fallback: Try local Whisper or Google Speech Recognition
        return JsonResponse({
            'status': 'error',
            'message': 'Transcription service unavailable. Configure GROQ_API_KEY in .env'
        })
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
def save_speech_history(request):
    """Save speech transcription to history"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            EditHistory.objects.create(
                user=request.user,
                operation='speech',
                input_text='[Speech Input]',
                output_text=data.get('text', ''),
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False}, status=405)


@login_required
def export_result(request):
    """Export operation result"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            content = data.get('content', '')
            format_type = data.get('format', 'txt')
            
            if format_type == 'pdf':
                doc = pymupdf.open()
                page = doc.new_page()
                page.insert_text((50, 50), content, fontsize=11)
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="export.pdf"'
                doc.write(response)
                return response
            else:
                response = HttpResponse(content, content_type='text/plain')
                response['Content-Disposition'] = 'attachment; filename="export.txt"'
                return response
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False}, status=405)
