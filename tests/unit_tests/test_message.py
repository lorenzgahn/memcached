import pytest 
from unittest.mock import patch

from message import Message
from hash_table import HashTable


def test_message_str_processing():
    message = Message(None, None, None, None, None, None) 
    
    ### mssage comes in all at once 
    message._recv_buffer += "set test 0 0 4\r\n1234\r\nget test\r\n"

    buffered, multiline = message._check_complete_buffered()
    assert buffered and multiline

    header, value = message._strip_message(multiline)
    assert header == "set test 0 0 4" and value == "1234"

    buffered, multiline = message._check_complete_buffered()
    assert buffered and not multiline
    header, value = message._strip_message(multiline)
    assert header == "get test" and value is None

    buffered, multiline = message._check_complete_buffered()
    assert not buffered 

    ### message comes in incrementally 
    message._recv_buffer += "set test 0 0 4"
    buffered, multiline = message._check_complete_buffered()
    assert not buffered 
    
    message._recv_buffer += "\r\n"
    buffered, multiline = message._check_complete_buffered()
    assert not buffered 

    message._recv_buffer += "1234\r\n"
    buffered, multiline = message._check_complete_buffered()
    assert buffered


def test_parse_header():
    message = Message(None, None, None, None, None, None)

    header = "set test 0 0 4"
    command, args, no_reply = message._parse_header(header)
    assert command == "set" and args == ["test", 0, 0, 4] and not no_reply
    
    header = "set test 0 0 4 noreply"
    command, args, no_reply = message._parse_header(header)
    assert command == "set" and args == ["test", 0, 0, 4] and no_reply

    header = "get test"
    command, args, no_reply = message._parse_header(header)
    assert command == "get" and args == ["test"] and not no_reply


    ### too many or too few values passed 
    header = "get test noreply"
    with pytest.raises(ValueError):
        command, args, no_reply = message._parse_header(header)
   
    header = "set test 0 0"
    with pytest.raises(ValueError):
        command, args, no_reply = message._parse_header(header)



def test_perform_cache_operations():
    hash_table = HashTable(capacity=5)
    message = Message(None, None, None, hash_table, None, None)
    
    with patch.object(Message, '_send_response'):
        command, args, value = "set", ["test", 0, 0, 4], "1234"
        no_reply = False
        return_str = message._perform_cache_operation(command, args, no_reply, value)
        assert return_str == "STORED"

        command, args = "get", ["test"]
        return_str = message._perform_cache_operation(command, args, no_reply, value)
        assert return_str == "VALUE 1234 0 4"

        command, args = "do_another_thing", ["test"]
        with pytest.raises(ValueError):
            message._perform_cache_operation(command, args, no_reply, value)




