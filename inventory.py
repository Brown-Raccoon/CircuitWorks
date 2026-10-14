# imports
import json
from pathlib import Path


# path to the item definition file
ITEM_FILE = Path(__file__).with_name("item_definitions.json")


# load all valid item definitions from JSON
def load_item_definitions():
    with ITEM_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data["items"]


# load item definitions when this file starts
item_definitions = load_item_definitions()


class Inventory:
    def __init__(self):
        # stores an inventory like:
        # {
        #     "copper_wire": 10,
        #     "miner": 2
        # }
        self.items = {}


    # adds an amount of an item to the inventory
    def add_item(self, item_key, amount=1):

        # make sure this item exists in item_definitions.json
        if item_key not in item_definitions:
            print(f"Item '{item_key}' does not exist.")
            return False

        # do not allow zero or negative amounts
        if amount <= 0:
            return False

        # get current amount, or 0 if the player does not have the item yet
        current_amount = self.items.get(item_key, 0)

        # add the new amount
        # stack_size is kept in the item definition for a future slot-based UI,
        # but it does not limit the player's total quantity here
        self.items[item_key] = current_amount + amount

        return True


    # removes an amount of an item from the inventory
    def remove_item(self, item_key, amount=1):

        # do not allow zero or negative amounts
        if amount <= 0:
            return False

        # make sure the player has enough of the item
        if not self.has_item(item_key, amount):
            return False

        # subtract the amount
        self.items[item_key] -= amount

        # remove the item completely if the quantity reaches 0
        if self.items[item_key] == 0:
            del self.items[item_key]

        return True


    # returns how many of an item the player currently has
    def get_quantity(self, item_key):
        return self.items.get(item_key, 0)


    # checks if the player has at least a certain amount of an item
    def has_item(self, item_key, amount=1):
        return self.get_quantity(item_key) >= amount


    # returns all items currently in the inventory
    def get_all_items(self):
        return self.items.copy()


    # removes everything from the inventory
    def clear(self):
        self.items.clear()


    # returns inventory data in a JSON-save-friendly format
    def to_dict(self):
        return self.items.copy()


    # loads inventory data from a saved dictionary
    def load_dict(self, saved_inventory):

        # start with an empty inventory
        self.items.clear()

        # ignore invalid save data
        if not isinstance(saved_inventory, dict):
            return False

        # only load valid items with positive quantities
        for item_key, amount in saved_inventory.items():

            if item_key not in item_definitions:
                continue

            if not isinstance(amount, int) or amount <= 0:
                continue

            self.items[item_key] = amount

        return True
