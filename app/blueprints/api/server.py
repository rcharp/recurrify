import time
import jwt
import cgi
import json
from sys import version as python_version
from cgi import parse_header, parse_multipart
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

secret_key = "abcd1234"

HOST_NAME = 'localhost'
PORT_NUMBER = 8080


class TestServerHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        """Respond to a GET request."""
        self.send_response(200)

        if self.path == "/":
            path = "index.html"
            self.send_header('Content-Type', 'text/html')
        elif self.path == "/embed.js":
            path = "embed.js"
        elif self.path == "/embedjs.css":
            path = "embedjs.css"
        elif self.path == "/favicon.ico":
            return ""

        self.end_headers()
        file = open(path, "r").read().encode('utf-8')
        self.wfile.write(file)

    def do_POST(self):
        self.send_response(200)
        post_data = self.parse_POST()
        if self.path == "/tokenize/":
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            encoded_jwt = jwt.encode(post_data, secret_key, algorithm='HS256')
            self.wfile.write(encoded_jwt)
        elif self.path == "/submit/":
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            decoded_jwt = jwt.decode(post_data['token'], secret_key, algorithm='HS256')
            self.wfile.write(json.dumps(decoded_jwt).encode('utf-8'))

    def parse_POST(self):
        ctype, pdict = parse_header(self.headers['content-type'])
        if ctype == 'multipart/form-data':
            postvars = parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers['content-length'])
            postvars = parse_qs(
                self.rfile.read(length),
                keep_blank_values=1)
        else:
            postvars = {}
        postvars = {k.decode('utf-8'): v[0].decode('utf-8') for k, v in postvars.items()}
        return postvars


if __name__ == '__main__':
    server_class = HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), TestServerHandler)
    print(time.asctime(), "Server Starts - {HOST_NAME}:{PORT_NUMBER}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print(time.asctime(), "Server Stops - {HOST_NAME}:{PORT_NUMBER}")
