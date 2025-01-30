import nltk
from nltk.corpus import wordnet

# Download WordNet if not already installed
print("starting")
nltk.download("wordnet")

def is_word_related(word1, word2):
    """Check if two words are related using WordNet synonyms."""
    synsets1 = wordnet.synsets(word1)
    synsets2 = wordnet.synsets(word2)
    
    if not synsets1 or not synsets2:
        return False  # No definition found

    # Check if they share synonyms
    for syn1 in synsets1:
        for syn2 in synsets2:
            similarity_score = syn1.wup_similarity(syn2)
            print("Simularity score for " + word1 + " and " + word2 + " is:", similarity_score)
            if similarity_score > 0.8:  # 80% similarity threshold can change
                return True
    return False





def similarity_score_word_related(word1, word2):
    """Check if two words are related using WordNet synonyms."""
    synsets1 = wordnet.synsets(word1)
    synsets2 = wordnet.synsets(word2)
    
    if not synsets1 or not synsets2:
        return -1  # No definition found

    # Check if they share synonyms
    for syn1 in synsets1:
        for syn2 in synsets2:
            similarity_score = syn1.wup_similarity(syn2)
            print("Simularity score for " + word1 + " and " + word2 + " is:", similarity_score)
 #           if similarity_score > 0.5:  # 50% similarity threshold
 #               return True
    return similarity_score



#print(is_word_related('chair', 'running'))
#print(is_word_related('chair', 'orange'))
#print(is_word_related('chair', 'stool'))
#print(is_word_related('chair', 'chair'))
#print(is_word_related('chair', 'armchair'))
