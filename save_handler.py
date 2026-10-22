#imports 
import json
from xml.dom.minidom import Node

#from networkx import nodes
import world_generation
import resource_nodes
from pathlib import Path

TILE_LENGTH = 2
NODELAYER = 2
VERSION = "0.4.3"
SAVE_PATH = Path(__file__).with_name("saves")

#### Save Handler

""" Create File
    Input =========
    Path path (Path to file)
    Output ========
    success bool (True if file created successfully, False otherwise)
"""
def create_file(path):

    bool = False

    #create file path, str check
    path = Path(path)

    #create file
    path.parent.mkdir(parents=True, exist_ok=True)

    #create file
    with open(f"{path}", "a", encoding="utf-8") as file:
        #print success
        print(f"file created succesfully at: {path}\n")
        bool = True

    #return success
    return bool

""" Create tile entity save data
    Input =========
    Path path (Path to save file)
    Entity list (Entity data)
    Output ========
    N/A
"""
def create_entity_file(path, entities):

    #create entity save file
    create_file(Path(f"{path}.entities"))

    #create entity list
    entity_list = [
        {"x": x, "y": y, **entity}
        for (x, y), entity in entities.items()
        ]

    #write entity data to file
    with open(f"{path}.entities", "w", encoding="utf-8") as file:
        json.dump(entity_list, file, indent=4)

""" Load tile entity save data
    Input =========
    Path path (Path to save file)
    Output ========
    Entity list (Entity data)
"""
def load_entity(path):

    #open entity save file and read data
    with open(f"{path}.entities", "r", encoding="utf-8") as file:
        entity_list = json.load(file)

    #create entity data dictionary
    entities = {}
    for entity in entity_list:
        entities[(entity["x"], entity["y"])] = {
        
            # Entity type
            "machine_id": entity["machine_id"],
        
            # Display name
            "orientation": entity["orientation"],
        
            # Identifier for the entity type
            "orientation_name": entity["orientation_name"],
        }
    
    #return entity data
    return entities

""" Save tile entity save data
    Input =========
    Path path (Path to save file)
    Entity list (Entity data)
    Output ========
    N/A
"""
def save_entitys(path, entities):
    #create entity list
    entity_list = [
        {"x": x, "y": y, **entity}
        for (x, y), entity in entities.items()
    ]

    #open entity save file and write data
    with open(f"{path}.entities", "w", encoding="utf-8") as file:
        json.dump(entity_list, file, indent=4)
        print("entity save saved succesfully\n")

""" Create Node save data
    Input =========
    Path path (Path to save file)
    Node list (Node data)
    Output ========
    N/A
"""
def create_node_file(path, nodes):

    #create node save file
    create_file(Path(f"{path}.nodes"))

    #create node list
    node_list = [
        {"x": x, "y": y, **node}
        for (x, y), node in nodes.items()
        ]

    #write node data to file
    with open(f"{path}.nodes", "w", encoding="utf-8") as file:
        json.dump(node_list, file, indent=4)

""" Load Node save data
    Input =========
    Path path (Path to save file)
    Output ========
    Node list (Node data)
"""
def load_nodes(path):

    #open node save file and read data
    with open(f"{path}.nodes", "r", encoding="utf-8") as file:
        node_list = json.load(file)

    #create node data dictionary
    nodes = {}
    for node in node_list:
        nodes[(node["x"], node["y"])] = {
        
            # Resource type
            "resource": node["resource"],

            # Display name
            "name": node["name"],
        
            # Identifier for the resource type
            "id": node["id"],
        
            # Low / Medium / High
            "concentration": node["concentration"],
        
            # How much can be extracted per second
            "resource_per_second": node["resource_per_second"],
        
            # How much resource remains in the node
            "resources_remaining": node["resources_remaining"]
        }
    
    #return node data
    return nodes

""" Save Node save data
    Input =========
    Path path (Path to save file)
    Node list (Node data)
    Output ========
    N/A
"""
def save_nodes(path, nodes):
    node_list = [
        {"x": x, "y": y, **node}
        for (x, y), node in nodes.items()
    ]

    #open node save file and write data
    with open(f"{path}.nodes", "w", encoding="utf-8") as file:
        json.dump(node_list, file, indent=4)
        print("node save saved succesfully\n")

""" Create World
    Input =========
    Path path (Path to save file)
    Seed int
    World Size
    World radius 
    Output ========
    World list
    Seed int
"""
def create_world_file(path, seed, size, radius):

    #create world file
    create_file(Path(f"{path}.dat"))


    #access world
    with open(f"{path}.dat","w+b") as file:

        file.seek(0x00)

        #write world size as hex
        file.write(size.to_bytes(length=8, byteorder='big', signed=False))

        #create world
        world, seed = world_generation.generate_world(seed)
        nodes = resource_nodes.generate_resource_nodes(seed, radius)

        #write world to save
        file.seek(0x30)
        for x in range(-radius, radius + 1):
            for y in range(-radius, radius + 1):
                file.write(int(world[(x,y)]).to_bytes(length=TILE_LENGTH, byteorder='big', signed=False))

        #write resource nodes to save
        file.seek(0x30 + (size * TILE_LENGTH * NODELAYER))
        for x in range(-radius, radius + 1):
            for y in range(-radius, radius + 1):

                #get resource node if it exists
                if(nodes.get((x,y))):
                    resource_node_temp = nodes[(x,y)]
                    resource_node = resource_node_temp["id"]
                else:
                    resource_node = 0

                #write resource node to save
                file.write(int(resource_node).to_bytes(length=TILE_LENGTH, byteorder='big', signed=False))

    #create node save file
    create_node_file(path, nodes)

    #return world and seed
    return world, nodes, seed

""" Get World
    Input =========
    Path path (Path to save file)
    World radius int 
    Output ========
    World list
"""
def get_world(path, radius):

    #make return variable
    world = {}

    #open world file and read data
    with open(f"{path}.dat", "r+b") as file:

        #skip to world data
        file.seek(0x30)

        #read world data
        for x in range(-radius, radius + 1):
            for y in range(-radius, radius + 1):
                world[(x,y)] = str(int.from_bytes(file.read(TILE_LENGTH), byteorder='big', signed=False))

    # return world
    return world

"""World Save
    Input =========
    Path path (Path to save file)
    World list
    World radius 
    Output ========
    N/A
"""
def save_world(path, world, nodes, radius, size):

    #open world file and write data
    with open(f"{path}.dat", "r+b") as file:
        file.seek(0x30)
        for x in range(-radius, radius + 1):
            for y in range(-radius, radius + 1):
                file.write(int(world[(x,y)]).to_bytes(length=TILE_LENGTH, byteorder='big', signed=False))

        #write resource nodes to save
        file.seek(0x30 + ((size * TILE_LENGTH * NODELAYER)))
        for x in range(-radius, radius + 1):
            for y in range(-radius, radius + 1):

                #get resource node if it exists
                if(nodes.get((x,y))):
                    resource_node_temp = nodes[(x,y)]
                    resource_node = resource_node_temp["id"]
                else:
                    resource_node = 0

                #write resource node to save
                file.write(int(resource_node).to_bytes(length=TILE_LENGTH, byteorder='big', signed=False))

""" Create Character File
    Input =========
    Path path (Path to save file)
    Name str (Character Name)
    Output ========
    Character list (Character data)
"""
def create_character_file(save, posx, posy, inventory):

    #create character file
    create_file(Path(f"{save}.player"))

    #create character data
    data = [{
        "Pos" : [posx, posy],
        "inventory" : {},
        "version" : VERSION,
        "last_saved" : 0.0
    }]

    #write character data to file
    with open(f"{save}.player", "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

    #return character data
    return data

""" Load Character File
    Input =========
    CharacterP (Path to character file)
    Character list (Character data)
    Output ========
    N/A
"""
def load_character(path):

    #open character file and read data
    with open(f"{path}.player", "r", encoding="utf-8") as file:
        data = json.load(file)

    #update character data
    return data

""" Save Character File
    Input =========
    CharacterP (Path to character file)
    Characters list (Character data)
    Output ========
    N/A
"""
def save_character(path, characters):

    #open character file and write data
    with open(f"{path}.player", "w", encoding="utf-8") as file:
        json.dump(characters, file, indent=4)
        print("character saved succesfully\n")

""" Create Save File
    Input =========
    Name str (Save Name)
    Output ========
    Name str (Path to save file)
"""
def create_save_file(name):

    # store save name
    sName = name

    # default save file
    data = {
        "name" : f"{sName}",
        "world" : f"{sName}.dat",
        "none" : f"{sName}.nodes",
        "entities" : f"{sName}.entities",
        "players" : f"{sName}.players",
        "version" : VERSION,
        "last_saved" : 0.0
    }

    # if save file already exists
    while Path(f"{SAVE_PATH}/{name}/{sName}.sav").exists():
        name += "_"

    # create save file directory
    file_path = Path(f"{SAVE_PATH}/{name}/{sName}")
    create_file(f"{file_path}.sav")

    # create save file
    with open(f"{file_path}.sav", "a", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
        print("save file created succesfully\n")

    #return path name
    return file_path

""" Load Save File
    Input =========
    Path str (Path to save file)
    Output ========
    Data dict (Save file data)
"""
def load_save(path):

    # open save file and read data
    with open(f"{path}.sav", "r", encoding="utf-8") as file:
        data = json.load(file)

    # return save file data
    return data

""" Save Save File
    Input =========
    Path str (Path to save file)
    Data dict (Save file data)
    Output ========
    N/A
"""
def save_save(path, data):

    # open save file and write data
    with open(f"{path}.sav", "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
        print("save file saved succesfully\n")

""" List Saves
    Input =========
    N/A
    Output ========
    Path list (List of save file paths)
    Output ========
    Path list (List of save file paths)
"""
def list_saves():
    path_list = []
    for file in Path(SAVE_PATH).glob("**/*.sav"):
        data = json.load(open(file, "r", encoding="utf-8"))
        if data["version"] == VERSION:
            filepath = Path(file).with_suffix('')
            path_list.append(filepath)

    #return list of save file paths
    return path_list
