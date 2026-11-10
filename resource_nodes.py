# imports
import pygame
import json
import random
from pathlib import Path



# Find the resource JSON file for resource info
resource_file = Path(__file__).with_name("resource_nodes.json")


# LOAD RESOURCE INFORMATION

# loads resource info from json
def load_resource_types():
    # Open the resource information JSON file
    with resource_file.open("r", encoding="utf-8") as file:

        # Turn the JSON data into Python data
        data = json.load(file)

    # Return the resource information
    return data["resources"]

# Load the resource information when this file starts
resource_types = load_resource_types()


# GENERATE RESOURCE NODES

#generates resource nodes based on world seed and radius
def generate_resource_nodes(world_seed, world_radius):

    # Create a random generator using the world seed
    # This makes the same seed create the same resource locations
    random_generator = random.Random(
        str(world_seed) + "_resources"
    )

    # Holds all generated resource nodes
    #
    # Example:
    # {
    # (5, 10): {...},
    # (6, 10): {...}
    # }
    resource_nodes = {}

    # Keeps track of tiles that already contain a resource
    occupied_tiles = set()

    # Determine how many clusters to create
    cluster_count = max(
        3,
        (world_radius * 2 + 1) // 8
    )


    # CREATE RESOURCE CLUSTERS

    for cluster_number in range(cluster_count):

        # Pick a random center for this cluster
        center_x = random_generator.randint(
            -world_radius,
            world_radius
        )

        center_y = random_generator.randint(
            -world_radius,
            world_radius
        )

        # Pick the resource type for this cluster
        resource_id = random_generator.choice(
            list(resource_types.keys())
        )

        # Get information about this resource
        resource_info = resource_types[resource_id]

        # Determine how many nodes this cluster will contain
        minimum_nodes = resource_info["cluster_size"]["minimum"]
        maximum_nodes = resource_info["cluster_size"]["maximum"]

        node_count = random_generator.randint(
            minimum_nodes,
            maximum_nodes
        )


        # CREATE NODES IN CLUSTER

        for node_number in range(node_count):

            # Try several times to find an empty tile
            for attempt in range(20):

                # How far the node can be from the cluster center
                spread = resource_info["cluster_size"]["spread"]

                # Pick a random position around the center
                node_x = center_x + random_generator.randint(
                    -spread,
                    spread
                )

                node_y = center_y + random_generator.randint(
                    -spread,
                    spread
                )

                # Make sure the node is inside the world
                if not (
                    -world_radius <= node_x <= world_radius
                    and
                    -world_radius <= node_y <= world_radius
                ):
                    continue

                # Don't place two nodes on the same tile
                if (node_x, node_y) in occupied_tiles:
                    continue

                # Mark this tile as occupied
                occupied_tiles.add((node_x, node_y))

                # Pick Low, Medium, or High concentration
                concentration = choose_concentration(
                    random_generator
                )

                # Get the extraction rate for the concentration
                resource_per_second = resource_info[
                    "concentration"
                ][concentration]["resource_per_second"]

                # Get the starting amount of resources
                starting_amount = resource_info[
                    "concentration"
                ][concentration]["starting_amount"]

                # Store the resource node
                resource_nodes[(node_x, node_y)] = {

                    # Resource type
                    "resource": resource_id,

                    # Display name
                    "name": resource_info["name"],

                    # Identifier for the resource type
                    "id": resource_info["id"],

                    # Low / Medium / High
                    "concentration": concentration,

                    # How much can be extracted per second
                    "resource_per_second": resource_per_second,

                    # How much resource remains in the node
                    "resources_remaining": starting_amount
                }

                # Stop trying to place this node
                break

    # Return all resource nodes
    return resource_nodes


# CHOOSE CONCENTRATION

#Rolls 1-100 to decide concentration rarity: 50% low, 35% medium, 15% high
def choose_concentration(random_generator):

    # Generate a number from 1 to 100
    concentration_number = random_generator.randint(1, 100)

    # 50% chance of Low
    if concentration_number <= 50:
        return "low"

    # 35% chance of Medium
    elif concentration_number <= 85:
        return "medium"

    # 15% chance of High
    else:
        return "high"


# DRAW RESOURCE NODES

# draw_resource_nodes 
def draw_resource_nodes(
    screen,
    resource_nodes,
    camera_x,
    camera_y,
    screen_width,
    screen_height,
    pixel_size
):

    # Determine how many tiles are visible
    tiles_x = screen_width // pixel_size + 2
    tiles_y = screen_height // pixel_size + 2

    # Determine the center of the visible area
    half_tiles_x = tiles_x // 2
    half_tiles_y = tiles_y // 2

    # Look through every resource node
    for (x, y), node in resource_nodes.items():

        # Don't draw nodes outside the visible area
        if not (
            camera_x - half_tiles_x <= x <= camera_x + half_tiles_x
            and
            camera_y - half_tiles_y <= y <= camera_y + half_tiles_y
        ):
            continue

        # Get information about this resource
        resource_info = resource_types[node["resource"]]

        # Get the colors from the JSON
        primary_color = tuple(
            resource_info["primary_color"]
        )

        secondary_color = tuple(
            resource_info["secondary_color"]
        )

        # Convert world coordinates into screen coordinates
        screen_x = (
            screen_width // 2
            + (x - camera_x) * pixel_size
        )

        screen_y = (
            screen_height // 2
            + (y - camera_y) * pixel_size
        )

        # Create a random generator specifically for this node
        # This makes the rocks stay in the same positions
        # instead of moving every frame.
        node_random = random.Random(
            str(node["resource"])
            + "_"
            + str(x)
            + "_"
            + str(y)
        )

        # Determine how many rocks this node has
        minimum_rocks = resource_info[
            "appearance"
        ]["rocks"]["minimum"]

        maximum_rocks = resource_info[
            "appearance"
        ]["rocks"]["maximum"]

        rock_count = node_random.randint(
            minimum_rocks,
            maximum_rocks
        )


        # DRAW THE ROCKS
        for rock_number in range(rock_count):

            # Pick a random position inside the tile
            rock_x = screen_x + node_random.randint(
                pixel_size // 5,
                pixel_size - pixel_size // 5
            )

            rock_y = screen_y + node_random.randint(
                pixel_size // 5,
                pixel_size - pixel_size // 5
            )

            # Pick a random rock size
            rock_size = node_random.randint(
                pixel_size // 6,
                pixel_size // 3
            )

            # Create an irregular rock shape
            points = [
                (rock_x - rock_size, rock_y),
                (rock_x - rock_size // 2, rock_y - rock_size),
                (rock_x + rock_size // 2, rock_y - rock_size // 2),
                (rock_x + rock_size, rock_y),
                (rock_x + rock_size // 2, rock_y + rock_size),
                (rock_x - rock_size // 2, rock_y + rock_size // 2)
            ]

            # Draw the main rock
            pygame.draw.polygon(
                screen,
                primary_color,
                points
            )

            # Create a line across the rock
            # using the secondary resource color
            line_start = (
                rock_x - rock_size // 2,
                rock_y - rock_size // 3
            )

            line_end = (
                rock_x + rock_size // 2,
                rock_y + rock_size // 3
            )

            # Draw the secondary-colored line
            pygame.draw.line(
                screen,
                secondary_color,
                line_start,
                line_end,
                max(1, pixel_size // 16)
            )