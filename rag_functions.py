import torch
from sentence_transformers import util
import json


def get_relevant_documents(text, documents, doc_embs, num_docs_to_return, retriever):
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
    # return top documents by retrieval score
    return [doc for _, doc, _ in retrieved_docs][:num_docs_to_return]


def get_model_response_with_rag(client, model_name, retriever, text, npc_info, doc_embs, conversation_history):
    documents_to_llm = get_relevant_documents(text, npc_info["knowledge"], doc_embs, 3, retriever)

    system_prompt = f"""
    You are a medieval person.
    Your name is {npc_info["name"]}.
    Stay in character at all times.
    Continue the conversation concisely based on the knowledge provided in following chunks:\n"""

    chunks = ""
    for i, doc in enumerate(documents_to_llm):
        chunks += f"[CHUNK {i+1}]\n{doc}\n"

    system_prompt += chunks

    system_prompt += """

    You must answer ONLY in valid JSON.

    Format:

    {
        "message": "<npc response>",
        "revealed_name": false,
        "give_item": false,
        "item_name": "",
        "give_money": false,
        "money_amount": 0
    }

    Set revealed_name to true if during this response you reveal your name to the player.

    If you decide to give an item to the player:
    - set give_item to true
    - set item_name to the item's name

    Otherwise:
    - set give_item to false
    - set item_name to ""

    If you decide to give money to the player:
    - set give_money to true
    - set money_amount to the amount of money you give

    Otherwise:
    - set give_money to false
    - set money_amount to 0
    """

    # Include NPC inventory so the model knows which items are available to give
    npc_inventory = npc_info.get("inventory", [])
    system_prompt += "\nNPC INVENTORY:\n"
    for it in npc_inventory:
        system_prompt += f"- {it}\n"
    system_prompt += "\nOnly set `give_item` true if the item is present above."
    system_prompt += f"\nNPC Gold: {npc_info.get('money', 0)}"
    system_prompt += "\nOnly set `give_money` true if the NPC has at least `money_amount`."

    # LLM PART
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

    data = json.loads(raw_response)

    answer = data["message"]
    other_info = {
        "revealed_name": data.get("revealed_name", False),
        "give_item": data.get("give_item", False),
        "item_name": data.get("item_name", ""),
        "give_money": data.get("give_money", False),
        "money_amount": int(data.get("money_amount", 0) or 0),
    }

    return text, chunks, answer, other_info
