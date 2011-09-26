# from wsgiref.util import setup_testing_defaults
import sys
from string import Template
import urllib
from wsgiref.simple_server import make_server
from xml.etree import ElementTree as ET
from multiprocessing import Process
from otto import Application as BaseApplication
from webob import Response


ok_response = \
"""<?xml version="1.0" encoding="UTF-8" ?>
<redirecttransaction result="ok">
<transaction>
<id>4084044</id>
<payment_url>http://$host:$port/paylink</payment_url>
</transaction>
</redirecttransaction>
"""

error_response =\
"""<?xml version="1.0" encoding="UTF-8"?>
<redirecttransaction result="error">
<error>
<code>1013</code>
<description>MD5 mismatch</description>
</error>
<transaction>
<id>4084044</id>
</transaction>
</redirecttransaction>
"""

status_ok_response = \
"""<?xml version="1.0" encoding="UTF-8"?>
<status result="ok">
    <ewallet>
        <id>80675</id>
        <status>completed</status>
        <created>20100415132654</created>
        <modified/>
    </ewallet>
    <customer>
        <currency>EUR</currency>
        <amount>1000</amount>
        <exchange_rate>1</exchange_rate>
        <firstname>Jan</firstname>
        <lastname>Modaal</lastname>
        <city>Amsterdam</city>
        <state/>
        <country>NL</country>
        <countryname>Netherlands</countryname>
    </customer>
    <transaction>
        <id>4084044</id>
        <currency>EUR</currency>
        <amount>1000</amount>
        <description>Test transaction</description>
        <var1/>
        <var2/>
        <var3/>
        <items/>
    </transaction>
</status>"""

pay_response = \
"""<html>
    <body>
        $shop_return_link
        <a href="$cancel_url">cancel</a>
    </body>
</html>"""


class Application(BaseApplication):

    def __init__(self):
        super(Application, self).__init__()
        self.notify_url = ''
        self.transaction_id = 0
        self.cancel_url = ''
        self.host = 'localhost'
        self.port = 9000

app = Application()


class TestServer(object):

    def __init__(self, host='localhost', port=9000):
        self.host = host
        self.port = port

    def run(self):

        def run_server():
            app.host = self.host
            app.port = self.port
            httpd = make_server(self.host, self.port, app)
            print "Serving for '{0}' on port {1}...".format(
                self.host, self.port)
            httpd.serve_forever()

        self.process = Process(target=run_server)
        self.process.start()

    def stop(self):
        self.process.terminate()


@app.connect('/ok')
def ok_handler(request):
    tree = ET.fromstring(request.body)
    body = Template(ok_response).substitute(host=app.host,
        port=app.port)
    app.notify_url = tree.find('merchant/notification_url').text
    app.cancel_url = tree.find('merchant/cancel_url').text
    app.transaction_id = tree.find('transaction/id').text
    return Response(content_type='application/xml',
                    body=body)


@app.connect('/paylink')
def paylink_handler(request):
    return Response(content_type='text/html',
                    body='<a href="./pay">pay</a>')


@app.connect('/pay')
def pay_handler(request):
    # do a request to the notify_url
    # show the result in the template
    f = urllib.urlopen('{0}&transactionid={1}'.format(
        app.notify_url, app.transaction_id))
    #f = urllib.urlopen('http://nu.nl')
    shop_return_link = f.read()
    f.close()
    #shop_return_link =\
    #    '<a href="http://localhost:8000/shop/delivery/">return</a>'
    return Response(content_type='text/html',
                    body=Template(pay_response).substitute(
                        shop_return_link=shop_return_link,
                        cancel_url=app.cancel_url))


@app.connect('/error')
def error_handler(request):
    return Response(content_type='application/xml',
                    body=error_response)


@app.connect('/status_ok')
def status_ok_handler(request):
    return Response(content_type='application/xml',
                    body=status_ok_response)


@app.connect('/status_error')
def status_error_handler(request):
    return Response(content_type='application/xml',
                    body=error_response)


def main():
    args = sys.argv[1:]
    host = len(args) > 0 and args[0] or 'localhost'
    port = len(args) > 1 and int(args[1]) or 9000
    server = TestServer(host, port)
    server.run()


def app_factory(global_config, **local_config):
    """ creates an otto WSGI-compliant HTTP publisher. """
#    config = ConfigParser()
#    config.read(global_config['__file__'])
#    app.set_config(config)
    return app
