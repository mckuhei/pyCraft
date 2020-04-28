import os
import json
import re

class AssetsManager:

    def __init__(self, directory, lang="en_us"):
        self.lang = {}
        
        if not os.path.isdir(directory):
            raise FileNotFoundError("%s is not a valid directory")

        if not os.path.isfile("%s/models/block/block.json"%(directory)):
            raise FileNotFoundError("%s is not a valid assets directory")
        
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
