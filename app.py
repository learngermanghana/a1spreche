
import os
import tornado.ioloop
import tornado.web

BASE = os.path.dirname(__file__)
PUBLIC = os.path.join(BASE, "public")

class AssetLinks(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Content-Type", "application/json")
        self.set_header("Cache-Control", "public, max-age=300")
        path = os.path.join(PUBLIC, ".well-known", "assetlinks.json")
        with open(path, "rb") as f:
            self.write(f.read())

class WebManifest(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Content-Type", "application/manifest+json")
        self.set_header("Cache-Control", "public, max-age=300")
        path = os.path.join(PUBLIC, "manifest.webmanifest")
        with open(path, "rb") as f:
            self.write(f.read())

class Health(tornado.web.RequestHandler):
    def get(self):
        self.write({"ok": True})

def make_app():
    return tornado.web.Application([
        (r"/health", Health),
        (r"/\.well-known/assetlinks\.json", AssetLinks),
        (r"/manifest\.webmanifest", WebManifest),
        (r"/(.*)", tornado.web.StaticFileHandler, {
            "path": PUBLIC,
            "default_filename": "index.html"
        }),
    ], debug=False)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app = make_app()
    app.listen(port)
    print(f"Listening on :{port}")
    tornado.ioloop.IOLoop.current().start()
