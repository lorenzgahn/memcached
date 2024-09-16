import sys
import socket
from threading import Thread
import subprocess
import time
import pytest 
import os 
from contextlib import contextmanager

from memcached.server import DEFAULT_HOST, DEFAULT_PORT


@pytest.fixture(scope="session")
def server_process():
    current_dir = os.path.dirname(__file__)
    src_path = os.path.join(current_dir, '..', '..')
    server_script = os.path.join(src_path, "main.py")
    process = subprocess.Popen(
        ["python", server_script, f"--port={DEFAULT_PORT}", f"--host={DEFAULT_HOST}"])
    time.sleep(0.2)

    yield server_process

    process.terminate()
    process.wait()


@contextmanager 
def connect_socket(host, port):
    s = socket.socket()
    s.settimeout(60)
    s.connect((host, port))    
    yield s 
    s.close()


def run_thread_test(messages, expected_responses, errors, host=DEFAULT_HOST, port=DEFAULT_PORT):
    with connect_socket(host, port) as s:
        for message, expected_response in zip(messages, expected_responses):
            s.sendall(message.encode("utf-8"))
            response = s.recv(1024)
            try:
                assert response.decode("utf-8") == expected_response
            except AssertionError as e:
                errors.append(e)


def test_connect_single_client(server_process):

    with connect_socket(DEFAULT_HOST, DEFAULT_PORT) as s:
        
        message = "set test 0 0 4\r\n1234\r\n"
        s.sendall(message.encode("utf-8"))
        response = s.recv(1024)
        assert response.decode("utf-8") == "STORED\r\n"

        message = "get test\r\n"
        s.sendall(message.encode("utf-8"))
        response = s.recv(1024)
        assert response.decode("utf-8") == "VALUE 1234 0 4\r\n"

        message = "delete test\r\n"
        s.sendall(message.encode("utf-8"))
        response = s.recv(1024)
        assert response.decode("utf-8") == "DELETED\r\n"

        message = "delete test\r\n"
        s.sendall(message.encode("utf-8"))
        response = s.recv(1024)
        assert response.decode("utf-8") == "END\r\n"


def test_connect_single_client_with_expiry(server_process):

    with connect_socket(DEFAULT_HOST, DEFAULT_PORT) as s:

        message = "set diff 0 1 4\r\n1234\r\n"
        s.sendall(message.encode("utf-8"))
        response = s.recv(1024)
        assert response.decode("utf-8") == "STORED\r\n"

        # value expires after 1 second, should return different things 
        expected_responses = ["VALUE 1234 0 4\r\n", "END\r\n"]
        for ind, expected in enumerate(expected_responses):
            message = "get diff\r\n"
            s.sendall(message.encode("utf-8"))
            response = s.recv(1024)
            assert response.decode("utf-8") == expected

            if ind == 0:
                time.sleep(1)


        
def test_connect_multiple_client(server_process):
    errors = []

    messages1 = ["set test 0 0 4\r\n1234\r\n", "get test\r\n"]
    expected_responses1 = ["STORED\r\n", "VALUE 1234 0 4\r\n"]
    thread1 = Thread(target=run_thread_test, args=(messages1, expected_responses1, errors))
    
    messages2 = ["set another 0 0 4\r\n1234\r\n", "get another\r\n"]
    expected_responses2 = ["STORED\r\n", "VALUE 1234 0 4\r\n"]
    thread2 = Thread(target=run_thread_test, args=(messages2, expected_responses2, errors))
    
    threads = [thread1, thread2]

    for t in threads:
        t.start()
        
    for t in threads:
        t.join()
        
    # check that different threads can access the same values in the cache 
    messages3 = ["get test\r\n"]
    expected_responses3 = ["VALUE 1234 0 4\r\n"]
    thread3 = Thread(target=run_thread_test, args=(messages3, expected_responses3, errors))

    thread3.start()
    thread3.join()

    assert len(errors) == 0


def test_connect_multiple_clients_complex(server_process):
    errors = []

    messages1 = ["set test 0 0 4\r\n1234\r\n", "get test\r\n"]
    expected_responses1 = ["STORED\r\n", "VALUE 1234 0 4\r\n"]
    thread1 = Thread(target=run_thread_test, args=(
        messages1, expected_responses1, errors))

    messages2 = ["set another 0 0 4\r\n1234\r\n", "get another\r\n"]
    expected_responses2 = ["STORED\r\n", "VALUE 1234 0 4\r\n"]
    thread2 = Thread(target=run_thread_test, args=(
        messages2, expected_responses2, errors))

    threads = [thread1, thread2]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # check that different threads can access the same values in the cache
    messages3 = ["get test\r\n", "replace test 0 0 4\r\n5678\r\n"]
    expected_responses3 = ["VALUE 1234 0 4\r\n", "STORED\r\n"]
    thread3 = Thread(target=run_thread_test, args=(
        messages3, expected_responses3, errors))
    
    messages4 = ["delete another\r\n", "add test 0 0 4\r\n5678\r\n", 
                 "replace test 0 0 4\r\n9000\r\n"]
    expected_responses4 = ["DELETED\r\n", "NOT STORED\r\n", "STORED\r\n"]
    

    thread4 = Thread(target=run_thread_test, args=(
        messages4, expected_responses4, errors))

    threads = [thread3, thread4]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    assert len(errors) == 0


def test_connect_many_dummy_clients(server_process):
    errors = []

    threads = {}
    for i in range(20):
        threads[i] = Thread(target=run_thread_test, args=([], [], errors))

    for i, t in threads.items():
        t.start()

    for i, t in threads.items():
        t.join()

    






