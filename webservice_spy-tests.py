import json
import StringIO
import unittest

from funct.spyobjects import WebServiceSpy

class MockRequest(object):
    pass

class MockResponse(object):
    def __init__(self):
        self.status = 200
        self.headers = {'Content-Type': 'text/html'}
        self.body = None

class MockCherrypy(object):
    def __init__(self):
        self.request = MockRequest()
        self.response = MockResponse()

class TestWebServiceSpy(unittest.TestCase):
    def setUp(self):
        self.mock_cherrypy = MockCherrypy()
        self.webspy = WebServiceSpy(self.mock_cherrypy, json)

    def __make_request(self, path='/', method='GET', headers={'Content-Type': 'application/json'}, body=''):
        self.mock_cherrypy.request.path_info = path
        self.mock_cherrypy.request.method = method
        self.mock_cherrypy.request.headers = headers
        self.mock_cherrypy.request.body = body
        self.webspy.default()

    def test_404_on_nonrequested_resource(self):
        """spyobjects.WebServiceSpy.default: should return 404 when getting non-requested resource"""
        self.__make_request('/requested/was/not/requested')
        self.assertEquals(404, self.mock_cherrypy.response.status, '404 not returned for unmade request')

class TestWebServiceSpyRequested(unittest.TestCase):
    def setUp(self):
        self.mock_cherrypy = MockCherrypy()
        self.webspy = WebServiceSpy(self.mock_cherrypy, json)

        self.__make_request('/request/1', 'PUT', body=json.dumps({'request 1': 'data'}))
        self.__make_request('/request/1', 'PUT', body=json.dumps({'request 1': 'again'}))
        self.__make_request('/request/2')
        self.__make_request('/request/3', 'POST', body=json.dumps({'request 3': 'data'}))

    def __make_request(self, path='/', method='GET', headers={'Content-Type': 'application/json'}, body=None):
        self.mock_cherrypy.request.path_info = path
        self.mock_cherrypy.request.method = method
        self.mock_cherrypy.request.headers = headers
        if body != None:
            body = StringIO.StringIO(body)
            body.seek(0)
        self.mock_cherrypy.request.body = body
        return self.webspy.default()

    def test_all_requests_stored(self):
        """spyobjects.WebServiceSpy.default: should be able to retrieve all previous requests"""
        expected = {
            '/request/1': [
                {
                    'headers': {'Content-Type': 'application/json'},
                    'method': 'PUT',
                    'body': json.dumps({'request 1': 'data'}),
                    },
                {
                    'headers': {'Content-Type': 'application/json'},
                    'method': 'PUT',
                    'body': json.dumps({'request 1': 'again'}),
                    },

                ],
            '/request/2': [
                {
                    'headers': {'Content-Type': 'application/json'},
                    'method': 'GET',
                    'body': None,
                    },
                ],
            '/request/3': [
                {
                    'headers': {'Content-Type': 'application/json'},
                    'method': 'POST',
                    'body': json.dumps({'request 3': 'data'}),
                    },
                ],
            }
        actual = self.__make_request('/requested/')
        self.assertEquals(expected, json.loads(actual))

    def test_retrieve_requests_to_specific_resource(self):
        """spyobjects.WebServiceSpy.default: able to retrieve requests to specific resource"""
        expected = [
            {
                'headers': {'Content-Type': 'application/json'},
                'method': 'PUT',
                'body': json.dumps({'request 1': 'data'}),
                },
            {
                'headers': {'Content-Type': 'application/json'},
                'method': 'PUT',
                'body': json.dumps({'request 1': 'again'}),
                },

            ]
        actual = self.__make_request('/requested/request/1')
        self.assertEquals(expected, json.loads(actual))

    def test_fetched_requests_returned_as_json(self):
        """spyobjects.WebServiceSpy.default: when GETting previous requests, returned as json"""
        self.__make_request('/requested/')
        self.assertEquals('application/json', self.mock_cherrypy.response.headers['Content-Type'])

