import threading 
from datetime import datetime 
from hash_table import HashTable, Command, Response


hash_table_lock = threading.Lock()


class Message:

    DATA_SIZE = 1024

    def __init__(self, thread: int, client: str, address: str, hash_table: HashTable, 
                 timeout: int, stop_event: threading.Event):
        self.thread = thread
        self.client = client
        self.address = address
        self.hash_table = hash_table
        self._recv_buffer = ""  
        self.timeout = timeout 
        self.stop_event = stop_event

    def process_commands(self):
        last_message = datetime.now()
        while not self.stop_event.is_set(): 
            try:
                data = self.client.recv(Message.DATA_SIZE)
            except BlockingIOError:
                now = datetime.now()
                if now - last_message > self.timeout:
                    raise RuntimeError("Client timed out")
            else:
                if data:
                    self._recv_buffer += data.decode("utf-8")
                    self._process_recv_buffer()
                    last_message = datetime.now()
                    print("Processed data")
                else:
                    print("Didn't process data")
                    raise RuntimeError("Client disconnected before data was sent")
                
        print("Stop event triggered, closing thread")

    def _process_recv_buffer(self):
        command_buffered, multiline = self._check_complete_buffered()
        while command_buffered:
            header, value = self._strip_message(multiline)
            command, args, no_reply = self._parse_header(header)
            self._perform_cache_operation(command, args, no_reply, value)
            command_buffered, multiline = self._check_complete_buffered() # continue while buffer nonempty 

    def _check_complete_buffered(self):
        count = self._recv_buffer.count("\r\n")
        one_buffered = (self._recv_buffer.startswith(Command.GET.value) or 
                        self._recv_buffer.startswith(Command.DELETE.value)) and count >= 1
        
        two_buffered = any([self._recv_buffer.startswith(val) for val in [
            Command.REPLACE.value, Command.ADD.value, Command.SET.value]]
            ) and count >= 2
        return one_buffered or two_buffered, count >= 2

    def _strip_message(self, multiline):
        '''If command is single line, value is None. If multi-line, second line is value'''
        header = self._strip_buffer_for_message()
        value = None 
        if multiline:
            value = self._strip_buffer_for_message()
        return header, value
    
    def _strip_buffer_for_message(self):
        idx = self._recv_buffer.find("\r\n")
        line_item = self._recv_buffer[:idx]
        self._recv_buffer = self._recv_buffer[idx + 2:]
        return line_item
    
    def _parse_header(self, header):
        elements = header.split(" ")
        
        command = elements[0]
        if command in [Command.GET.value, Command.DELETE.value]:
            if len(elements) != 2:
                raise ValueError("Must pass 2 items for get or delete command")
            args = [elements[1]]
            no_reply = False

        elif command in [Command.SET.value, Command.ADD.value, Command.REPLACE.value]:
            if not (len(elements) == 5 or len(elements) == 6):
                raise ValueError("Must pass 5 or 6 items for setter command")
            if len(elements) == 5:
                args = elements[1:]
                no_reply = False
            elif len(elements) == 6:
                args = elements[1:-1]
                no_reply = True if elements[-1] == "noreply" else False 

            args = [int(arg) if idx != 0 else arg for idx, arg in enumerate(args)]
        
        else:
            raise ValueError(f"Command {command} not supported")
            
        return command, args, no_reply 
        

    def _perform_cache_operation(self, command, args, no_reply, value):
        with hash_table_lock:
            if command == Command.GET.value:
                key = args[0] 
                return_value = self.hash_table.get(key)
                if return_value:
                    value, flag, byte_count = return_value
                    return_str = f"{Response.VALUE.value} {value} {flag} {byte_count}"
                else:
                    return_str = Response.END.value

            elif command in [Command.SET.value, Command.ADD.value, Command.REPLACE.value]:
                key, flag, expiry, byte_count = args
                return_str = self.hash_table.insert(key, value, flag, byte_count, expiry, Command(command))

            elif command == Command.DELETE.value:
                key = args[0]
                return_str = self.hash_table.delete(key)

            else:
                raise ValueError(f"Command {command} is not supported")
        

        if not no_reply:
            self._send_response(return_str)

        return return_str

    def _send_response(self, return_str):
        return_str += "\r\n"
        self.client.send(return_str.encode("utf-8"))


    def close(self):
       self.client.close()
