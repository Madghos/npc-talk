from load import load_models, encode_documents
from rag_functions import get_model_response_with_rag

def main():
    model_name = "gpt-4.1-mini"
    retriever_name = "BAAI/bge-small-en-v1.5"
    reranker_name = "Qwen/Qwen3-Reranker-0.6B"

    client, retriever, reranker = load_models(model_name, retriever_name, reranker_name)

    documents = [
        "A knight serves his lord with loyalty and courage.",
        "In medieval towns, markets are held weekly around the central square.",
        "Herbal remedies were commonly used to treat wounds and fevers.",
    ]

    enc_documents = encode_documents(retriever, documents)

    last_response = ""
    while True:
        user_input = input("You: ").strip()
        if not user_input or user_input.lower() in {"quit", "exit"}:
            break

        _, chunks, response = get_model_response_with_rag(
            client,
            retriever,
            reranker,
            user_input,
            documents,
            enc_documents,
            last_response,
        )

        print("\n[RAG CHUNKS USED]")
        print(chunks)
        print("\nNPC:", response)
        last_response = response

if __name__ == "__main__":
    main()

