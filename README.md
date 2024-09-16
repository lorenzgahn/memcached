# Memcached Server Coding Challenge

This is an implementation of the Memcached server, as described by John Crickett in his Coding Challenges series (https://codingchallenges.fyi/challenges/challenge-memcached/). Memcached is a distributed in-memory key value store that allows for efficient caching and retrieval of data. A description of supported commands, syntax, etc. can be found on the coding challenge page description. 

## Installation 

From the root of the repository, the server can be run locally as follows. Each command line argument takes on default values, so the server can be run without arguments.  

python main.py --host {host} --port {port} --max_threads {max_threads}  


There are several unit and integration tests for the server, message processing, and data structure. To run, simply run pytest from the repo root. Additional configuration can be placed in pytest.ini file.   

The server as well as the tests can be run from within a container. The server image is built with Dockerfile.app, while the testing image is built with Dockerfile.test. The steps to run the container are as follows:  

docker build -t memcached -f Dockerfile.app .  
docker run -p 11211:11211 memcached

By default Memcached runs on the port 11211, but any value can be specified as a command line argument when running the server. Just be sure to expose a different port in the Dockerfile, and modify the port mapping in the above command. 


## Server usage
The server exposes sockets that a client connects to via TCP. The primary commands of the server are get, set, and delete, although there are others. To send commands to the server, you can use telnet (unencrypted), netcat (offers encryption), or, if running on a Linux machine, /dev/tcp/{host}/{port}. Once connected, the server will continue to listen for messages for 60 seconds (this can be configured in server.py) before disconnecting from the client. If a client is disconnected, the client can reconnect, and the server will start a new thread to process the client's commands. 


## Repo structure overview 

The main classes in this repository are as follows:   
ThreadedServer (server.py): the server class that manages client connections to the server. This implementation uses multithreading to allow several clients to connect to the server at once, while making use of a shared key-value store. For each client, creates a Message class to process commands.   

Message (message.py): Processes commands to a single client; parses messages, executes operations on the underlying HashTable class, and returns the appropriate response.   

HashTable (hash_table.py): The underlying data structure of the server used for key-value storage, which is modified support time-based expiration of keys.   


## Steps to deploy to AWS EC2 (note to self)
I deployed this server to an EC2 instance. The steps were as follows:
1. Instantiate EC2 instance - configure OS (Linux), choose server specs, etc. 
2. Modify security settings to allow any TCP connection on port 11211
3. SSH into instance using generated keys
4. Download Docker, log into Docker account, and set docker user permissions
5. Pull Docker image from Docker repository (image must be previously uploaded)
6. Build and run container following above commands
7. Can now connect to server with telnet and instance public IP 