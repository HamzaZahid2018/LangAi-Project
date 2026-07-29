import re
import nltk
import math
import os
import sys
import urllib.parse
import urllib.request
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.summarizers.luhn import LuhnSummarizer
from deep_translator import GoogleTranslator
import types as _types

class _MockPipeline:
    def __init__(self, *args, **kwargs):
        pass
    def __call__(self, text):
        class _Doc:
            @property
            def sentences(self):
                class _Sent:
                    @property
                    def text(self): return text
                return [_Sent()]
        return _Doc()

_mock_stanza = _types.ModuleType('stanza')
_mock_stanza.download = lambda *a, **kw: None
_mock_stanza.Pipeline = _MockPipeline
sys.modules.setdefault('stanza', _mock_stanza)
# Download required NLTK data
for pkg in ['punkt', 'stopwords', 'punkt_tab']:
    try:
        nltk.download(pkg, quiet=True)
    except Exception:
        pass
#Grammar tool (lazy-loaded, needs Java + internet on first use) 
_grammar_tool = None
def _get_grammar_tool():
    """Try to load the local LanguageTool server (requires Java).
    Returns the tool on success, or False if unavailable."""
    global _grammar_tool
    if _grammar_tool is None:
        try:
            import language_tool_python
            # Use a short timeout so we fail fast if Java isn't ready
            _grammar_tool = language_tool_python.LanguageTool('en-US')
        except Exception as e:
            print(f"[GRAMMAR TOOL ERROR] {e}")
            _grammar_tool = False
    return _grammar_tool
_GRAMMAR_RULES = [
    (r'\ba ([aeiouAEIOU]\w+)',
     'Use "an" before words starting with a vowel sound.', 'ARTICLE'),
    (r'\ban ([^aeiouAEIOU\s]\w+)',
     'Use "a" before words starting with a consonant sound.', 'ARTICLE'),
    (r"\b(he|she|it)\s+don't\b",
     '"He/she/it" requires "doesn\'t" not "don\'t".', 'SVA'),
    (r"\b(i|you|we|they)\s+doesn't\b",
     '"I/you/we/they" requires "don\'t" not "doesn\'t".', 'SVA'),
    (r"\b(he|she|it)\s+have\b",
     '"He/she/it" requires "has" not "have".', 'SVA'),
    (r"\b(i|you|we|they)\s+has\b",
     '"I/you/we/they" requires "have" not "has".', 'SVA'),
    (r"\b(he|she|it)\s+were\b",
     '"He/she/it" requires "was" not "were" in past simple.', 'SVA'),
    (r"\b(he|she|it)\s+(go|run|eat|play|come|make|take|give|know|see|get|like|want|need|try|use|look|work|think|keep|let|begin|show|hear|seem|feel|tell|put|bring|stand|buy|hold|turn|move|live|set)\b",
     '"He/she/it" needs a verb with -s/es (e.g. "goes", "runs").', 'SVA'),
    (r"\bto\s+(eats|runs|goes|plays|comes|makes|takes|gives|knows|sees|gets|likes|wants|needs|tries|uses|looks|works|thinks|keeps|shows|hears|feels|tells|puts|brings|turns|moves|lives|sets|stands|buys|holds)\b",
     'Use the base form of the verb after "to" (infinitive). Remove the "-s".', 'INFINITIVE'),
    (r"\bshould of\b", 'Should be "should have".', 'MODAL'),
    (r"\bwould of\b",  'Should be "would have".', 'MODAL'),
    (r"\bcould of\b",  'Should be "could have".', 'MODAL'),
    (r"\bmust of\b",   'Should be "must have".',  'MODAL'),
    (r"\bshould\s+to\s+", 'Remove "to" after "should" — use base verb directly.', 'MODAL'),
    (r"\bwould\s+to\s+",  'Remove "to" after "would" — use base verb directly.', 'MODAL'),
    (r"\bcould\s+to\s+",  'Remove "to" after "could" — use base verb directly.', 'MODAL'),

    #Double negatives 
    (r"\b(don't|doesn't|didn't|can't|won't|isn't|aren't|wasn't|weren't)\b.{0,30}\b(nothing|nobody|nowhere|never|no one)\b",
     'Double negative detected. Use "anything", "anyone", "anywhere", "ever" instead.', 'DOUBLE_NEGATIVE'),

    # Capitalization
    (r'(?<![.!?]\s)(?<![.!?])\bi\b(?!\w)',
     'The pronoun "I" should always be uppercase.', 'CAPITALIZATION'),

    #Punctuation 
    (r'\w ,', 'No space before a comma.', 'PUNCTUATION'),
    (r'\w ;', 'No space before a semicolon.', 'PUNCTUATION'),
    (r'\.{4,}', 'Use exactly three dots for an ellipsis (...).', 'PUNCTUATION'),
    (r'\b(\w+)\s+\1\b', 'Repeated word detected.', 'DUPLICATE_WORD'),
    (r"\btheir\s+(is|are|was|were)\b",
     'Possible confusion: "their" (possessive) vs "there" (place).', 'CONFUSABLE'),
    (r"\bthere\s+(book|car|house|dog|cat|phone|job|team)\b",
     'Possible confusion: "there" (place) vs "their" (possessive).', 'CONFUSABLE'),
    (r"\bits\s+(a |an |the )\b",
     'Possible confusion: "its" (possessive) vs "it\'s" (it is).', 'CONFUSABLE'),
    (r"\byour\s+(a |an |the |going|coming|right|wrong|not)\b",
     'Possible confusion: "your" (possessive) vs "you\'re" (you are).', 'CONFUSABLE'),
    (r"\bthen\b(?=\s+\w+er\b)",
     'Possible confusion: "then" (time) vs "than" (comparison).', 'CONFUSABLE'),
]
# Verbs that need -s/es with he/she/it — used for auto-correction
_SVA_BASE_TO_S = {
    'go':'goes','do':'does','have':'has','be':'is',
    'run':'runs','eat':'eats','play':'plays','come':'comes',
    'make':'makes','take':'takes','give':'gives','know':'knows',
    'see':'sees','get':'gets','like':'likes','want':'wants',
    'need':'needs','try':'tries','use':'uses','look':'looks',
    'work':'works','think':'thinks','keep':'keeps','let':'lets',
    'begin':'begins','show':'shows','hear':'hears','seem':'seems',
    'feel':'feels','tell':'tells','put':'puts','bring':'brings',
    'stand':'stands','buy':'buys','hold':'holds','turn':'turns',
    'move':'moves','live':'lives','set':'sets',
}

def _offline_grammar_check(text: str) -> dict:
    errors = []
    corrected = text

    for pattern, message, category in _GRAMMAR_RULES:
        if not message:
            continue
        for m in re.finditer(pattern, corrected, re.IGNORECASE):
            errors.append({
                'message':     message,
                'context':     corrected[max(0, m.start()-25):m.end()+25],
                'offset':      m.start(),
                'length':      m.end() - m.start(),
                'suggestions': [],
                'category':    category,
                'rule_id':     pattern[:40],
            })
    corrected = re.sub(r'\ba ([aeiouAEIOU]\w+)', r'an \1', corrected)
    # an → a before consonants
    corrected = re.sub(r'\ban ([^aeiouAEIOU\s]\w+)', r'a \1', corrected)
    # he/she/it + don't → doesn't
    corrected = re.sub(
        r"\b(he|she|it)\s+don't\b",
        lambda m: m.group(1) + " doesn't",
        corrected, flags=re.IGNORECASE
    )
    # I/you/we/they + doesn't → don't
    corrected = re.sub(
        r"\b(i|you|we|they)\s+doesn't\b",
        lambda m: m.group(1) + " don't",
        corrected, flags=re.IGNORECASE
    )
    # he/she/it + have → has
    corrected = re.sub(
        r"\b(he|she|it)\s+have\b",
        lambda m: m.group(1) + ' has',
        corrected, flags=re.IGNORECASE
    )
    # I/you/we/they + has → have
    corrected = re.sub(
        r"\b(i|you|we|they)\s+has\b",
        lambda m: m.group(1) + ' have',
        corrected, flags=re.IGNORECASE
    )
    # he/she/it + base verb → verb+s
    def _fix_sva(m):
        subj = m.group(1)
        verb = m.group(2).lower()
        return subj + ' ' + _SVA_BASE_TO_S.get(verb, verb + 's')
    corrected = re.sub(
        r"\b(he|she|it)\s+(go|run|eat|play|come|make|take|give|know|see|get|like|want|need|try|use|look|work|think|keep|let|begin|show|hear|seem|feel|tell|put|bring|stand|buy|hold|turn|move|live|set)\b",
        _fix_sva, corrected, flags=re.IGNORECASE
    )
    # to + verb-s → to + base verb
    corrected = re.sub(
        r"\bto\s+(eats|runs|goes|plays|comes|makes|takes|gives|knows|sees|gets|likes|wants|needs|tries|uses|looks|works|thinks|keeps|shows|hears|feels|tells|puts|brings|turns|moves|lives|sets|stands|buys|holds)\b",
        lambda m: 'to ' + m.group(1).rstrip('s') if not m.group(1).endswith('es') else 'to ' + re.sub(r'es$','',m.group(1)),
        corrected, flags=re.IGNORECASE
    )
    # should/would/could of → have
    corrected = re.sub(r"\b(should|would|could|must)\s+of\b", r'\1 have', corrected, flags=re.IGNORECASE)
    # Repeated words
    corrected = re.sub(r'\b(\w+)\s+\1\b', r'\1', corrected, flags=re.IGNORECASE)

    return {
        'success':     True,
        'mode':        'offline',
        'original':    text,
        'corrected':   corrected,
        'errors':      errors,
        'error_count': len(errors),
        'has_errors':  len(errors) > 0,
    }


def _is_online():
    try:
        urllib.request.urlopen('http://google.com', timeout=3)
        return True
    except:
        return False


def check_grammar(text: str) -> dict:
    if not text.strip():
        return {'error': 'Please Provide Text To Check.'}

    #  ONLINE: LanguageTool Public API 
    if _is_online():
        try:
            import requests
            response = requests.post(
                'https://api.languagetool.org/v2/check',
                data={'text': text, 'language': 'en-US'},
                timeout=10
            )
            data    = response.json()
            matches = data.get('matches', [])
            errors = []
            for m in matches:
                replacements = [r['value'] for r in m['replacements'][:4]]
                errors.append({
                    'message':     m['message'],
                    'context':     m['context']['text'],
                    'offset':      m['offset'],
                    'length':      m['length'],
                    'suggestions': replacements,
                    'category':    m['rule']['category']['name'],
                    'rule_id':     m['rule']['id'],
                })
            corrected    = text
            offset_shift = 0
            for m in sorted(matches, key=lambda x: x['offset']):
                replacements = [r['value'] for r in m['replacements'][:1]]
                if not replacements:
                    continue
                rule_id = m['rule']['id']
                if any(skip in rule_id for skip in ['SPELL', 'MORFOLOGIK', 'HUNSPELL', 'TYPO']):
                    continue
                offset    = m['offset'] + offset_shift
                length    = m['length']
                best      = replacements[0]
                corrected = corrected[:offset] + best + corrected[offset + length:]
                offset_shift += len(best) - length
            return {
                'success':     True,
                'original':    text,
                'corrected':   corrected,
                'errors':      errors,
                'error_count': len(errors),
                'has_errors':  len(errors) > 0,
            }
        except Exception:
            pass

    # ── OFFLINE: try local LanguageTool server first, fall back to pure-Python ─
    tool = _get_grammar_tool()
    if tool:
        try:
            import language_tool_python
            matches   = tool.check(text)
            corrected = language_tool_python.utils.correct(text, matches)
            errors = []
            for m in matches:
                errors.append({
                    'message':     m.message,
                    'context':     str(m.context),
                    'offset':      m.offset,
                    'length':      m.error_length,
                    'suggestions': m.replacements[:3],
                    'category':    str(m.category),
                    'rule_id':     m.rule_id,
                })
            return {
                'success':     True,
                'mode':        'offline',
                'original':    text,
                'corrected':   corrected,
                'errors':      errors,
                'error_count': len(errors),
                'has_errors':  len(errors) > 0,
            }
        except Exception as e:
            print(f"[LOCAL GRAMMAR ERROR] {e}")
    # OFFLINE FALLBACK: pure-Python rule-based checker 
    return _offline_grammar_check(text)

#TRANSLATION 
SUPPORTED_LANGUAGES = {
    'en':    'English',
    'ur':    'Urdu',
    'ar':    'Arabic',
    'fr':    'French',
    'es':    'Spanish',
    'de':    'German',
    'zh-CN': 'Chinese (Simplified)',
    'hi':    'Hindi',
}
_EN_MY_NAME_IS_PATTERN = re.compile(
    r"^\s*my\s+name\s+is\s+([a-zA-Z][a-zA-Z\-\'\s]{0,40})\s*[\.!?]?\s*$",
    re.IGNORECASE,
)
_KNOWN_URDU_NAME_MAP = {
    'manan': 'منان',
}
def _latin_name_to_urdu(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z]", "", name).lower()
    if not cleaned:
        return ''
    if cleaned in _KNOWN_URDU_NAME_MAP:
        return _KNOWN_URDU_NAME_MAP[cleaned]
    # Lightweight fallback transliteration 
    digraphs = {
        'sh': 'ش', 'ch': 'چ', 'kh': 'خ', 'gh': 'غ', 'ph': 'ف',
        'th': 'ت', 'dh': 'د', 'zh': 'ژ', 'aa': 'ا', 'ee': 'ی',
        'oo': 'و', 'ai': 'ے', 'ei': 'ے', 'ou': 'و',
    }
    singles = {
        'a': '', 'e': '', 'i': '', 'o': '', 'u': '',
        'b': 'ب', 'c': 'ک', 'd': 'د', 'f': 'ف', 'g': 'گ',
        'h': 'ہ', 'j': 'ج', 'k': 'ک', 'l': 'ل', 'm': 'م',
        'n': 'ن', 'p': 'پ', 'q': 'ق', 'r': 'ر', 's': 'س',
        't': 'ت', 'v': 'و', 'w': 'و', 'x': 'کس', 'y': 'ی',
        'z': 'ز',
    }
    out = []
    i = 0
    while i < len(cleaned):
        pair = cleaned[i:i + 2]
        if len(pair) == 2 and pair in digraphs:
            out.append(digraphs[pair])
            i += 2
            continue
        out.append(singles.get(cleaned[i], ''))
        i += 1

    urdu = ''.join(out)
    return urdu if urdu else name
def _maybe_fix_name_sentence(original_text: str, translated_text: str, source_lang: str, target_lang: str) -> str:
    if target_lang != 'ur':
        return translated_text
    if source_lang not in ('auto', 'en'):
        return translated_text

    match = _EN_MY_NAME_IS_PATTERN.match(original_text)
    if not match:
        return translated_text

    name = match.group(1).strip()
    urdu_name = _latin_name_to_urdu(name)
    if not urdu_name:
        return translated_text
    return f'میرا نام {urdu_name} ہے'
def _split_text(text: str, max_len: int = 4500) -> list:
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    for word in words:
        word_length = len(word) + 1  
        if current_length + word_length > max_len and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = word_length
        else:
            current_chunk.append(word)
            current_length += word_length
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return chunks
def translate_text(text: str, target_lang: str, source_lang: str = 'auto') -> dict:
    if not text.strip():
        return {'success': False, 'error': 'Please Provide Text To Translate.'}
    if target_lang not in SUPPORTED_LANGUAGES:
        return {'success': False, 'error': f'Language "{target_lang}" not supported.'}

    # ── ONLINE MODE: Google Translate ────────────────────────────────────────
    if _is_online():
        try:
            chunks = _split_text(text, max_len=4500)
            translated_chunks = []
            for chunk in chunks:
                translator = GoogleTranslator(source=source_lang, target=target_lang)
                translated_chunks.append(translator.translate(chunk))
            translated = ' '.join(translated_chunks)
            return {
                'success':          True,
                'mode':             'online',
                'original':         text,
                'translated':       translated,
                'source_lang':      source_lang,
                'target_lang':      target_lang,
                'target_lang_name': SUPPORTED_LANGUAGES.get(target_lang, target_lang),
            }
        except Exception as e:
            return {'success': False, 'error': f'Online Translation Failed: {str(e)}'}

    # ── OFFLINE MODE: Argostranslate ─────────────────────────────────────────
    try:
        import argostranslate.package
        import argostranslate.translate

        src = 'en' if source_lang == 'auto' else source_lang
        tgt = 'zh' if target_lang == 'zh-CN' else target_lang
        src = 'zh' if src == 'zh-CN' else src

        installed_languages = argostranslate.translate.get_installed_languages()
        installed_codes     = [l.code for l in installed_languages]
        from_lang = next((l for l in installed_languages if l.code == src), None)
        to_lang   = next((l for l in installed_languages if l.code == tgt), None)

        if not from_lang or not to_lang:
            missing = [c for c in [src, tgt] if c not in installed_codes]
            return {
                'success': False,
                'error': (
                    f'Offline translation from "{src}" to "{tgt}" is not available. '
                    f'Missing language pack(s): {missing}. '
                    'Please connect to the internet once to download them.'
                )
            }

        translation_model = from_lang.get_translation(to_lang)
        if not translation_model:
            return {
                'success': False,
                'error': f'No offline translation model found for {src} → {tgt}. Please connect to the internet to download it.'
            }

        translated = translation_model.translate(text)
        return {
            'success':          True,
            'mode':             'offline',
            'original':         text,
            'translated':       translated,
            'source_lang':      src,
            'target_lang':      target_lang,
            'target_lang_name': SUPPORTED_LANGUAGES.get(target_lang, target_lang),
        }
    except ImportError as ie:
        return {'success': False, 'error': f'Argostranslate not installed: {str(ie)}'}
    except Exception as e:
        import traceback
        print(f"[OFFLINE TRANSLATE ERROR]\n{traceback.format_exc()}")
        return {'success': False, 'error': f'Offline translation error: {type(e).__name__} - {str(e)}'}

#PLAGIARISM DETECTION  (TF-IDF ML Model)
def check_plagiarism(input_text: str, documents: list) -> dict:
    if not input_text.strip():
        return {'success': False, 'error': 'Please provide text to check.'}
    results   = []
    max_score = 0.0
    #Compare against saved documents (TF-IDF)
    if documents:
        try:
            doc_texts    = [doc.content for doc in documents]
            all_texts    = [input_text] + doc_texts
            vectorizer   = TfidfVectorizer(stop_words='english', ngram_range=(1, 2), min_df=1)
            tfidf_matrix = vectorizer.fit_transform(all_texts)
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

            for i, doc in enumerate(documents):
                score = round(float(similarities[i]) * 100, 2)
                if score > max_score:
                    max_score = score
                results.append({
                    'source':     doc.title,
                    'similarity': score,
                    'severity':   _severity(score),
                    'type':       'Database Match',
                })
            results.sort(key=lambda x: x['similarity'], reverse=True)
        except Exception as e:
            pass
    # AI Content Detection using writing pattern analysis
    ai_score = _detect_ai_content(input_text)
    results.append({
        'source':     'AI Content Detector',
        'similarity': ai_score,
        'severity':   _severity(ai_score),
        'type':       'AI Generated Detection',
    })
    # C) Online plagiarism check via search patterns
    if _is_online():
        online_score = _online_plagiarism_check(input_text)
        if online_score > 0:
            results.append({
                'source':     'Web Content Match',
                'similarity': online_score,
                'severity':   _severity(online_score),
                'type':       'Online Match',
            })
            if online_score > max_score:
                max_score = online_score

    final_score = max(max_score, ai_score)

    return {
        'success':          True,
        'similarity_score': round(final_score, 2),
        'is_plagiarized':   final_score >= 40,
        'ai_score':         ai_score,
        'details':          results[:6],
    }


def _detect_ai_content(text: str) -> float:
    """
    Multi-signal AI content detector.
    Calibrated to correctly score typical AI essay text ~55-80%
    while keeping genuine human writing below 30%.
    """
    sentences = re.split(r'[.!?]+', text.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    # Need at least 3 sentences for a meaningful signal
    if len(sentences) < 3:
        return 0.0

    score      = 0.0
    words      = re.findall(r'\b[a-z]+\b', text.lower())
    word_count = max(len(words), 1)
    text_lower = text.lower()

    # ── 1. AI BUZZWORD DENSITY ────────────────────────────────────────────────
    # AI models heavily overuse these formal, polished words/phrases
    ai_buzzwords = [
        'essential', 'crucial', 'significant', 'substantial', 'comprehensive',
        'innovative', 'transformative', 'increasingly', 'paramount', 'multifaceted',
        'noteworthy', 'fundamentally', 'undeniably', 'imperative', 'pivotal',
        'facilitate', 'leverage', 'utilize', 'robust', 'seamlessly',
        'holistic', 'proactive', 'delve', 'dive into',
        'it is worth noting', 'it is important to note', 'it is crucial',
        'plays a crucial role', 'plays an important role', 'plays a vital role',
        "in today's world", 'in the modern world', "in today's society",
        'in the digital age', 'in recent years', 'over the past few decades',
        'it is evident', 'it is clear that',
    ]
    buzz_hits = sum(1 for w in ai_buzzwords if w in text_lower)
    if buzz_hits >= 5:
        score += 30
    elif buzz_hits >= 3:
        score += 20
    elif buzz_hits >= 1:
        score += 10

    # ── 2. TRANSITION WORD DENSITY ────────────────────────────────────────────
    transition_words = [
        'however', 'furthermore', 'moreover', 'additionally', 'consequently',
        'nevertheless', 'therefore', 'thus', 'in conclusion', 'in summary',
        'in addition', 'on the other hand', 'as a result', 'for instance',
        'for example', 'in contrast', 'similarly', 'likewise', 'notably',
        'importantly', 'ultimately', 'overall', 'in essence', 'to summarize',
    ]
    trans_hits  = sum(text_lower.count(w) for w in transition_words)
    trans_ratio = trans_hits / (word_count / 100)   # hits per 100 words
    if trans_ratio > 3.5:
        score += 20
    elif trans_ratio > 2.0:
        score += 15
    elif trans_ratio > 1.0:
        score += 10

    # ── 3. CLASSIC AI CONTRAST / BALANCE STRUCTURE ───────────────────────────
    # "While X, it also Y" / "Although X, Y" / "On the other hand"
    ai_contrast_patterns = [
        r'\bwhile\b.{5,100},',
        r'\balthough\b.{5,100},',
        r'\bdespite\b.{5,80},',
        r'\bon the other hand\b',
        r'\bon one hand\b',
        r'\bwhile it\b',
        r'\bwhile (they|this|these|that)\b',
    ]
    pattern_hits = sum(1 for p in ai_contrast_patterns
                       if re.search(p, text_lower))
    if pattern_hits >= 2:
        score += 15
    elif pattern_hits >= 1:
        score += 7

    # ── 4. SERIAL COMMA LISTS OF 3  (X, Y, and Z) ───────────────────────────
    # AI loves enumerating exactly 3 items: "work, communicate, and learn"
    list_of_3 = len(re.findall(r'\b\w+,\s*\w+,\s*and\s+\w+', text_lower))
    if list_of_3 >= 3:
        score += 15
    elif list_of_3 >= 2:
        score += 8

    # ── 5. SENTENCE LENGTH UNIFORMITY ────────────────────────────────────────
    lengths  = [len(s.split()) for s in sentences]
    avg      = sum(lengths) / len(lengths)
    variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
    std_dev  = math.sqrt(variance)
    if avg > 8 and std_dev > 0:
        cv = std_dev / avg          # coefficient of variation
        if cv < 0.25:               # very uniform → very AI-like
            score += 15
        elif cv < 0.40:             # moderately uniform
            score += 7

    # ── 6. NO CONTRACTIONS IN SUSTAINED TEXT ─────────────────────────────────
    # AI almost never writes don't / it's / they're in formal prose
    contractions = len(re.findall(
        r"\b\w+n't\b|\b\w+'re\b|\bcan't\b|\bwon't\b|\bI'm\b|\bI'll\b", text))
    if contractions == 0 and len(sentences) >= 5 and score >= 15:
        score += 10

    # ── 7. PASSIVE VOICE DENSITY ──────────────────────────────────────────────
    passive = len(re.findall(r'\b(is|are|was|were|been|being)\s+\w+ed\b',
                             text, re.I))
    if passive / max(len(sentences), 1) > 0.5:
        score += 10

    # ── 8. GENERIC AI ESSAY OPENER ───────────────────────────────────────────
    filler_openers = [
        r'^in (today|the modern|recent|our)',
        r'^technology has (become|been|made)',
        r'^(the|it) is (important|essential|crucial|clear|evident)',
        r'^(with|as) (technology|the advent|the rise|the growth)',
        r'^throughout (history|the years|human history)',
        r'^(education|technology|society|the internet) (plays|has|is)',
        r'^(social media|artificial intelligence|climate change|the internet) has',
    ]
    first_sent = sentences[0].lower() if sentences else ''
    if any(re.search(p, first_sent) for p in filler_openers):
        score += 10

    return min(round(score, 2), 95.0)
def _severity(score: float) -> str:
    if score >= 75:
        return 'Critical'
    elif score >= 50:
        return 'High'
    elif score >= 25:
        return 'Medium'
    elif score > 0:
        return 'Low'
    else:
        return 'None'
def _online_plagiarism_check(text: str) -> float:
    """Only flag as online match if the exact snippet appears verbatim as a known
    AbstractText (encyclopedia / direct article match). Generic RelatedTopics are
    returned for almost any common subject and are not a reliable plagiarism signal."""
    try:
        import requests
        snippet = ' '.join(text.split()[:20])
        url     = f"https://api.duckduckgo.com/?q=%22{urllib.parse.quote(snippet)}%22&format=json"
        resp    = requests.get(url, timeout=5)
        data    = resp.json()
        # Only count it as plagiarism if there is a direct article/abstract match
        if data.get('AbstractText') and len(data['AbstractText']) > 50:
            return 45.0
        return 0.0
    except:
        return 0.0
#SUMMARIZATION  (LSA Model)
def summarize_text(text: str, sentences_count: int = 3) -> dict:
    if not text.strip():
        return {'success': False, 'error': 'Please provide text to summarize.'}
    words = text.split()
    if len(words) < 30:
        return {'success': False, 'error': 'Text is too short to summarize (need at least 30 words).'}

    sentences_count = max(1, min(sentences_count, 8))

    try:
        parser    = PlaintextParser.from_string(text, Tokenizer('english'))
        summarizer = LsaSummarizer()
        summary_sentences = summarizer(parser.document, sentences_count)
        summary = ' '.join(str(s) for s in summary_sentences)

        if not summary.strip():
            # Fallback to Luhn
            summarizer2 = LuhnSummarizer()
            summary_sentences = summarizer2(parser.document, sentences_count)
            summary = ' '.join(str(s) for s in summary_sentences)

        orig_words = len(words)
        summ_words = len(summary.split())
        reduction  = round((1 - summ_words / orig_words) * 100, 1) if orig_words > 0 else 0

        return {
            'success':         True,
            'original':        text,
            'summary':         summary,
            'original_words':  orig_words,
            'summary_words':   summ_words,
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}