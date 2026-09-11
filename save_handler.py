#imports Frank Kates what the actual fuck so let's go to real generation can't believe Frank Kates what the actual fuck so let's go to real generation can't believe what the Frank Kates what the actual fuck so let's go to real generation can't believe what the actual Frank Kates what the actual fuck so let's go to real generation can't believe what the actual fuck
import pygame
import json
import world_generation

## Get Hex
# Pos[x]
# Pos[y]
# Return Hex

## Create World
# Name str
# Seed str
# World Size
# return world
# and seed
def create_world_file(name,seed,size,radius):
    
    #create world
    with open(f"{name}.dat","a") as file:
        #print success
        print("world created succesfully\n")


    #access world
    with open(f"{name}.dat","w+b") as file:

        file.seek(0x00)

        #write world size as hex
        file.write(size.to_bytes(length=8, byteorder='big', signed=False))

        #create world
        world, seed = world_generation.generate_world(seed)

        #write world to save
        file.seek(0x30)
        for x in range(-radius, radius + 1):
            for y in range(-radius, radius + 1):
                binaryformat = bytes([int(world[(x,y)])])
                file.write(binaryformat)

    return world, seed

## Get World
# File[World]
# return str
# read from world and return array
def get_world(world, name, radius):

    with open(f"{name}.dat", "r+b") as file:
        file.seek(0x30)
        for x in range(-radius, radius + 1):
            for y in range(-radius, radius + 1):
                world[(x,y)] = int.from_bytes(file.read(1), byteorder='big', signed=False)
    return world

    

## World Save
# File[World]
def save_world(world, name, radius):

    with open(f"{name}.dat", "r+b") as file:
        file.seek(0x30)
        for x in range(-radius, radius + 1):
            for y in range(-radius, radius + 1):
                binaryformat = bytes([int(world[(x,y)])])
                file.write(binaryformat)