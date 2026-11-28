"""A fixed-capacity separate-chaining hash table for string keys."""


class _Node:
    __slots__ = ("key", "value", "next", "had_collision")

    def __init__(self, key, value, next_node=None, had_collision=False):
        self.key = key
        self.value = value
        self.next = next_node
        self.had_collision = had_collision


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
        self.last_slot_checks = 0
        self.last_probe_path = []

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
        self.last_comparisons = 0
        self.last_slot_checks = 1
        self.last_probe_path = [index]
        node = self.buckets[index]
        if node is None:
            self.buckets[index] = _Node(key, value)
            self._size += 1
            return

        while node is not None:
            self.last_comparisons += 1
            if node.key == key:
                node.value = value
                return
            if node.next is None:
                node.next = _Node(key, value, had_collision=True)
                self._size += 1
                return
            node = node.next

    def get(self, key):
        self._validate_key(key)
        self.last_comparisons = 0
        index = self._index(key)
        self.last_slot_checks = 1
        self.last_probe_path = [index]
        node = self.buckets[index]
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
        self.last_slot_checks = 1
        self.last_probe_path = [index]
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


_DELETED = object()


class LinearProbingHashTable:
    """Store string keys in a fixed-size array using linear probing."""

    def __init__(self, capacity=8):
        if isinstance(capacity, bool) or not isinstance(capacity, int):
            raise TypeError("capacity must be an integer")
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.slots = [None] * capacity
        self._size = 0
        self.last_comparisons = 0
        self.last_slot_checks = 0
        self.last_probe_path = []

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

    def _reset_lookup_metrics(self):
        self.last_comparisons = 0
        self.last_slot_checks = 0
        self.last_probe_path = []

    def put(self, key, value):
        self._validate_key(key)
        self._reset_lookup_metrics()
        start = self._index(key)
        first_deleted = None
        collision_slots = []

        for offset in range(self.capacity):
            index = (start + offset) % self.capacity
            self.last_probe_path.append(index)
            self.last_slot_checks += 1
            slot = self.slots[index]
            if slot is None:
                target = first_deleted if first_deleted is not None else index
                self.slots[target] = (
                    key,
                    value,
                    list(self.last_probe_path),
                    collision_slots,
                )
                self._size += 1
                return
            if slot is _DELETED:
                if first_deleted is None:
                    first_deleted = index
                continue
            self.last_comparisons += 1
            if slot[0] == key:
                self.slots[index] = (key, value, slot[2], slot[3])
                return
            collision_slots.append(index)

        if first_deleted is not None:
            self.slots[first_deleted] = (
                key,
                value,
                list(self.last_probe_path),
                collision_slots,
            )
            self._size += 1
            return
        raise OverflowError("hash table is full")

    def get(self, key):
        self._validate_key(key)
        self._reset_lookup_metrics()
        start = self._index(key)

        for offset in range(self.capacity):
            index = (start + offset) % self.capacity
            self.last_probe_path.append(index)
            self.last_slot_checks += 1
            slot = self.slots[index]
            if slot is None:
                break
            if slot is _DELETED:
                continue
            self.last_comparisons += 1
            if slot[0] == key:
                return slot[1]
        raise KeyError(key)

    def delete(self, key):
        self._validate_key(key)
        self._reset_lookup_metrics()
        start = self._index(key)

        for offset in range(self.capacity):
            index = (start + offset) % self.capacity
            self.last_probe_path.append(index)
            self.last_slot_checks += 1
            slot = self.slots[index]
            if slot is None:
                break
            if slot is _DELETED:
                continue
            self.last_comparisons += 1
            if slot[0] == key:
                self.slots[index] = _DELETED
                self._size -= 1
                return
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
        for slot in self.slots:
            if slot is not None and slot is not _DELETED:
                yield slot[0], slot[1]
