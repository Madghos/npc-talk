from load import load_models, encode_documents
from rag_functions import get_model_response
from process_response import process_response

player_info = {
    "inventory": [],
    "money": 5
}

npc_info = {
    "name": "John",
    "name_known": False,
    "inventory": {
        "Mithril Ore": 300,
        "Iron Sword": 50,
        "Leather Apron": 15,
        "Old Horseshoe": 5
    },
    "money": 20,
    "knowledge": ["You are a blacksmith in the village of Puddlewater.",
                  "You are known for your skill in crafting weapons and armor.",
                  "You have a friendly demeanor and enjoy helping travelers with their needs.",
                  "You have a son named Timmy who is learning the trade.",
                  "You recently acquired a rare ore that can be used to craft powerful weapons.",
                  "You are a member of the local blacksmith guild and often collaborate with other blacksmiths in the area.",
                  "You have a secret recipe for a special type of steel that is highly sought after by adventurers and warriors.",
                  "You have a friendly rivalry with another blacksmith in a neighboring town, and you often compete to see who can craft the best weapons and armor.",
                  "You have a small workshop where you create your masterpieces, and it's filled with various tools, materials, and half-finished projects."]
}

def main():
    model_name = "gpt-4.1-mini"
    retriever_name = "BAAI/bge-small-en-v1.5"
    client, retriever = load_models(retriever_name)

    enc_documents = encode_documents(retriever, npc_info["knowledge"])

    conversation_history = []

    print("Type 'quit' or 'exit' to end the conversation.\n")
    print("Type 'inv' to view your inventory.\n")
    print("NPC: Greetings, traveler! How may I assist you today?")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"quit", "exit"}:
            break
        if user_input.lower() == "inv":
            if not player_info["inventory"]:
                print("\nYour inventory is empty.")
                print(f"\nGold: {player_info['money']}")
            else:
                print("\nYour inventory:\n")
                print('\n'.join(player_info["inventory"]))
                print(f"\nGold: {player_info['money']}")
            continue
        if user_input.lower() == "npcinv":
            npc_inv = npc_info.get("inventory", [])
            if not npc_inv:
                print("\nNPC inventory is empty.")
                print(f"\nNPC Gold: {npc_info.get('money', 0)}")
            else:
                print("\nNPC inventory:\n")
                for item, price in npc_inv.items():
                    print(f"{item} - {price} gold")
                print(f"\nNPC Gold: {npc_info.get('money', 0)}")
            continue

        text, chunks, response, other_info = get_model_response(
            client,
            model_name,
            retriever,
            user_input,
            player_info,
            npc_info,
            enc_documents,
            conversation_history,
        )

        item_msg, money_msg, offered_item = process_response(player_info, npc_info, text, response, other_info)

        # print("\n[RAG CHUNKS USED]")
        # print(chunks)

        if npc_info["name_known"]:
            print(f"\n{npc_info['name']}:", response)
        else:
            print("\nNPC:", response)

        # Print item message after the NPC message
        if item_msg:
            print(item_msg)
        if money_msg:
            print(money_msg)
        if offered_item["item"]:
            user_input = input(f"\nBuy {offered_item['item']} for {offered_item['price']} gold? (yes/no): ").strip()
            
            item = offered_item["item"]
            if user_input.lower() == "yes":
                price = offered_item["price"]
                if player_info.get("money", 0) >= price:
                    player_info["money"] -= price
                    npc_info["money"] += price
                    player_info["inventory"].append(item)
                    del npc_info["inventory"][item]
                    item_msg = f"\n[ITEM RECEIVED] {item}"
                else:
                    item_msg = f"\n[NOT ENOUGH GOLD] You need {price} gold to buy {item}"
                print(item_msg)
            else:
                print(f"\n[OFFER DECLINED] You did not buy {item}.")

        conversation_history.append({
            "role": "user",
            "content": text
        })

        conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        conversation_history = conversation_history[-20:]

if __name__ == "__main__":
    main()
