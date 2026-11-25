"""A fixed-capacity separate-chaining hash table for string keys."""


class _Node:
    __slots__ = ("key", "value", "next")

    def __init__(self, key, value, next_node=None):
        self.key = key
        self.value = value
        self.next = next_node


class HashTable:
    """Store string keys in linked-list buckets using Horner's method."""

    def __init__(self, capacity=8):
        if isinstance(capacity, bool) or not isinstance(capacity, int):
            raise TypeError("capacity must be an integer")
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.buckets = [None] * capacity
        self._size = 0
        self.last_comparisons = 0

    def _validate_key(self, key):
        if not isinstance(key, str):
            raise TypeError("key must be a string")

    def hash_trace(self, key):
        """Return (character, previous value, new value) for each Horner step."""
        self._validate_key(key)
        value = 0
        trace = []
        for character in key:
            previous = value
            value = (31 * value + ord(character)) % self.capacity
            trace.append((character, previous, value))
        return trace

    def _index(self, key):
        trace = self.hash_trace(key)
        return trace[-1][2] if trace else 0

    def put(self, key, value):
        self._validate_key(key)
        index = self._index(key)
        node = self.buckets[index]
        if node is None:
            self.buckets[index] = _Node(key, value)
            self._size += 1
            return

        while node is not None:
            if node.key == key:
                node.value = value
                return
            if node.next is None:
                node.next = _Node(key, value)
                self._size += 1
                return
            node = node.next

    def get(self, key):
        self._validate_key(key)
        self.last_comparisons = 0
        node = self.buckets[self._index(key)]
        while node is not None:
            self.last_comparisons += 1
            if node.key == key:
                return node.value
            node = node.next
        raise KeyError(key)

    def delete(self, key):
        self._validate_key(key)
        self.last_comparisons = 0
        index = self._index(key)
        previous = None
        node = self.buckets[index]
        while node is not None:
            self.last_comparisons += 1
            if node.key == key:
                if previous is None:
                    self.buckets[index] = node.next
                else:
                    previous.next = node.next
                self._size -= 1
                return
            previous, node = node, node.next
        raise KeyError(key)

    def __contains__(self, key):
        try:
            self.get(key)
        except KeyError:
            return False
        return True

    def __len__(self):
        return self._size

    def items(self):
        for bucket in self.buckets:
            node = bucket
            while node is not None:
                yield node.key, node.value
                node = node.next
