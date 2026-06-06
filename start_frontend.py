import socketserver
import sys
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = 8000
DIRECTORY = r'C:\Users\qabct\Documents\Programming\FantasyFootball\Version2\ingest\frontend'

class QuietHandler(SimpleHTTPRequestHandler):
    # Suppress all log messages
    def log_message(self, format, *args):
        pass

    def end_headers(self):
        # Prevent connection close issues with Windows curl
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-Length', str(len(self.file)))
        self.send_header('Connection', 'keep-alive')
        self.end_headers()

    def do_GET(self):
        if self.path == '/index.html' or self.path == '/':
            filepath = os.path.join(DIRECTORY, 'index.html')
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    self.file = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.send_header('Content-Length', str(len(self.file)))
                self.send_header('Connection', 'keep-alive')
                self.end_headers()
                self.wfile.write(self.file)
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(('127.0.0.1', PORT), QuietHandler) as httpd:
        print(f'Frontend server running on http://localhost:{PORT}', flush=True)
        httpd.serve_forever()
