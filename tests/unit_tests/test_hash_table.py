
### HACK
import sys

sys.path.append("/Users/lorenzgahn/Repositories/Memcached")
##### 

import time
from hash_table import HashTable, Command, Response 



def test_insert_get_remove():
    table = HashTable(capacity=3)
    table.insert("dogs", 2, 0, 4, 0, Command.SET)
    table.insert("cats", 3, 1, 4, 0, Command.SET)
    assert table.capacity == 6

    table.insert("horses", 5, 2, 6, 0, Command.SET)
    table.insert("dogs", 1, 3, 4, 0, Command.SET)
    assert table.capacity == 12
    assert table.get("dogs") == (1, 3, 4)
    assert table.get("horses") == (5, 2, 6)

    table.delete("dogs")
    assert table.get("dogs") is None
    assert table.get_size() == 2
    assert table.get_capacity() == 12


def test_with_expiry():

    table = HashTable(capacity=6)
    table.insert("dogs", 2, 1, 4, -1, Command.SET)
    table.insert("cats", 2, 2, 4, 0, Command.SET)
    table.insert("fish", 2, 3, 4, 0.1, Command.SET)

    assert table.get("dogs") is None
    assert table.get("cats") == (2, 2, 4)
    assert table.get("fish") == (2, 3, 4)

    time.sleep(0.1)
    assert table.get("fish") is None


def test_set_add_replace():
    table = HashTable(capacity=6)
    
    # set behaves the same regardless of key's presence
    response1 = table.insert("dogs", 2, 0, 4, 0, Command.SET)
    response2 = table.insert("dogs", 3, 0, 4, 0, Command.SET)
    assert response1 == Response.STORED.value and response2 == Response.STORED.value
    
    # add should not store if key is present 
    response_add = table.insert("dogs", 3, 1, 4, 0, Command.ADD)
    assert table.get("dogs") == (3, 0, 4)
    assert response_add == Response.NOT_STORED.value

    # replace should store if key is present 
    response_replace = table.insert("dogs", 4, 1, 4, 0, Command.REPLACE)
    assert response_replace == Response.STORED.value
    assert table.get("dogs") == (4, 1, 4)

    # add should store if key is not present 
    response_add = table.insert("cat", 3, 1, 4, 0, Command.ADD)
    assert response_add == Response.STORED.value
    assert table.get("cat") == (3, 1, 4)
    
    # replace should not store if key is not present 
    response_add = table.insert("horse", 3, 1, 4, 0, Command.REPLACE)
    assert response_add == Response.NOT_STORED.value
    assert table.get("horse") is None 
   
    