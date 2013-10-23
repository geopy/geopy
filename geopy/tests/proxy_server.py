import SimpleHTTPServer
import SocketServer
import urllib

class Proxy(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.copyfile(urllib.urlopen(self.path), self.wfile)

class ProxyServer():
    '''Class used to invoke a simple test HTTP Proxy server'''
    def __init__(self):
        self.proxy_port = 1337
        self.proxy_host = 'localhost'

        self.proxyd = None

    def run_proxy(self):
        '''Starts Instance of Proxy in a TCPServer'''
        #Setup Proxy in thread
        self.proxyd = SocketServer.TCPServer((self.proxy_host, self.proxy_port), Proxy).serve_forever()
        # Start Proxy Process
        print "serving at port %s on PID %s " % (self.proxy_port, self.proxyd.pid)

    def get_proxy_url(self):
        return "http://%s:%s" % (self.proxy_host, self.proxy_port)


if __name__ == '__main__':
    import daemon

    daemon.daemonize()
    daemon.createPid()

    proxy = ProxyServer()
    proxy.run_proxy()



