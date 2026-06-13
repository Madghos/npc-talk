import torch
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


def load_models(retriever_name):

    print("Loading models...")

    client = OpenAI(
        api_key=api_key
    )

    print(f"Client initialized successfully.")

    retriever = SentenceTransformer(
        retriever_name,
        model_kwargs={"torch_dtype": torch.bfloat16} if torch.cuda.is_available() else None,
    )

    print(f"Retriever {retriever_name} loaded successfully.")

    return client, retriever


def encode_documents(retriever, documents):

    doc_embs = retriever.encode(
        documents,
        convert_to_tensor=True,
        show_progress_bar=False,
    )

    return doc_embs
