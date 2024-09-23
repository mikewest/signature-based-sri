import http.server
import re

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        resource_file = "index.html"
        resource_type = "text/html"
        signature = ""
        if re.match('^/enforced', self.path):
            resource_file = "enforced.html"
        elif re.match('^/unenforced', self.path):
            resource_file = "unenforced.html"
        elif re.match('^/script-with-sig', self.path):
            resource_file = "script-with-sig.js"
            resource_type = "application/javascript"
            signature = "ed25519-65dtE6uTKVYBkwUNCrsf1TfbX4bTjpwUPw48/XgLgwXwKayfvOJop+vveiTfqCC1fZjENnGC4sPMIXj73kuIBQ=="
        elif re.match('^/script-without-sig', self.path):
            resource_file = "script-without-sig.js"
            resource_type = "application/javascript"

        self.send_response(200)
        self.send_header('Content-Type', resource_type)
        if signature != "":
            self.send_header("Integrity", signature)
        self.end_headers()

        self.wfile.write(open(resource_file, "r").read().encode("utf-8"))

if __name__ == "__main__":
    httpd = http.server.HTTPServer(('', 8000), RequestHandler)
    httpd.serve_forever()
