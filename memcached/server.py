import socket 
import threading 

from memcached.message import Message 
from memcached.hash_table import HashTable

DEFAULT_TIMEOUT = 60
DEFAULT_CACHE_CAPACITY = 100
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 11211

class ThreadedServer:

    BACKLOG_SIZE = 5
    DEFAULT_TIMEOUT = 60
    DEFAULT_CACHE_CAPACITY = 100

    def __init__(self, host, port, max_threads, hash_capacity=DEFAULT_CACHE_CAPACITY, 
                 client_timeout=DEFAULT_TIMEOUT):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.stop_event = threading.Event()
        self.client_timeout = client_timeout

        self.thread_manager = ThreadManager(max_threads)
        self.hash_table = HashTable(hash_capacity)


    def __enter__(self):
        return self 

    def __exit__(self, exc_type, exc_value, traceback):
        #TODO: are there exceptions to handle? what are these inputs?
        for thread in self.thread_manager.threads:
           thread.join()

        self.sock.close()

    def run(self):
        self.sock.listen(ThreadedServer.BACKLOG_SIZE)
        while not self.stop_event.is_set():
            client, address = self.sock.accept()
            client.settimeout(self.client_timeout) 
            thread = threading.Thread(target=self.listen_to_client, args=(client, address))
            thread.start()

    def stop(self):
        self.stop_event.set()
        self.__exit__(None, None, None)

    def listen_to_client(self, client, address):
        thread_id = threading.get_ident()
        current_thread = threading.current_thread()
        message = Message(thread_id, client, address, self.hash_table, 
                          self.client_timeout, self.stop_event)

        try:
            if self.thread_manager.add_thread(current_thread):
                print(f"Successfully connected thread {thread_id}")
                message.process_commands()
            else:
                raise RuntimeError("Maximum number of threads are currently connected")
        except RuntimeError:
            print(f"Thread {thread_id} disconnected")
        
        finally:
            client.close()
            removed = self.thread_manager.remove_thread(current_thread)
            if removed:
                print(f"Successfully stopped thread {thread_id}")
            else:
                print(f"Failed to remove {thread_id} from ThreadManager")


class ThreadManager:

    def __init__(self, max_threads):
        self.max_threads = max_threads
        self.active_thread_count = 0
        self.lock = threading.Lock()
        self.threads = []

    def add_thread(self, thread):
        with self.lock:
            if self.active_thread_count < self.max_threads:
                self.active_thread_count += 1
                self.threads.append(thread)
                return True
            else:
                return False 

    def remove_thread(self, thread):
        with self.lock:
            if thread in self.threads: 
                self.active_thread_count -= 1
                self.threads.remove(thread)
                return True 
            else:
                return False 

