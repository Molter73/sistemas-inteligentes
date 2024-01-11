from abc import ABC, abstractmethod


class Node(ABC):
    @abstractmethod
    def eval(self, index):
        ...


class AndNode(Node):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def eval(self, index):
        return list(set(self.left.eval(index)) & set(self.right.eval(index)))

    def __str__(self):
        return f"({self.left} AND {self.right})"


class OrNode(Node):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def eval(self, index):
        return list(
            sorted(set(self.left.eval(index)) | set(self.right.eval(index)))
        )

    def __str__(self):
        return f"({self.left} OR {self.right})"


class NotNode(Node):
    def __init__(self, data):
        self.data = data

    def eval(self, index):
        all_docs: set = set(index.ids_all_docs)
        return list(all_docs - set(self.data.eval(index)))

    def __str__(self):
        return f"NOT ({self.data})"


class WordNode(Node):
    def __init__(self, data):
        self.data = data

    def eval(self, index):
        return index.postings[self.data]

    def __str__(self):
        return self.data
