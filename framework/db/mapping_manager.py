from framework.db import models
from framework.config import config
from framework.lib.exceptions import InvalidMappingReference
import os
import json
import logging
import ConfigParser


class MappingDB(object):
    def __init__(self, Core):
        """
        The mapping_types attributes contain the unique mappings in memory
        """
        self.Core = Core
        self.mapping_types = []
        self.LoadMappingDBFromFile(self.Core.Config.FrameworkConfigGet("DEFAULT_MAPPING_PROFILE"))

    def LoadMappingDBFromFile(self, file_path):
        """
        This needs to be a list instead of a dictionary to preserve order in
        python < 2.7
        """
        logging.info("Loading Mapping from: %s", file_path)
        config_parser = ConfigParser.RawConfigParser()
        # Otherwise all the keys are converted to lowercase xD
        config_parser.optionxform = str
        config_parser.read(file_path)
        for owtf_code in config_parser.sections():
            mappings = {}
            category = None
            for mapping_type, data in config_parser.items(owtf_code):
                if mapping_type != 'category':
                    if mapping_type not in self.mapping_types:
                        self.mapping_types.append(mapping_type)
                    mapped_code, mapped_name = data.split('_____')
                    mappings[mapping_type] = [mapped_code, mapped_name]
                else:
                    category = data
            self.Core.DB.session.merge(models.Mapping(
                owtf_code=owtf_code,
                mappings=json.dumps(mappings),
                category=category))
        self.Core.DB.session.commit()

    def DeriveMappingDict(self, obj):
        if obj:
            pdict = dict(obj.__dict__)
            pdict.pop("_sa_instance_state", None)
            # If output is present, json decode it
            if pdict.get("mappings", None):
                pdict["mappings"] = json.loads(pdict["mappings"])
            return pdict

    def DeriveMappingDicts(self, obj_list):
        dict_list = []
        for obj in obj_list:
            dict_list.append(self.DeriveMappingDict(obj))
        return(dict_list)

    def GetMappingTypes(self):
        """
        In memory data saved when loading db
        """
        return self.mapping_types

    def GetMappings(self, mapping_type):
        if mapping_type in self.mapping_types:
            mapping_objs = self.Core.DB.session.query(models.Mapping).all()
            mappings = {}
            for mapping_dict in self.DeriveMappingDicts(mapping_objs):
                if mapping_dict["mappings"].get(mapping_type, None):
                    mappings[mapping_dict["owtf_code"]] = mapping_dict["mappings"][mapping_type]
            return mappings
        else:
            raise InvalidMappingReference("InvalidMappingReference " + mapping_type + " requested")

    def GetCategory(self, plugin_code):
        category = self.Core.DB.session.query(models.Mapping.category).get(plugin_code)
        # Getting the corresponding category back from db
        return category
