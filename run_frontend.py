import socketserver
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configure paths
FRONTEND_DIR = r'C:\Users\qabct\Documents\Programming\FantasyFootball\Version2\ingest\frontend'
BACKEND_WORK_DIR = r'C:\Users\qabct\Documents\Programming\FantasyFootball\Version2'
PORT = 8000

# Suppress all output from the frontend server
class QuietHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html' or self.path.endswith('.html'):
            filepath = os.path.join(FRONTEND_DIR, 'index.html')
        else:
            filepath = os.path.join(FRONTEND_DIR, self.path.lstrip('/'))
        
        if os.path.exists(filepath) and filepath.endswith('.html'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open(filepath, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    socketserver.TCPServer.allow_reuse_address = True
    print(f"Starting Frontend on http://localhost:{PORT}")
    HTTPServer(('127.0.0.1', PORT), QuietHandler).serve_forever()
