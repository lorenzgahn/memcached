from enum import Enum 
from datetime import datetime, timedelta


class Command(Enum):
    SET = "set"
    REPLACE = "replace"
    ADD = "add"
    GET = "get"
    DELETE = "delete"


class Response(Enum):
    STORED = "STORED"
    VALUE = "VALUE"
    DELETED = "DELETED"
    END = "END"
    NOT_STORED = "NOT STORED"



class Node:

    def __init__(self, key, value, flag, byte_count, expiry, next=None):
        self.key = key
        self.value = value
        self.flag = flag
        self.byte_count = byte_count
        self.expiry = expiry
        self.next = next


class HashTable:

    '''Implements hash table with time-based expiry'''

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.size = 0
        self.table = [None] * capacity

    @staticmethod 
    def _get_expiry_time(time_to_expiry: int) -> tuple[bool, datetime.timestamp]:
        if time_to_expiry < 0:
            add_to_cache, expiry_time = False, None
        elif time_to_expiry == 0:
            add_to_cache, expiry_time = True, None
        else:
            add_to_cache = True
            expiry_time = datetime.now() + timedelta(seconds=time_to_expiry)
        return add_to_cache, expiry_time

    @staticmethod 
    def _is_expired(expiry_time: datetime.timestamp) -> bool:
        if expiry_time is None or expiry_time > datetime.now():
            return False 
        return True 

    def _hash_key(self, key) -> int:
        val = 0
        for k in str(key):
            val += ord(k)
        return val % self.capacity

    def update_node(self, node, value, flag, byte_count, expiry_time):
        node.value = value
        node.flag = flag
        node.byte_count = byte_count
        node.expiry_time = expiry_time

    def insert(self, key: int, value: int, flag: int, byte_count: int, time_to_expiry: int, method: Command):
        add_to_cache, expiry_time = HashTable._get_expiry_time(time_to_expiry)
        if not add_to_cache:
            return Response.NOT_STORED
        
        hash_key = self._hash_key(key)
        node = self.table[hash_key]
        if node is None:
            if method == Command.REPLACE:
                return Response.NOT_STORED.value
            else:
                self.table[hash_key] = Node(key, value, flag, byte_count, expiry_time)
                self.size += 1
                self.check_and_do_resize()
                return Response.STORED.value
             
        else:
            prev = None
            while node:
                if node.key == key:
                    if method == Command.ADD:
                        return Response.NOT_STORED.value
                    else:
                        self.update_node(node, value, flag, byte_count, expiry_time)
                        return Response.STORED.value
                prev, node = node, node.next

            if method == Command.REPLACE:
                return Response.NOT_STORED
            
            else:
                prev.next = Node(key, value, flag, byte_count, expiry_time)
                self.size += 1
                self.check_and_do_resize()
                return Response.STORED.value


    def get(self, key: int) -> int | str:
        index = self._hash_key(key)
        node = self.table[index]
        while node:
            if node.key == key:
                if not HashTable._is_expired(node.expiry):
                    return node.value, node.flag, node.byte_count
                else:
                    return None 
            node = node.next 

        return None
            
    def delete(self, key: int) -> bool:
        index = self._hash_key(key)
        node = self.table[index]
        prev = None 
        while node:
            if node.key == key:
                if prev:
                    prev.next = node.next
                else:
                    self.table[index] = node.next 

                self.size -= 1
                return Response.DELETED.value
            prev, node = node, node.next

        return Response.END.value
            

    def get_size(self) -> int:
        return self.size 

    def get_capacity(self) -> int:
        return self.capacity

    def check_and_do_resize(self) -> None:
        if self.size / self.capacity >= 0.5:
            self.resize()

    def resize(self) -> None:
        self.capacity = self.capacity * 2
        new_table = [None] * self.capacity 

        for node in self.table:
            while node:
                if HashTable._is_expired(node.expiry):
                    continue 
        
                index = self._hash_key(node.key)
                if new_table[index] is None:
                    new_table[index] = Node(node.key, node.value, node.flag, node.byte_count, node.expiry)

                else:
                    new_node = new_table[index]
                    while new_node.next:
                        new_node = new_node.next
                    new_node.next = Node(node.key, node.value, node.flag, node.byte_count, node.expiry)
                
                node = node.next

        self.table = new_table 
