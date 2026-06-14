import torch
from sentence_transformers import util
import json
from system_prompt import get_system_prompt


def get_chunks(text, npc_knowledge, embeddings, num_chunks_to_return, retriever):
    query_for_embedding = "[query]: " + text
    query_emb = retriever.encode(
        [query_for_embedding],
        convert_to_tensor=True,
        show_progress_bar=False
    )

    scores = util.cos_sim(query_emb, embeddings)[0]

    top_k = min(10, len(npc_knowledge))
    top_results = torch.topk(scores, k=top_k)

    retrieved_chunks = []
    for chunk_idx, score in zip(top_results.indices.tolist(), top_results.values.tolist()):
        chunk = npc_knowledge[chunk_idx]
        retrieved_chunks.append((chunk_idx, chunk, float(score)))
    return [chunk for _, chunk, _ in retrieved_chunks][:num_chunks_to_return]


def get_model_response(client, model_name, retriever, text, player_info, npc_info, doc_embs, conversation_history):
    knowledge_to_llm = get_chunks(text, npc_info["knowledge"], doc_embs, 3, retriever)

    chunks = ""
    for i, doc in enumerate(knowledge_to_llm):
        chunks += f"[CHUNK {i+1}]\n{doc}\n"

    system_prompt = get_system_prompt(npc_info, player_info, chunks)

    # print("\n[SYSTEM PROMPT]\n")
    # print(system_prompt)

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    messages.extend(conversation_history)

    messages.append({
        "role": "user",
        "content": text
    })

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.5,
        max_tokens=100,
        response_format={"type": "json_object"}
    )

    raw_response = response.choices[0].message.content

    # print("\n[MODEL RESPONSE]\n")
    # print(raw_response)

    data = json.loads(raw_response)

    answer = data["message"]
    other_info = {
        "revealed_name": data.get("revealed_name", False),
        "action": data.get("action", "none"),
        "item_name": data.get("item_name", ""),
        "money_amount": int(data.get("money_amount", 0) or 0),
        "quest_name": data.get("quest_name", "")
    }

    return text, chunks, answer, other_info
