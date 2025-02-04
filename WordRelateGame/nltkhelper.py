import nltk
from nltk.corpus import wordnet
import gensim.downloader as api

# Load Word2Vec Model
word2vec_model = api.load("word2vec-google-news-300")

# Ensure WordNet is available
try:
    wordnet.synsets("test")
except LookupError:
    print("Downloading WordNet...")
    nltk.download("wordnet")

def get_similarity_score(word1, word2):
    """Returns the highest similarity score between two words using WordNet and Word Embeddings."""
    
    # ✅ **Step 1: WordNet Similarity Score**
    synsets1 = wordnet.synsets(word1)
    synsets2 = wordnet.synsets(word2)
    
    max_wordnet_score = 0  # Track highest WordNet similarity
    if synsets1 and synsets2:
        for syn1 in synsets1:
            for syn2 in synsets2:
                similarity_score = syn1.wup_similarity(syn2)
                if similarity_score:
                    max_wordnet_score = max(max_wordnet_score, similarity_score)

    # ✅ **Step 2: Word Embeddings Similarity Score**
    try:
        embedding_score = word2vec_model.similarity(word1, word2)
    except KeyError:
        embedding_score = 0  # Word not found in Word2Vec
    
    # ✅ **Step 3: Return the best available similarity score**
    return max(max_wordnet_score, embedding_score)

def is_word_related(word1, word2, wordnet_threshold=0.8, embedding_threshold=0.5):
    """Check if two words are related based on similarity scores."""
    similarity_score = get_similarity_score(word1, word2)
    print(f"Similarity Score ({word1} ↔ {word2}): {similarity_score}")
    return similarity_score >= min(wordnet_threshold, embedding_threshold)