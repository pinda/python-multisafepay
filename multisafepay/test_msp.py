from time import sleep
import pytest
from multisafepay.transaction import Transaction, MSPError, get_status
from testhttpserver import TestServer


def pytest_funcarg__wsgiserver(request):
    # Module level startup of wsgi server
    # so it is started only once for all test runs

    def setup_wsgisrvr():
        srv = TestServer()
        srv.run()
        # give some time to start server
        sleep(1)
        print 'wsgi started'
        return srv

    def teardown_wsgisrv(srv):
        srv.stop()

    request.cached_setup(
        setup=setup_wsgisrvr,
        teardown=teardown_wsgisrv,
        scope='module')


def test_msp_ok(wsgiserver):
    transaction = Transaction(account='a', site_id='b', site_secure_code='c',
        notification_url='http://localhost/notify', cancel_url='',
        locale='nl_NL', ipaddress='1.2.3.4', email='test@example.com',
        transaction_id='1234', amount='2300', description='party',
        api_url='http://localhost:9000/ok')
    res = transaction.start()
    assert res == 'http://localhost:9000/paylink'


def test_msp_error(wsgiserver):
    transaction = Transaction(account='a', site_id='b', site_secure_code='c',
        notification_url='http://localhost/notify', cancel_url='',
        locale='nl_NL', ipaddress='1.2.3.4', email='test@example.com',
        transaction_id='1234', amount='2300', description='party',
        api_url='http://localhost:9000/error')
    pytest.raises(MSPError, transaction.start)


def test_status(wsgiserver):
    status = get_status(account='a', site_id='b', site_secure_code='c',
            transaction_id='1234', api_url='http://localhost:9000/status_ok')
    assert status == 'completed'


def test_status_error(wsgiserver):
    pytest.raises(MSPError, get_status, account='a', site_id='b',
        site_secure_code='c',
        transaction_id='1234',
        api_url='http://localhost:9000/status_error')
