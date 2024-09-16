import argparse 
from memcached.server import ThreadedServer, DEFAULT_HOST, DEFAULT_PORT


def get_port_and_host():
    parser = argparse.ArgumentParser(description='Start up memcached server')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT)
    parser.add_argument('--host', type=str, default=DEFAULT_HOST)
    parser.add_argument('--max_threads', type=int, default=4)
    args = parser.parse_args()
    return args.port, args.host, args.max_threads


def run_server():
    port, host, max_threads = get_port_and_host()
    with ThreadedServer(host, port, max_threads) as server:
        server.run()


if __name__ == "__main__":
    run_server()
