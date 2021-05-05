from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.wsgi import WSGIResource

from pepys_timeline.app import create_app

app = create_app()

resource = WSGIResource(reactor, reactor.getThreadPool(), app)
site = Site(resource)
reactor.listenTCP(5000, site)
reactor.run()
