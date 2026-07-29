from django.db import models
from django.contrib.auth.models import User


class Document(models.Model):
    LANGUAGE_CHOICES = [
        ('en', 'English'), ('ur', 'Urdu'), ('ar', 'Arabic'),
        ('fr', 'French'), ('es', 'Spanish'), ('de', 'German'),
        ('zh-CN', 'Chinese'), ('hi', 'Hindi'), ('pt', 'Portuguese'),
        ('ru', 'Russian'), ('tr', 'Turkish'),
    ]

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    title      = models.CharField(max_length=200)
    content    = models.TextField()
    language   = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} ({self.user.username})"

    def word_count(self):
        return len(self.content.split())

    def char_count(self):
        return len(self.content)


class EditHistory(models.Model):
    OPERATION_CHOICES = [
        ('translate',   ' Translation'),
        ('grammar',     ' Grammar Check'),
        ('plagiarism',  ' Plagiarism Check'),
        ('summarize',   ' Summarization'),
        ('speech',      ' Speech to Text'),
    ]

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='edit_history')
    document   = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True)
    operation  = models.CharField(max_length=20, choices=OPERATION_CHOICES)
    input_text = models.TextField()
    output_text = models.TextField()
    metadata   = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_operation_display()} by {self.user.username}"

    def truncated_input(self):
        return self.input_text[:80] + '...' if len(self.input_text) > 80 else self.input_text


class PlagiarismResult(models.Model):
    user             = models.ForeignKey(User, on_delete=models.CASCADE)
    input_text       = models.TextField()
    similarity_score = models.FloatField(default=0.0)
    is_plagiarized   = models.BooleanField(default=False)
    details          = models.JSONField(default=list)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Plagiarism by {self.user.username} — {self.similarity_score}%"

    def severity_label(self):
        if self.similarity_score < 20:
            return ('success', 'Original')
        elif self.similarity_score < 40:
            return ('warning', 'Slightly Similar')
        else:
            return ('danger', 'Plagiarism Detected')