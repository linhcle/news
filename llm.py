import transformers
import torch
import gc
from sentence_transformers import SentenceTransformer, util
from transformers import AutoModelForCausalLM, AutoTokenizer

# model_id = "mistralai/Mistral-7B-Instruct-v0.3"

# # Load the model without quantization for CPU inference
# tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)
# model = AutoModelForCausalLM.from_pretrained(
#     model_id,
#     torch_dtype=torch.float16,  # Use FP16 precision
# )


# # Initialize the pipeline
# pipeline = transformers.pipeline(
#     "text-generation", 
#     model=model, 
#     tokenizer=tokenizer, 
#     device=-1  # CPU-only mode
# )


# # Function to generate a summary
# def generate_summary(article):
#     gc.collect()
#     if torch.cuda.is_available():
#         torch.cuda.empty_cache()

#     # Create the chat-like message format
#     message = [
#         {"role": "system", "content": "You are an expert in summarizing articles. For each article, summarize THE WHOLE ARTICLE it in ONLY two sentences for ease of comprehension. Retain only the important information."},
#         {"role": "user", "content": article},
#     ]

#     # Format the prompt manually
#     prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in message])

#     # Generate the response
#     outputs = pipeline(
#         prompt,
#         max_new_tokens=256,
#         eos_token_id=tokenizer.eos_token_id,
#         do_sample=True,
#         temperature=0.6,
#         top_p=0.9,
#     )

#     # Extract the generated text
#     response = outputs[0]["generated_text"][len(prompt):].strip()
#     return response


# Load the model (MiniLM)
model = SentenceTransformer('all-mpnet-base-v2')

import re
from sentence_transformers import util

def small_summary(article, top_n=2):
    # Use regex to split sentences more accurately
    sentences = re.split(r'(?<=[.!?])\s+', article.strip())

    # Encode all sentences into embeddings
    sentence_embeddings = model.encode(sentences, convert_to_tensor=True)

    # Calculate the mean embedding (to represent the entire article)
    article_embedding = sentence_embeddings.mean(dim=0)

    # Use cosine similarity to rank sentences based on relevance to the whole article
    similarities = util.pytorch_cos_sim(article_embedding, sentence_embeddings)[0]

    # Ensure top_n does not exceed the number of available sentences
    top_n = min(top_n, len(sentences))

    # Get the top N sentences with the highest similarity scores
    top_sentence_indices = similarities.topk(top_n).indices

    # Sort the selected sentences by their original order in the article
    top_sentences = [sentences[i] for i in sorted(top_sentence_indices)]

    # Join the sentences to form the summary
    summary = ' '.join(top_sentences)
    return summary