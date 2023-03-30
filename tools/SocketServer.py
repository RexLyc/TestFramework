from socketserver import BaseRequestHandler, TCPServer
import time

class EchoHandler(BaseRequestHandler):
    def handle(self):
        print('Got connection from', self.client_address)
        while True:
            self.request.send('hello world'.encode())
            msg=self.request.recv(1024).strip()
            print('recv: {}'.format(msg))
            time.sleep(0.5)

if __name__ == '__main__':
    serv = TCPServer(('', 5001), EchoHandler)
    serv.serve_forever()