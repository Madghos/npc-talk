from load import load_models, encode_documents
from rag_functions import get_model_response
from process_response import process_response

player_info = {
    "inventory": [],
    "money": 5,
    "quests": [],
}

npc_info = {
    "name": "John",
    "name_known": False,
    "inventory": {
        "Mithril Ore": 300,
        "Iron Sword": 50,
        "Leather Apron": 15,
        "Old Horseshoe": 5,
        "Timmy": 100
    },
    "money": 20,
    "knowledge": ["You are a blacksmith in the village of Puddlewater.",
                  "You are known for your skill in crafting tools, weapons and armor.",
                  "You have a son named Timmy who is learning the trade.",
                  "You recently acquired a rare ore that can be used to craft powerful weapons.",
                  "A year ago the village was attacked by a band of goblins.",
                  "It is late spring now, but the weather has been unusually cold and rainy, which has affected the growth of crops in the village.",
                  "You have a lot of work to do.",
                  "Villagers complain about a pack of wolves that live in the nearby forest and have been attacking livestock.",
    ],
    "quests": [
        {
            "name": "Hungry Wolves",
            "description": "A pack of wolves has been terrorizing the village. Help the villagers by hunting down the wolves.",
            "reward_money": 100,
            "reward_item": "Leather Gloves",
            "status": "available",
        },
        {
            "name": "Carrots",
            "description": "Collect 10 carrots from the garden and bring them to me.",
            "reward_money": 50,
            "reward_item": "",
            "status": "available",
        }
    ]
}

def main():
    model_name = "gpt-4.1-mini"
    retriever_name = "BAAI/bge-small-en-v1.5"
    client, retriever = load_models(retriever_name)

    enc_documents = encode_documents(retriever, npc_info["knowledge"])

    conversation_history = []

    print("Type '/quit' or '/exit' to end the conversation.\n")
    print("Type '/inv' to view your inventory.\n")
    print("Type '/quests' to show your quests.\n")
    print("Type '/quests {id}' to complete the quest.\n")
    print("Type '/npcinv' to view NPC inventory.\n")

    print("NPC: Greetings, traveler!")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"/quit", "/exit"}:
            break

        if user_input.lower() == "/inv":
            if not player_info["inventory"]:
                print("\nYour inventory is empty.")
                print(f"\nGold: {player_info['money']}")
            else:
                print("\nYour inventory:\n")
                print('\n'.join(player_info["inventory"]))
                print(f"\nGold: {player_info['money']}")
            continue

        if user_input.lower() == "/quests":
            if not player_info["quests"]:
                print("\nYou have no active quests.")
            else:
                print("\nYour quests:\n")
                for quest in player_info["quests"]:
                    print(f"- {quest['name']}: {quest['description']}")
            continue

        if user_input.lower().split()[0] == "/quest":
            comm = user_input.lower().split()
            if len(comm) > 1:
                id = int(user_input.lower().split()[1])

                if len(player_info["quests"]) <= id:
                    print("\nInvalid quest id.")
                else:
                    quest = next((q for q in npc_info["quests"] if q["name"].lower() == player_info["quests"][id]["name"].lower()), None)
                    quest_id = npc_info["quests"].index(quest)
                    npc_info["quests"][quest_id]["status"] = "due_reward"
                    print(f"\n[QUEST COMPLETED] {player_info["quests"][id]["name"]}")
                    player_info["quests"].pop(id)
                continue

        if user_input.lower() == "/npcinv":
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

        item_msg, money_msg, offered_item, offered_quest = process_response(player_info, npc_info, text, response, other_info)

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
                    print(f"\n[ITEM RECEIVED] {item}")
                else:
                    print(f"\n[NOT ENOUGH GOLD] You need {price} gold to buy {item}")
            else:
                print(f"\n[OFFER DECLINED] You did not buy {item}.")

        if offered_quest:
            user_input = input(f"\nAccept quest: {offered_quest}? (yes/no): ").strip()

            quest = next((q for q in npc_info["quests"] if q["name"].lower() == offered_quest.lower()), None)
            quest_id = npc_info["quests"].index(quest)

            if user_input.lower() == "yes":
                player_info["quests"].append(quest)
                npc_info["quests"][quest_id]["status"] = "accepted"
                print(f"\n[QUEST ACCEPTED] {offered_quest}")
            else:
                print(f"\n[QUEST NOT ACCEPTED] {offered_quest}")

            
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
