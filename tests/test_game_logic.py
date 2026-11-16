from inventory import Inventory
from world_generation import generate_world

# World generation tests
def test_world_generation_is_reproducible():
    world_a, seed_a = generate_world(12345)
    world_b, seed_b = generate_world(12345)

    assert world_a == world_b
    assert seed_a == seed_b

# Inventory tests
def test_add_item_increases_quantity():
    inventory = Inventory()

    assert inventory.add_item("copper_wire", 5) is True
    assert inventory.get_quantity("copper_wire") == 5


def test_remove_item_decreases_quantity():
    inventory = Inventory()
    inventory.add_item("copper_wire", 5)

    assert inventory.remove_item("copper_wire", 2) is True
    assert inventory.get_quantity("copper_wire") == 3


def test_cannot_remove_more_items_than_owned():
    inventory = Inventory()
    inventory.add_item("copper_wire", 2)

    assert inventory.remove_item("copper_wire", 5) is False
    assert inventory.get_quantity("copper_wire") == 2


def test_invalid_item_is_rejected():
    inventory = Inventory()

    assert inventory.add_item("invalid_item", 1) is False


def test_inventory_data_can_be_restored():
    inventory = Inventory()
    inventory.add_item("copper_wire", 5)
    saved_data = inventory.to_dict()

    restored_inventory = Inventory()
    assert restored_inventory.load_dict(saved_data) is True
    assert restored_inventory.get_quantity("copper_wire") == 5
  
