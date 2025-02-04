import gensim.downloader as api

word2vec_model = api.load("word2vec-google-news-300")
print(word2vec_model.similarity("cat", "dog"))  # Should return a high similarity score
print(word2vec_model.most_similar("king"))      # Should return words like "queen", "prince", etc.