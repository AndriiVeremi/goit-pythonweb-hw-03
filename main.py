import mimetypes
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import urllib.parse
import time

from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)
DATA_FILE = STORAGE_DIR / "data.json"

jinja = Environment(loader=FileSystemLoader("templates"))


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case '/':
                self.send_html_file('index.html')
            case '/message':
                self.send_html_file('message.html')
            case '/read':
                self.render_template('read.jinja')
            case _:
                file = BASE_DIR.joinpath(route.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html_file('error.html', 404)

    def do_POST(self):
        size = self.headers.get("Content-Length")
        body = self.rfile.read(int(size)).decode('utf-8')
        parse_body = urllib.parse.unquote_plus(body)
        r = dict(item.split('=') for item in parse_body.split('&'))

        self.save_message(r.get("username", "Anonymous"), r.get("message", ""))

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def save_message(self, username, message):
        try:
            if DATA_FILE.exists():
                with open(DATA_FILE, "r", encoding="utf-8") as file:
                    try:
                        data = json.load(file)
                    except json.JSONDecodeError:
                        data = {}
            else:
                data = {}
        except FileNotFoundError:
            data = {}

        timestamp = str(int(time.time()))
        data[timestamp] = {"username": username, "message": message}

        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def render_template(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        template = jinja.get_template(filename)
        content = template.render(posts=data)
        self.wfile.write(content.encode())

    def send_static(self, filename, status=200):
        self.send_response(status)
        mime_type, *_ = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-type', mime_type)
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', 8000)
    http = server_class(server_address, handler_class)
    print('Starting server...')
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == '__main__':
    run()
