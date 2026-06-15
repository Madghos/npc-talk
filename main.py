import tkinter as tk
from tkinter import messagebox, ttk
from load import load_models, encode_documents
from rag_functions import get_model_response
from process_response import process_response

player_info = {"inventory": [], "money": 5, "quests": []}

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
    "knowledge": [
        "You are a blacksmith in the village of Puddlewater.",
        "You are known for your skill in crafting tools, weapons and armor.",
        "You have a son named Timmy who is learning the trade.",
        "You recently acquired a rare ore that can be used to craft powerful weapons.",
        "A year ago the village was attacked by a band of goblins.",
        "It is late spring now, but the weather has been unusually cold and rainy.",
        "You have a lot of work to do.",
        "Villagers complain about a pack of wolves in the nearby forest.",
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

class GameGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RPG NPC Talk Engine")
        self.root.geometry("900x600")
        self.root.configure(bg="#2c3e50")

        print("Loading AI models... Please wait...")
        model_name = "gpt-4.1-mini"
        retriever_name = "BAAI/bge-small-en-v1.5"
        self.client, self.retriever = load_models(retriever_name)
        self.enc_documents = encode_documents(self.retriever, npc_info["knowledge"])
        self.conversation_history = []
        self.model_name = model_name

        self.setup_ui()
        self.append_to_chat("NPC: Greetings, traveler!")

    def setup_ui(self):
        self.left_panel = tk.Frame(self.root, bg="#34495e", width=250)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        avatar_art = "\n\n   O   \n  /|\\  \n  / \\  \n\n[ NPC ]"
        self.avatar_label = tk.Label(self.left_panel, text=avatar_art, font=("Courier", 16, "bold"), 
                                     bg="#34495e", fg="#ecf0f1", justify=tk.CENTER)
        self.avatar_label.pack(pady=20)

        self.stats_label = tk.Label(self.left_panel, text=f"Your Gold: {player_info['money']}g", 
                                    font=("Arial", 12, "bold"), bg="#34495e", fg="#f1c40f")
        self.stats_label.pack(pady=10)

        self.right_panel = tk.Frame(self.root, bg="#2c3e50")
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.chat_frame = tk.Frame(self.right_panel)
        self.chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.chat_text = tk.Text(self.chat_frame, wrap=tk.WORD, state=tk.DISABLED, bg="#ffffff", fg="#333333", font=("Arial", 11))
        self.chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = tk.Scrollbar(self.chat_frame, command=self.chat_text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_text.config(yscrollcommand=self.scrollbar.set)

        self.entry_frame = tk.Frame(self.right_panel, bg="#2c3e50")
        self.entry_frame.pack(fill=tk.X)

        self.user_entry = tk.Entry(self.entry_frame, font=("Arial", 12))
        self.user_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=4)
        self.user_entry.bind("<Return>", lambda event: self.send_message())

        self.send_button = tk.Button(self.entry_frame, text="Talk", command=self.send_message, bg="#2ecc71", fg="white", font=("Arial", 10, "bold"), width=10)
        self.send_button.pack(side=tk.RIGHT)

        self.menu_frame = tk.Frame(self.right_panel, bg="#2c3e50")
        self.menu_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Button(self.menu_frame, text="My Inventory", command=self.show_player_inv).pack(side=tk.LEFT, padx=5)
        tk.Button(self.menu_frame, text="NPC Inventory", command=self.show_npc_inv).pack(side=tk.LEFT, padx=5)
        tk.Button(self.menu_frame, text="Quests", command=self.show_quests).pack(side=tk.LEFT, padx=5)
        tk.Button(self.menu_frame, text="Complete Quest", command=self.complete_first_quest).pack(side=tk.LEFT, padx=5)

    def append_to_chat(self, message):
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, message + "\n\n")
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)

    def send_message(self):
        user_input = self.user_entry.get().strip()
        if not user_input:
            return

        self.user_entry.delete(0, tk.END)
        self.append_to_chat(f"You: {user_input}")

        text, chunks, response, other_info = get_model_response(
            self.client, self.model_name, self.retriever, user_input,
            player_info, npc_info, self.enc_documents, self.conversation_history
        )

        item_msg, money_msg, offered_item, offered_quest = process_response(
            player_info, npc_info, text, response, other_info
        )

        speaker = npc_info['name'] if npc_info["name_known"] else "NPC"
        self.append_to_chat(f"{speaker}: {response}")

        if item_msg:
            self.append_to_chat(f"[SYSTEM]: {item_msg}")
        if money_msg:
            self.append_to_chat(f"[SYSTEM]: {money_msg}")

        self.stats_label.config(text=f"Your Gold: {player_info['money']}g")

        if offered_item.get("item"):
            self.handle_item_offer(offered_item)

        if offered_quest:
            self.handle_quest_offer(offered_quest)

        self.conversation_history.append({"role": "user", "content": text})
        self.conversation_history.append({"role": "assistant", "content": response})
        self.conversation_history = self.conversation_history[-20:]

    def handle_item_offer(self, offered_item):
        item = offered_item["item"]
        price = offered_item["price"]
        buy = messagebox.askyesno("Trade Offer", f"Do you want to buy {item} for {price} gold?")
        if buy:
            if player_info.get("money", 0) >= price:
                player_info["money"] -= price
                npc_info["money"] += price
                player_info["inventory"].append(item)
                del npc_info["inventory"][item]
                messagebox.showinfo("Success", f"You bought {item}!")
                self.stats_label.config(text=f"Your Gold: {player_info['money']}g")
            else:
                messagebox.showerror("Error", "You do not have enough gold!")

    def handle_quest_offer(self, offered_quest):
        accept = messagebox.askyesno("New Quest", f"Do you accept the quest: {offered_quest}?")
        quest = next((q for q in npc_info["quests"] if q["name"].lower() == offered_quest.lower()), None)
        if quest:
            quest_id = npc_info["quests"].index(quest)
            if accept:
                player_info["quests"].append(quest)
                npc_info["quests"][quest_id]["status"] = "accepted"
                messagebox.showinfo("Quest", f"Accepted quest: {offered_quest}!")
            else:
                messagebox.showinfo("Quest", "Quest declined.")

    def show_player_inv(self):
        items = "\n".join(player_info["inventory"]) if player_info["inventory"] else "(Empty)"
        messagebox.showinfo("Your Inventory", f"Items:\n{items}")

    def show_npc_inv(self):
        items = "\n".join([f"- {k} ({v} gold)" for k, v in npc_info["inventory"].items()])
        messagebox.showinfo("Npc inventory", f"{items}\n\nGold: {npc_info['money']}g")

    def show_quests(self):
        if not player_info["quests"]:
            messagebox.showinfo("Quests", "No active quests.")
        else:
            quests_txt = ""
            for idx, q in enumerate(player_info["quests"]):
                quests_txt += f"[{idx}] {q['name']}: {q['description']}\n"
            messagebox.showinfo("Your Quests", quests_txt)

    def complete_first_quest(self):
        if not player_info["quests"]:
            messagebox.showinfo("Quest", "No active quests.")
            return

        quest = player_info["quests"][0]

        npc_quest = next(
            (q for q in npc_info["quests"]
            if q["name"].lower() == quest["name"].lower()),
            None
        )

        if npc_quest:
            quest_id = npc_info["quests"].index(npc_quest)

            npc_info["quests"][quest_id]["status"] = "due_reward"

            completed_name = quest["name"]
            player_info["quests"].pop(0)

            messagebox.showinfo(
                "Quest Completed",
                f"[QUEST COMPLETED] {completed_name}"
            )

if __name__ == "__main__":
    root = tk.Tk()
    app = GameGUI(root)
    root.mainloop()
