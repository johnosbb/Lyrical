
from smells.smell import Smell

from smells.smellsCollections import SmellsCollection

from nltk.corpus import wordnet

collection = SmellsCollection()
count = 0
with open("literary_resources/words_to_describe_smell.txt", "r") as filestream:
    for line in filestream:
        currentline = line.split(":")
        sections = len(currentline)
        if(sections == 3):
            targetSmell = currentline[0].strip()
            rgbValue = currentline[1].strip()
            classification = currentline[2].strip()  # this is a list
            if(classification.isspace()):
                classification = ["Unknown Classification"]
            else:
                classification = classification.replace(
                    '\n', '', 1).split(',')

            tags = []
            newSmell = Smell(
                targetSmell, classification, tags)
            collection.add(newSmell)
            count = count + 1
        else:
            print(
                "Error: Not enough or too many fields: " + str(sections) + " to create a word entry for entry " + str(count))
            print(currentline)
            break

        if __name__ == '__main__':
            collection.save()
            collection.dump()
            print("Processed " + str(count) + " words")
