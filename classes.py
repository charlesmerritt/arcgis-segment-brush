

class Dog:
    def __init__(self, name: str):
        self.name = name
        self.age = 0

    def bark(self):
        print("Woof!")

my_dog = Dog(name="Buddy")
my_dog.bark()