import json
import jsonpickle
from colourDescriptors.colourDescriptor import ColourDescriptor

COLOUR_DESCRIPTORS = "literary_resources/descriptors.json"


class DescriptorsCollection():
    def __init__(self):
        self.__descriptorList = []

    @property
    def descriptorList(self):
        return self.__descriptorList

    @descriptorList.setter
    def descriptorList(self, descriptors):
        self.__descriptorList = descriptors

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

    def add(self, word: ColourDescriptor):
        self.descriptorList.append(word)

    def save(self):
        # saves the descriptors to a file
        self.descriptorList.sort(key=lambda x: x.descriptor, reverse=False)
        with open(COLOUR_DESCRIPTORS, "w") as outfile:
            jsonObj = jsonpickle.encode(self.descriptorList, keys=True)
            outfile.write(jsonObj)

    def load(self):
        # loads the descriptors from a file
        # Opening JSON file
        with open(COLOUR_DESCRIPTORS, 'r') as infile:
            descriptors = infile.read()
            self.descriptorList = jsonpickle.decode(descriptors, keys=True)
        return len(self.descriptorList)

    def filter_by_tag(self):
        # only return descriptors that conform to the filter
        print("---")

    def dump(self):
        with open('Descriptor_dump.txt', 'w') as file:
            for aDescriptor in self.__descriptorList:
                file.write(aDescriptor.descriptor + " : " +
                           aDescriptor.description + " : ")
                file.write(','.join(aDescriptor.classification))
                file.write(" : ")
                file.write(','.join(aDescriptor.tags))
                file.write("\n")
