import threading
import socket
import select

from geopy.compat import urlopen

try:
    # python 2
    import SimpleHTTPServer
    import SocketServer
except ImportError:
    import socketserver as SocketServer
    import http.server as SimpleHTTPServer


def pipe_sockets(sock1, sock2, timeout):
    """Pipe data from one socket to another and vice-versa."""
    sockets = [sock1, sock2]
    try:
        while True:
            rlist, _, xlist = select.select(sockets, [], sockets, timeout)
            if xlist:
                break
            for sock in rlist:
                data = sock.recv(8096)
                if not data:  # disconnected
                    break
                other = next(s for s in sockets if s is not sock)
                other.sendall(data)
    except IOError:
        pass
    finally:
        for sock in sockets:
            sock.close()


class ProxyServerThread(threading.Thread):
    spinup_timeout = 10

    def __init__(self, timeout=None):
        self.proxy_host = 'localhost'
        self.proxy_port = None  # randomly selected by OS
        self.timeout = timeout

        self.proxy_server = None
        self.socket_created_event = threading.Event()
        self.requests = []

        super(ProxyServerThread, self).__init__()
        self.daemon = True

    def get_proxy_url(self):
        if not self.socket_created_event.wait(self.spinup_timeout):
            raise AssertionError("Proxy Server didn't successfully start")
        return "http://%s:%s" % (self.proxy_host, self.proxy_port)

    def run(self):
        assert not self.proxy_server, ("This class is not reentrable. "
                                       "Please create a new instance.")

        requests = self.requests

        class Proxy(SimpleHTTPServer.SimpleHTTPRequestHandler):
            timeout = self.timeout

            def do_GET(self):
                requests.append(self.path)

                req = urlopen(self.path, timeout=self.timeout)
                self.send_response(req.getcode())
                self.send_header('Connection', 'close')
                self.end_headers()
                self.copyfile(req, self.wfile)
                self.connection.close()
                req.close()

            def do_CONNECT(self):
                requests.append(self.path)

                # Make a raw TCP connection to the target server
                host, port = self.path.split(':')
                try:
                    addr = host, int(port)
                    other_connection = \
                        socket.create_connection(addr, timeout=self.timeout)
                except socket.error:
                    self.send_error(502, 'Bad gateway')
                    return

                # Respond that a tunnel has been created
                self.send_response(200)
                self.send_header('Connection', 'close')
                self.end_headers()
                pipe_sockets(self.connection,  # it closes sockets
                             other_connection, self.timeout)

        # ThreadingTCPServer offloads connections to separate threads, so
        # the serve_forever loop doesn't block until connection is closed
        # (unlike TCPServer). This allows to shutdown the serve_forever loop
        # even if there's an open connection.
        self.proxy_server = SocketServer.ThreadingTCPServer(
            (self.proxy_host, 0),
            Proxy
        )

        # don't hang if there're some open connections
        self.proxy_server.daemon_threads = True

        self.proxy_port = self.proxy_server.server_address[1]
        self.socket_created_event.set()
        self.proxy_server.serve_forever()

    def stop(self):
        self.proxy_server.shutdown()  # stop serve_forever()
        self.proxy_server.server_close()
