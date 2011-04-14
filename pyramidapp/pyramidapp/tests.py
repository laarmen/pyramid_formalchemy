import unittest
from pyramid.config import Configurator
from pyramid import testing

import os
from webtest import TestApp
from pyramidapp import main
from paste.deploy import loadapp

dirname = os.path.abspath(__file__)
dirname = os.path.dirname(dirname)
dirname = os.path.dirname(dirname)

class Test_1_UI(unittest.TestCase):

    config = os.path.join(dirname, 'test.ini')
    extra_environ = {}

    def setUp(self):
        app = loadapp('config:%s' % self.config)
        self.app = TestApp(app, extra_environ=self.extra_environ)
        self.config = Configurator(autocommit=True)
        self.config.begin()

    def tearDown(self):
        self.config.end()

    def test_index(self):
        resp = self.app.get('/')

    def test_crud(self):
        # index
        resp = self.app.get('/admin')
        self.assertEqual(resp.status_int, 302)
        assert '/admin/' in resp.location, resp

        resp = self.app.get('/admin/')
        resp.mustcontain('/admin/Foo')
        resp = resp.click('Foo')

        ## Simple model

        # add page
        resp.mustcontain('/admin/Foo/new')
        resp = resp.click('New Foo')
        resp.mustcontain('/admin/Foo"')
        form = resp.forms[0]
        form['Foo--bar'] = 'value'
        resp = form.submit()
        assert resp.headers['location'] == 'http://localhost/admin/Foo', resp

        # model index
        resp = resp.follow()
        resp.mustcontain('<td>value</td>')
        form = resp.forms[0]
        resp = form.submit()

        # edit page
        form = resp.forms[0]
        form['Foo-1-bar'] = 'new value'
        #form['_method'] = 'PUT'
        resp = form.submit()
        resp = resp.follow()

        # model index
        resp.mustcontain('<td>new value</td>')

        # delete
        resp = self.app.get('/admin/Foo')
        resp.mustcontain('<td>new value</td>')
        resp = resp.forms[1].submit()
        resp = resp.follow()

        assert 'new value' not in resp, resp

    def test_json(self):
        # index
        response = self.app.get('/admin/json')
        response.mustcontain('{"models": {', '"Foo": "http://localhost/admin/Foo/json"')

        ## Simple model

        # add page
        response = self.app.post('/admin/Foo/json',
                                    {'Foo--bar': 'value'})

        data = response.json
        id = data['item_url'].split('/')[-1]

        response.mustcontain('"Foo-%s-bar": "value"' % id)


        # get data
        response = self.app.get(str(data['item_url']))
        response.mustcontain('"Foo-%s-bar": "value"' % id)

        # edit page
        response = self.app.post(str(data['item_url']), {'Foo-%s-bar' % id: 'new value'})
        response.mustcontain('"Foo-%s-bar": "new value"' % id)

        # delete
        response = self.app.delete(str(data['item_url']))

class Test_2_Security(Test_1_UI):

    config = os.path.join(dirname, 'security.ini')
    extra_environ = {'REMOTE_USER': 'admin'}

    def test_model_security(self):
        resp = self.app.get('/admin/', extra_environ={'REMOTE_USER': 'editor'})
        self.assertEqual(resp.status_int, 200)

        resp = self.app.get('/admin/Foo', extra_environ={'REMOTE_USER': 'editor'})
        self.assertEqual(resp.status_int, 200)

        resp = self.app.get('/admin/Foo/new', status=403, extra_environ={'REMOTE_USER': 'editor'})
        self.assertEqual(resp.status_int, 403)

        resp = self.app.get('/admin/Bar', status=403, extra_environ={'REMOTE_USER': 'editor'})
        self.assertEqual(resp.status_int, 403)

        resp = self.app.get('/admin/Bar', extra_environ={'REMOTE_USER': 'bar_manager'})
        self.assertEqual(resp.status_int, 200)

class Test_3_JQuery(Test_1_UI):

    config = os.path.join(dirname, 'jquery.ini')

    def test_crud(self):
        # index
        resp = self.app.get('/admin/')
        resp.mustcontain('/admin/Foo')
        resp = resp.click('Foo')

        ## Simple model

        # add page
        resp.mustcontain('/admin/Foo/new')
        resp = resp.click('New Foo')
        resp.mustcontain('/admin/Foo"')
        form = resp.forms[0]
        form['Foo--bar'] = 'value'
        resp = form.submit()
        assert resp.headers['location'] == 'http://localhost/admin/Foo', resp

        # model index
        resp = resp.follow()

        # edit page
        resp = self.app.get('/admin/Foo/1/edit')
        form = resp.forms[0]
        form['Foo-1-bar'] = 'new value'
        #form['_method'] = 'PUT'
        resp = form.submit()
        resp = resp.follow()

        # model index
        resp.mustcontain('<td>new value</td>')

        # delete
        resp = self.app.get('/admin/Foo')
        resp.mustcontain('jQuery')

