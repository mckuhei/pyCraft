import os
import json
import re

class AssetsManager:

    def __init__(self, directory, lang="en_us"):
        self.lang = {}
        self.directory = directory
        
        if not os.path.isdir(directory):
            raise FileNotFoundError("%s is not a valid directory")

        if not os.path.isfile("%s/models/block/block.json"%(directory)):
            raise FileNotFoundError("%s is not a valid assets directory"%(directory))
        
        with open("%s/lang/%s.json"%(directory, lang)) as f:
            self.lang = json.loads(f.read())
            for x in self.lang:
                self.lang[x] = re.sub("\%\d+\$s", "%s", self.lang[x]) # HACK
    
    def translate(self, key, extra=[]):
        if key not in self.lang:
            return "[%?]"%(key)
        if extra:
            return self.lang[key]%tuple(extra)
        else:
            return self.lang[key]

    def get_block_variant(self, name, properties={}):
        if name.startswith("minecraft:"):
            name = name[10:]
        
        filename = "%s/blockstates/%s.json"%(self.directory, name)
        if not os.path.isfile(filename):
            raise FileNotFoundError("'%s' is not a valid block name"%(name))
        with open(filename) as f:
            variants = json.loads(f.read())['variants']

        if properties:
            k = ",".join(["%s=%s"%(x, properties[x]) for x in sorted(properties.keys())])
        else:
            k = ""
        
        if not k in variants:
            k = ""
            
        v = variants[k]
        if isinstance(v, list) and len(v)>0:
            v=v[0] # HACK
        return v

    def get_model(self, path, recursive=True):
        filename = "%s/models/%s.json"%(self.directory, path)
        if not os.path.isfile(filename):
            raise FileNotFoundError("'%s' is not a valid model path"%(path))
        with open(filename) as f:
            model = json.loads(f.read())
        
        if recursive and 'parent' in model:
            parent = self.get_model(model['parent'])
            for x in parent:
                a = parent[x]
                if x in model:
                    a.update(model[x])
                model[x] = a
            del(model['parent'])
        
        return model
        
    def get_faces_textures(self, model):
        if 'textures' not in model or 'elements' not in model:
            return {}
        textures = model['textures']
        faces = {}
        for e in model['elements']:
            for x in e['faces']:
                if x in faces:
                    continue
                faces[x] = e['faces'][x]
                while faces[x]['texture'].startswith("#"):
                    # TODO: Raise exception on max iteration
                    faces[x]['texture'] = textures[faces[x]['texture'][1:]]
        return faces
        
