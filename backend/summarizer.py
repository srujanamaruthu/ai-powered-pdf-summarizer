import re
import os
import collections
import math

# Fallback Stopwords list to avoid dependency issues
STOPWORDS = set([
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "arent", "as", "at",
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "cant", "cannot", "could",
    "couldnt", "did", "didnt", "do", "does", "doesnt", "doing", "dont", "down", "during", "each", "few", "for",
    "from", "further", "had", "hadnt", "has", "hasnt", "have", "havent", "having", "he", "hed", "hell", "hes",
    "her", "here", "heres", "hers", "herself", "him", "himself", "his", "how", "hows", "i", "id", "ill", "im",
    "ive", "if", "in", "into", "is", "isnt", "it", "its", "itself", "lets", "me", "more", "most", "mustnt", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "shant", "she", "shed", "shell", "shes", "should", "shouldnt",
    "so", "some", "such", "than", "that", "thats", "the", "their", "theirs", "them", "themselves", "then",
    "there", "theres", "these", "they", "theyd", "theyll", "theyre", "theyve", "this", "those", "through",
    "to", "too", "under", "until", "up", "very", "was", "wasnt", "we", "wed", "well", "were", "weve", "werent",
    "what", "whats", "when", "whens", "where", "wheres", "which", "while", "who", "whos", "whom", "why", "whys",
    "with", "wont", "would", "wouldnt", "you", "youd", "youll", "youre", "youve", "your", "yours", "yourself",
    "yourselves"
])

# Attempt to import NLTK and Sumy
try:
    import nltk
    # Quietly check/download punkt and punkt_tab for sumy tokenizers
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        nltk.download('punkt_tab', quiet=True)
        
    from sumy.parsers.plaintext import PlaintextParser
    from sumy.nlp.tokenizers import Tokenizer
    from sumy.summarizers.text_rank import TextRankSummarizer
    HAS_SUMY = True
except Exception:
    HAS_SUMY = False

# Attempt to import Transformers & Torch
try:
    from transformers import pipeline
    import torch
    HAS_TRANSFORMERS = True
except Exception:
    HAS_TRANSFORMERS = False

# Global cache for transformers pipeline
_transformers_pipeline = None

def get_transformers_pipeline():
    """Lazily load and cache the Hugging Face summarization pipeline on CPU."""
    global _transformers_pipeline
    if _transformers_pipeline is None:
        if not HAS_TRANSFORMERS:
            raise ImportError("Hugging Face transformers or PyTorch is not installed in the environment.")
        # Using a small, lightweight model suitable for CPU
        model_name = "sshleifer/distilbart-cnn-12-6"
        _transformers_pipeline = pipeline(
            "summarization",
            model=model_name,
            device=-1  # Force CPU execution
        )
    return _transformers_pipeline

def split_sentences_fallback(text: str) -> list:
    """Split text into sentences using newlines and punctuation fallback."""
    # Split by newlines first to keep list items, paragraphs, and steps separate
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    all_sentences = []
    import re
    for line in lines:
        # Split by periods, question marks, or exclamation marks followed by whitespace
        splits = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s', line)
        for s in splits:
            s_clean = s.strip()
            if s_clean:
                all_sentences.append(s_clean)
    return all_sentences

def custom_frequency_textrank(text: str, num_sentences: int) -> str:
    """
    Extractive summarizer. It scores sentences using normalized term frequencies,
    moderately boosts list items and numbered steps (1.5x), selects the top-scoring
    sentences globally, and formats them in their original order.
    """
    sentences = split_sentences_fallback(text)
    if not sentences:
        return text
    num_sentences = min(num_sentences, len(sentences))

    # Clean words and count frequencies
    words = re.findall(r'\b\w+\b', text.lower())
    word_frequencies = collections.Counter(
        word for word in words if word not in STOPWORDS and len(word) > 2
    )

    if not word_frequencies:
        # If no meaningful words, return the first few sentences
        return " ".join(sentences[:num_sentences])

    max_freq = max(word_frequencies.values())
    # Normalize frequencies
    for word in word_frequencies:
        word_frequencies[word] = word_frequencies[word] / max_freq

    # Score sentences
    sentence_scores = {}
    for i, sentence in enumerate(sentences):
        sentence_words = re.findall(r'\b\w+\b', sentence.lower())
        score = sum(word_frequencies.get(word, 0) for word in sentence_words)
        
        # Length normalization: penalize very long or very short sentences
        word_count = len(sentence_words)
        if 5 <= word_count <= 40:
            score = score / math.sqrt(word_count)
        else:
            score = score / (word_count + 1)
            
        # --- PRECISE STEP / LIST / INSTRUCTION BOOSTING ---
        is_list_or_step = False
        # Matches: "1. ", "Step 1: ", "- ", "* ", "• ", "1) "
        if re.match(r'^\s*(\d+|[a-zA-Z])[\.\)\-]\s+', sentence) or \
           re.match(r'^\s*[\-\*\•\–]\s+', sentence) or \
           re.match(r'^\s*(step|task|action|instruction|phase)\s*\d+[:\.-]?\s+', sentence, re.IGNORECASE):
            is_list_or_step = True
            
        if is_list_or_step:
            score = score * 1.5
            
        sentence_scores[i] = score

    # Select the top scoring sentences globally
    top_indices = sorted(
        sentence_scores, key=sentence_scores.get, reverse=True
    )[:num_sentences]
    
    # Sort indices so they appear in chronological order
    top_indices.sort()
    
    # Extract title/topic for presentation
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = ""
    if lines:
        first_line = lines[0]
        if len(first_line.split()) <= 10:
            title = first_line
        else:
            top_keywords = [w[0] for w in word_frequencies.most_common(3)]
            title = " ".join(top_keywords).title()
            
    # Deduplicate and clean sentences
    unique_sentences = []
    seen = set()
    for idx in top_indices:
        sent = sentences[idx].strip()
        sent_lower = sent.lower()
        if sent_lower not in seen:
            unique_sentences.append(sent)
            seen.add(sent_lower)
            
    # Check if the text contains steps or list structures
    has_steps = any(re.match(r'^\s*(\d+|step|task|action|instruction|phase)\b', s, re.IGNORECASE) for s in unique_sentences)
    
    formatted_summary = []
    if title:
        formatted_summary.append(f"SUMMARY OF: {title.upper()}")
        formatted_summary.append("-" * len(f"SUMMARY OF: {title}"))
        formatted_summary.append("")
    else:
        formatted_summary.append("DOCUMENT SUMMARY")
        formatted_summary.append("----------------")
        formatted_summary.append("")

    if has_steps:
        formatted_summary.append("Key steps and procedures extracted from the document:")
        formatted_summary.append("")
        step_number = 1
        for s in unique_sentences:
            # Clean old list prefixes to avoid double numbers
            cleaned_s = re.sub(r'^\s*(\d+|[a-zA-Z]|\-|\*|\•)\s*[\.\)\-]?\s*', '', s)
            cleaned_s = re.sub(r'^\s*step\s*\d+[:\.-]?\s*', '', cleaned_s, flags=re.IGNORECASE)
            formatted_summary.append(f"{step_number}. {cleaned_s}")
            step_number += 1
    else:
        formatted_summary.append("Main points and key takeaways:")
        formatted_summary.append("")
        for s in unique_sentences:
            cleaned_s = re.sub(r'^\s*(\-|\*|\•)\s*', '', s)
            formatted_summary.append(f"• {cleaned_s}")
            
    return "\n".join(formatted_summary)

def run_textrank(text: str, length: str) -> str:
    """Run extractive TextRank summarization."""
    sentences = split_sentences_fallback(text)
    total_sentences = len(sentences)

    # Determine summary size - balanced and readable ratios
    if length == "short":
        num_sentences = max(4, int(total_sentences * 0.08))
        num_sentences = min(num_sentences, 6)
    elif length == "detailed":
        num_sentences = max(15, int(total_sentences * 0.50))
        num_sentences = min(num_sentences, 50)
    else:  # medium
        num_sentences = max(8, int(total_sentences * 0.20))
        num_sentences = min(num_sentences, 15)

    num_sentences = min(num_sentences, total_sentences)

    # Try Sumy TextRank
    if HAS_SUMY:
        try:
            parser = PlaintextParser.from_string(text, Tokenizer("english"))
            summarizer = TextRankSummarizer()
            summary = summarizer(parser.document, num_sentences)
            return " ".join([str(sentence) for sentence in summary])
        except Exception:
            # Fallback to custom frequency summarizer
            pass

    return custom_frequency_textrank(text, num_sentences)

def chunk_text(text: str, max_words: int = 600) -> list:
    """Split text into chunks of roughly max_words words."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunks.append(" ".join(words[i:i + max_words]))
    return chunks

def run_transformers(text: str, length: str) -> str:
    """Run abstractive Hugging Face transformers summarization locally."""
    # Split text into manageable chunks (distilbart has a max token limit)
    chunks = chunk_text(text, max_words=600)
    summarizer = get_transformers_pipeline()

    # Determine length settings per chunk
    if length == "short":
        max_len, min_len = 60, 20
    elif length == "detailed":
        max_len, min_len = 350, 150
    else:  # medium
        max_len, min_len = 120, 40

    summarized_chunks = []
    for chunk in chunks:
        # Skip very small chunks
        if len(chunk.split()) < 30:
            summarized_chunks.append(chunk)
            continue
            
        try:
            # Dynamically adjust max_length if the chunk itself is small
            chunk_word_count = len(chunk.split())
            curr_max_len = min(max_len, int(chunk_word_count * 0.6))
            curr_min_len = min(min_len, int(chunk_word_count * 0.2))
            
            if curr_max_len <= curr_min_len:
                curr_max_len = curr_min_len + 15
                
            res = summarizer(
                chunk, 
                max_length=curr_max_len, 
                min_length=curr_min_len, 
                do_sample=False
            )
            summarized_chunks.append(res[0]['summary_text'])
        except Exception as e:
            # If a chunk fails, fallback to its TextRank summary for that chunk
            summarized_chunks.append(run_textrank(chunk, length))

    combined_summary = " ".join(summarized_chunks)
    
    # If the combined summary is still very long and we have multiple chunks, summarize the summary
    if len(chunks) > 1 and len(combined_summary.split()) > (max_len * 2.5):
        try:
            res = summarizer(
                combined_summary,
                max_length=max_len,
                min_length=min_len,
                do_sample=False
            )
            return res[0]['summary_text']
        except Exception:
            pass

    return combined_summary

def run_openai(text: str, length: str, api_key: str) -> str:
    """Run OpenAI summarization using gpt-4o-mini."""
    if not api_key:
        raise ValueError("OpenAI API Key is required for GPT summarization.")
        
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    # Truncate text if extremely long to manage costs and prompt limits
    words = text.split()
    if len(words) > 30000:
        text = " ".join(words[:30000])
        truncated_note = "\n\n*(Note: The document was truncated to the first 30,000 words to respect token limits.)*"
    else:
        truncated_note = ""

    # Define length rules
    if length == "short":
        prompt_instruction = "Provide a short, concise summary of the following text in 100 words or less. Capture only the most critical core points."
    elif length == "detailed":
        prompt_instruction = "Provide an extremely comprehensive, in-depth summary of the following text (up to 1000 words). Break it down into logical sections with clear markdown headers and bullet points. Make sure to capture all key arguments, critical data, evidence, sub-points, and conclusions in detail."
    else:  # medium
        prompt_instruction = "Provide a medium-length summary of the following text in 250 words or less. Synthesize the main ideas and supporting arguments in a few cohesive paragraphs."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a professional research assistant specializing in creating clear, objective, and readable document summaries. Output only the summary itself without introductory phrases like 'Here is the summary'."
                },
                {"role": "user", "content": f"{prompt_instruction}\n\nDocument Text:\n{text}"}
            ],
            max_tokens=1500,
            temperature=0.3
        )
        summary = response.choices[0].message.content.strip()
        return f"{summary}{truncated_note}"
    except Exception as e:
        raise RuntimeError(f"OpenAI API call failed: {str(e)}")

def generate_summary(text: str, model_type: str, length: str, api_key: str = None) -> dict:
    """
    Generate summary using the specified method and length.
    
    Args:
        text (str): The raw text to summarize.
        model_type (str): 'textrank', 'transformers', or 'openai'.
        length (str): 'short', 'medium', or 'detailed'.
        api_key (str, optional): OpenAI API key.
        
    Returns:
        dict: A dictionary containing the summary, word count stats, and reduction percentage.
    """
    word_count_before = len(text.split())
    if word_count_before == 0:
        return {
            "summary": "No text available to summarize.",
            "word_count_before": 0,
            "word_count_after": 0,
            "reduction_percentage": 0
        }

    # Normalize inputs
    model_type = model_type.lower()
    length = length.lower()
    if length not in ["short", "medium", "detailed"]:
        length = "medium"

    summary_text = ""
    error_warning = None

    if model_type == "openai":
        try:
            summary_text = run_openai(text, length, api_key)
        except Exception as e:
            error_warning = f"OpenAI failed ({str(e)}). Falling back to TextRank."
            summary_text = run_textrank(text, length)
            model_type = "textrank"
            
    elif model_type == "transformers":
        try:
            summary_text = run_transformers(text, length)
        except Exception as e:
            error_warning = f"Hugging Face transformers failed ({str(e)}). Make sure dependencies are downloaded. Falling back to TextRank."
            summary_text = run_textrank(text, length)
            model_type = "textrank"
            
    else:  # TextRank (or default)
        summary_text = run_textrank(text, length)
        model_type = "textrank"

    word_count_after = len(summary_text.split())
    
    # Calculate percentage reduction
    reduction = 0.0
    if word_count_before > 0:
        reduction = round((1 - (word_count_after / word_count_before)) * 100, 1)
        # Don't show negative reduction if summary somehow gets longer
        reduction = max(0.0, reduction)

    return {
        "summary": summary_text,
        "model_used": model_type,
        "word_count_before": word_count_before,
        "word_count_after": word_count_after,
        "reduction_percentage": reduction,
        "warning": error_warning
    }
