from load import load_models, encode_documents
from rag_functions import get_model_response_with_rag

player_inventory = []
player_money = 5

npc_info = {
    "name": "John",
    "name_known": False,
    "inventory": ["Iron Sword", "Leather Apron", "Old Horseshoe"],
    "money": 20,
    "knowledge": ["You are a blacksmith in the village of Puddlewater.",
                  "You are known for your skill in crafting weapons and armor.",
                  "You have a friendly demeanor and enjoy helping travelers with their needs."]
}

def main():
    model_name = "gpt-4.1-mini"
    retriever_name = "BAAI/bge-small-en-v1.5"
    client, retriever = load_models(retriever_name)
    global player_money


    conversation_history = []

    print("Type 'quit' or 'exit' to end the conversation.\n")
    print("Type 'inv' to view your inventory.\n")
    print("NPC: Greetings, traveler! How may I assist you today?")

    while True:
        user_input = input("You: ").strip()
        if not user_input or user_input.lower() in {"quit", "exit"}:
            break
        if user_input.lower() == "inv":
            if not player_inventory:
                print("\nYour inventory is empty.")
                print(f"\nGold: {player_money}")
            else:
                print("\nYour inventory:\n")
                print('\n'.join(player_inventory))
                print(f"\nGold: {player_money}")
            continue
        if user_input.lower() == "npcinv":
            npc_inv = npc_info.get("inventory", [])
            if not npc_inv:
                print("\nNPC inventory is empty.")
                print(f"\nNPC Gold: {npc_info.get('money', 0)}")
            else:
                print("\nNPC inventory:\n")
                print('\n'.join(npc_inv))
                print(f"\nNPC Gold: {npc_info.get('money', 0)}")
            continue

        enc_documents = encode_documents(retriever, npc_info["knowledge"])

        text, chunks, response, other_info = get_model_response_with_rag(
            client,
            model_name,
            retriever,
            user_input,
            npc_info,
            enc_documents,
            conversation_history,
        )

        # Prepare any item/name/money updates but defer printing messages
        item_msg = None
        money_msg = None
        if other_info["revealed_name"]:
            npc_info["name_known"] = True
        if other_info["give_item"]:
            item = other_info.get("item_name", "") or ""
            # case-insensitive match to NPC inventory
            npc_inv = npc_info.get("inventory", [])
            match = None
            for it in npc_inv:
                if it.lower() == item.lower():
                    match = it
                    break

            if match:
                player_inventory.append(match)
                npc_info["inventory"].remove(match)
                item_msg = f"\n[ITEM RECEIVED] {match}"
            else:
                item_msg = f"\n[NPC DOESN'T HAVE ITEM] {item}"

        # handle money transfer from NPC to player
        if other_info.get("give_money"):
            amt = int(other_info.get("money_amount", 0) or 0)
            if amt <= 0:
                money_msg = f"\n[INVALID AMOUNT] {amt}"
            else:
                npc_money = npc_info.get("money", 0)
                if npc_money >= amt:
                    player_money += amt
                    npc_info["money"] = npc_money - amt
                    money_msg = f"\n[MONEY RECEIVED] {amt} gold"
                else:
                    money_msg = f"\n[NPC CANNOT AFFORD] {amt} gold"

        print("\n[RAG CHUNKS USED]")
        print(chunks)

        if npc_info["name_known"]:
            print(f"\n{npc_info['name']}:", response)
        else:
            print("\nNPC:", response)

        # Print item message after the NPC message
        if item_msg:
            print(item_msg)
        if money_msg:
            print(money_msg)

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

