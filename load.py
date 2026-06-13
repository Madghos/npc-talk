import torch
from sentence_transformers import SentenceTransformer, CrossEncoder
from openai import OpenAI
import os

api_key = os.getenv("OPENAI_API_KEY")

def load_models(model_name, retriever_name, reranker_name):

    print("Loading models...")

    client = OpenAI(
        api_key=api_key
    )

    print(f"Client for {model_name} initialized successfully.")

    retriever = SentenceTransformer(
        retriever_name,
        model_kwargs={"torch_dtype": torch.bfloat16} if torch.cuda.is_available() else None,
        
    )

    print(f"Retriever {retriever_name} loaded successfully.")

    reranker = CrossEncoder(
        reranker_name,
        activation_fn=torch.nn.Identity(),
        max_length=8192,
        device="cuda" if torch.cuda.is_available() else "cpu",
        model_kwargs={"torch_dtype": torch.bfloat16} if torch.cuda.is_available() else None,
    )

    print(f"Reranker {reranker_name} loaded successfully.")

    return client, retriever, reranker


def encode_documents(retriever, documents):

    doc_embs = retriever.encode(
        documents,
        convert_to_tensor=True,
        show_progress_bar=False,
    )

    return doc_embs
