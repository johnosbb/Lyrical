from typing import Callable
import enchant
from enchant import DictWithPWL
from PyQt5.QtCore import QTemporaryFile


class SpellCheck:
    def __init__(
        self, personal_word_list: list[str], addToDictionary: Callable[[str], None]
    ):
        # Creating temporary file
        self.file = QTemporaryFile()
        self.file.open()
        self.dictionary = DictWithPWL(  # load the initial default dictionary
            "en_UK",
            self.file.fileName(),
        )  # DictWithPWL() is an inbuilt method of enchant module. It is used to combine a language dictionary and a custom dictionary also known as Personal Word List(PSL).

        self.addToDictionary = addToDictionary

        self.word_list = set(personal_word_list)
        self.load_words()  # we can load a customised dictionary

    def load_words(self):
        for word in self.word_list:
            self.dictionary.add(word)

    def suggestions(self, word: str) -> list[str]:
        return self.dictionary.suggest(word)

    def correction(self, word: str) -> str:
        return self.dictionary.suggest(word)[0]

    def add(self, new_word: str) -> bool:
        if self.check(new_word):
            return False
        self.word_list.add(new_word)
        self.addToDictionary(new_word)
        self.dictionary.add(new_word)
        return True

    def check(self, word: str) -> bool:
        return self.dictionary.check(word)

    # sets are unordered, has no duplicates and its items are unchangeable
    def getNewWords(self) -> set[str]:
        return self.word_list
