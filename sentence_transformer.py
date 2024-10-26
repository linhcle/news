from sentence_transformers import SentenceTransformer, util

# Load the model (MiniLM)
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

def extractive_summary(article, top_n=2):
    # Split the article into sentences
    sentences = article.split('. ')
    
    # Encode all sentences into embeddings
    sentence_embeddings = model.encode(sentences, convert_to_tensor=True)
    
    # Calculate the mean embedding (to represent the entire article)
    article_embedding = sentence_embeddings.mean(dim=0)
    
    # Use cosine similarity to rank sentences based on relevance to the whole article
    similarities = util.pytorch_cos_sim(article_embedding, sentence_embeddings)[0]

    # Get the top N sentences with the highest similarity scores
    top_sentences = [sentences[i] for i in similarities.topk(top_n).indices]

    # Join the sentences to form the summary
    summary = '. '.join(top_sentences)
    return summary

# Example usage
article = """Artificial Intelligence is transforming industries by automating tasks 
and enhancing decision-making. Companies are increasingly adopting AI to remain competitive 
in the fast-changing digital landscape. However, the ethical implications of AI need to 
be addressed to ensure responsible usage."""

summary = extractive_summary(article)
print("Summary:", summary)
