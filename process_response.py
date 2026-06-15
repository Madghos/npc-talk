

def process_response(player_info, npc_info, text, response, other_info):
    item_msg = None
    money_msg = None
    offered_item = {
        "item": None,
        "price": None,
    }
    offered_quest_name = ""

    # reveal NPC name
    if other_info["revealed_name"]:
        if npc_info["name"] in response:
            npc_info["name_known"] = True

    # give item to player
    if other_info["action"] == "give_item":
        item = other_info.get("item_name", "") or ""
        npc_inv = npc_info.get("inventory", {})

        match = next((it for it in npc_inv if it.lower() == item.lower()), None)

        if not match:
            item_msg = f"\n[NPC DOESN'T HAVE ITEM] {item}"
        else:
            player_info["inventory"].append(match)
            del npc_info["inventory"][match]
            item_msg = f"\n[ITEM RECEIVED] {match}"
                
    # sell item to player
    if other_info["action"] == "offer_item":
        item = other_info.get("item_name", "") or ""
        npc_inv = npc_info.get("inventory", {})
        
        match = next((it for it in npc_inv if it.lower() == item.lower()), None)

        if not match:
            item_msg = f"\n[NPC DOESN'T HAVE ITEM] {item}"
        else:
            price = npc_info["inventory"][match]
            if player_info.get("money", 0) < price:
                item_msg = f"\n[NOT ENOUGH GOLD] You need {price} gold to buy {match}"
            else:
                offered_item["item"] = match
                offered_item["price"] = price

    # give money to player
    if other_info["action"] == "give_money":
        amt = int(other_info.get("money_amount", 0) or 0)
        if amt <= 0:
            money_msg = f"\n[INVALID AMOUNT] {amt}"
        else:
            npc_money = npc_info.get("money", 0)
            if npc_money >= amt:
                player_info["money"] += amt
                npc_info["money"] = npc_money - amt
                money_msg = f"\n[MONEY RECEIVED] {amt} gold"
            else:
                money_msg = f"\n[NPC CANNOT AFFORD] {amt} gold"

    # offer quest to player
    if other_info["action"] == "offer_quest":
        quest_name = other_info.get("quest_name", "") or ""
        npc_quests = npc_info.get("quests", [])
        
        match = next((q for q in npc_quests if q["name"].lower() == quest_name.lower()), None)

        if not match:
            item_msg = f"\n[NPC DOESN'T HAVE QUEST] {quest_name}"
        else:
            if match["status"] in ["accepted", "due_reward"]:
                item_msg = f"\n[QUEST ALREADY ACCEPTED] {match['name']}"
            elif match["status"] == "completed":
                item_msg = f"\n[QUEST ALREADY COMPLETED] {match['name']}"
            else:
                offered_quest_name = match['name']

    # give reward to player
    if other_info["action"] == "give_reward":
        quest_name = other_info.get("quest_name", "") or ""
        npc_quests = npc_info.get("quests", [])
        
        match = next((q for q in npc_quests if q["name"].lower() == quest_name.lower()), {})
        quest_id = npc_info["quests"].index(match)

        if npc_info["quests"][quest_id]["status"] == "due_reward":
            item = match.get("reward_item", "") or ""
            money = match.get("reward_money", 0) or 0

            player_info["inventory"].append(item)
            item_msg = f"\n[ITEM RECEIVED] {item}"

            player_info["money"] += money
            money_msg = f"\n[MONEY RECEIVED] {money} gold"

            npc_info["quests"][quest_id]["status"] = "completed"

        else:
            item_msg = f"\n[QUEST ALREADY COMPLETED] {match['name']}"

    return item_msg, money_msg, offered_item, offered_quest_name
