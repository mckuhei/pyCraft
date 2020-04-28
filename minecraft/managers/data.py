import os
import json

class DataManager:

    def __init__(self, directory):
        self.blocks = {}
        self.blocks_states = {}
        self.registries = {}
        self.biomes = {}
        
        if not os.path.isdir(directory):
            raise FileNotFoundError("%s is not a valid directory")

        if not os.path.isfile("%s/registries.json"%(directory)):
            raise FileNotFoundError("%s is not a valid minecraft data directory")
        
        with open("%s/blocks.json"%(directory)) as f:
            blocks = json.loads(f.read())
        for x in blocks:
            for s in blocks[x]['states']:
                self.blocks_states[s['id']] = x

        with open("%s/registries.json"%(directory)) as f:
            registries = json.loads(f.read())
        for x in registries["minecraft:biome"]["entries"]:
            self.biomes[registries["minecraft:biome"]["entries"][x]["protocol_id"]] = x
