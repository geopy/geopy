import select
import socket
import threading

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


class Future(object):
    # concurrent.futures.Future docs say that they shouldn't be instantiated
    # directly, so this is a simple implementation which mimics the Future
    # which can safely be instantiated!

    def __init__(self):
        self._event = threading.Event()
        self._result = None
        self._exc = None

    def result(self, timeout=None):
        if not self._event.wait(timeout):
            raise AssertionError("Future timed out")
        if self._exc is not None:
            raise self._exc
        return self._result

    def set_result(self, result):
        self._result = result
        self._event.set()

    def set_exception(self, exception):
        self._exc = exception
        self._event.set()


class ProxyServerThread(threading.Thread):
    spinup_timeout = 10

    def __init__(self, timeout=None):
        self.proxy_host = 'localhost'
        self.proxy_port = None  # randomly selected by OS
        self.timeout = timeout

        self.proxy_server = None
        self.socket_created_future = Future()
        self.requests = []

        super(ProxyServerThread, self).__init__()
        self.daemon = True

    def get_proxy_url(self):
        assert self.socket_created_future.result(self.spinup_timeout)
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
        try:
            self.proxy_server = SocketServer.ThreadingTCPServer(
                (self.proxy_host, 0),
                Proxy
            )

            # don't hang if there're some open connections
            self.proxy_server.daemon_threads = True

            self.proxy_port = self.proxy_server.server_address[1]
        except Exception as e:
            self.socket_created_future.set_exception(e)
            raise
        else:
            self.socket_created_future.set_result(True)

        self.proxy_server.serve_forever()

    def stop(self):
        self.proxy_server.shutdown()  # stop serve_forever()
        self.proxy_server.server_close()


class HttpServerThread(threading.Thread):
    spinup_timeout = 10

    def __init__(self, timeout=None):
        self.server_host = 'localhost'
        self.server_port = None  # randomly selected by OS
        self.timeout = timeout

        self.http_server = None
        self.socket_created_future = Future()

        super(HttpServerThread, self).__init__()
        self.daemon = True

    def get_server_url(self):
        assert self.socket_created_future.result(self.spinup_timeout)
        return "http://%s:%s" % (self.server_host, self.server_port)

    def run(self):
        assert not self.http_server, ("This class is not reentrable. "
                                      "Please create a new instance.")

        class Server(SimpleHTTPServer.SimpleHTTPRequestHandler):
            timeout = self.timeout

            def do_GET(self):
                self.send_response(200)
                self.send_header('Connection', 'close')
                self.end_headers()
                self.wfile.write(b"Hello world")
                self.connection.close()

        # ThreadingTCPServer offloads connections to separate threads, so
        # the serve_forever loop doesn't block until connection is closed
        # (unlike TCPServer). This allows to shutdown the serve_forever loop
        # even if there's an open connection.
        try:
            self.http_server = SocketServer.ThreadingTCPServer(
                (self.server_host, 0),
                Server
            )

            # don't hang if there're some open connections
            self.http_server.daemon_threads = True

            self.server_port = self.http_server.server_address[1]
        except Exception as e:
            self.socket_created_future.set_exception(e)
            raise
        else:
            self.socket_created_future.set_result(True)

        self.http_server.serve_forever()

    def stop(self):
        self.http_server.shutdown()  # stop serve_forever()
        self.http_server.server_close()
