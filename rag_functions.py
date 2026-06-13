from vllm import SamplingParams
import torch
from sentence_transformers import util

sampling_params = SamplingParams(n=1, temperature=1.0, top_k=10, max_tokens=5000)


def get_relevant_documents(text, documents, doc_embs, num_docs_to_return, retriever, reranker):
    # RETRIEVE PART
    query_for_embedding = "[query]: " + text
    query_emb = retriever.encode(
        [query_for_embedding],
        convert_to_tensor=True,
        show_progress_bar=False
    )

    scores = util.cos_sim(query_emb, doc_embs)[0]

    top_k = min(10, len(documents))
    top_results = torch.topk(scores, k=top_k)

    retrieved_docs = []
    for doc_idx, score in zip(top_results.indices.tolist(), top_results.values.tolist()):
        doc = documents[doc_idx]
        retrieved_docs.append((doc_idx, doc, float(score)))

    # RERANK PART
    top_for_rerank = retrieved_docs[:5]
    pairs = [[text, doc] for _, doc, _ in top_for_rerank]

    rerank_scores = reranker.predict(pairs)

    reranked = sorted(
        zip(top_for_rerank, rerank_scores),
        key=lambda x: x[1],
        reverse=True
    )

    # return only texts
    return [x[0][1] for x in reranked][:num_docs_to_return]


def get_model_response_with_rag(client, retriever, reranker, text, documents, doc_embs, last_response):
    documents_to_llm = get_relevant_documents(text, documents, doc_embs, 3, retriever, reranker)

    system_prompt = """You are a medieval person. Continue the conversation concisely based on the knowledge provided in following chunks:\n"""

    chunks = ""
    for i, doc in enumerate(documents_to_llm):
        chunks += f"[CHUNK {i+1}]\n{doc}\n"

    system_prompt += chunks

    # system_prompt += "Your last response was:\n" + last_response + "\n"

    # LLM PART
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": text
        },
    ]

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        temperature=0.5,
        max_tokens=500
    )

    answer = response.choices[0].message.content

    return text, chunks, answer
