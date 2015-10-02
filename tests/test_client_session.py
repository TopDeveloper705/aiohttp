# -*- coding: utf-8 -*-
"""Tests for aiohttp/client.py"""

import asyncio
import gc
import unittest
from unittest import mock

import aiohttp
from aiohttp.client import ClientSession
from aiohttp.multidict import MultiDict, CIMultiDict
from aiohttp.connector import BaseConnector, TCPConnector


class TestClientSession(unittest.TestCase):

    maxDiff = None

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)
        self.run = self.loop.run_until_complete

    def tearDown(self):
        self.loop.close()
        gc.collect()

    def make_open_connector(self):
        conn = BaseConnector(loop=self.loop)
        transp = unittest.mock.Mock()
        conn._conns['a'] = [(transp, 'proto', 123)]
        return conn

    def test_init_headers_simple_dict(self):
        session = ClientSession(
            headers={
                "h1": "header1",
                "h2": "header2"
            }, loop=self.loop)
        self.assertEqual(
            sorted(session._default_headers.items()),
            ([("H1", "header1"),
              ("H2", "header2")]))
        session.close()

    def test_init_headers_list_of_tuples(self):
        session = ClientSession(
            headers=[("h1", "header1"),
                     ("h2", "header2"),
                     ("h3", "header3")],
            loop=self.loop)
        self.assertEqual(
            session._default_headers,
            CIMultiDict([("h1", "header1"),
                         ("h2", "header2"),
                         ("h3", "header3")]))
        session.close()

    def test_init_headers_MultiDict(self):
        session = ClientSession(
            headers=MultiDict(
                [("h1", "header1"),
                 ("h2", "header2"),
                 ("h3", "header3")]),
            loop=self.loop)
        self.assertEqual(
            session._default_headers,
            CIMultiDict([("H1", "header1"),
                         ("H2", "header2"),
                         ("H3", "header3")]))
        session.close()

    def test_init_headers_list_of_tuples_with_duplicates(self):
        session = ClientSession(
            headers=[("h1", "header11"),
                     ("h2", "header21"),
                     ("h1", "header12")],
            loop=self.loop)
        self.assertEqual(
            session._default_headers,
            CIMultiDict([("H1", "header11"),
                         ("H2", "header21"),
                         ("H1", "header12")]))
        session.close()

    def test_init_cookies_with_simple_dict(self):
        session = ClientSession(
            cookies={
                "c1": "cookie1",
                "c2": "cookie2"
            }, loop=self.loop)
        self.assertEqual(set(session.cookies), {'c1', 'c2'})
        self.assertEqual(session.cookies['c1'].value, 'cookie1')
        self.assertEqual(session.cookies['c2'].value, 'cookie2')
        session.close()

    def test_init_cookies_with_list_of_tuples(self):
        session = ClientSession(
            cookies=[("c1", "cookie1"),
                     ("c2", "cookie2")],
            loop=self.loop)
        self.assertEqual(set(session.cookies), {'c1', 'c2'})
        self.assertEqual(session.cookies['c1'].value, 'cookie1')
        self.assertEqual(session.cookies['c2'].value, 'cookie2')
        session.close()

    def test_merge_headers(self):
        # Check incoming simple dict
        session = ClientSession(
            headers={
                "h1": "header1",
                "h2": "header2"
            }, loop=self.loop)
        headers = session._prepare_headers({
            "h1": "h1"
        })
        self.assertIsInstance(headers, CIMultiDict)
        self.assertEqual(headers, CIMultiDict([
            ("h2", "header2"),
            ("h1", "h1")
        ]))
        session.close()

    def test_merge_headers_with_multi_dict(self):
        session = ClientSession(
            headers={
                "h1": "header1",
                "h2": "header2"
            }, loop=self.loop)
        headers = session._prepare_headers(MultiDict([("h1", "h1")]))
        self.assertIsInstance(headers, CIMultiDict)
        self.assertEqual(headers, CIMultiDict([
            ("h2", "header2"),
            ("h1", "h1")
        ]))
        session.close()

    def test_merge_headers_with_list_of_tuples(self):
        session = ClientSession(
            headers={
                "h1": "header1",
                "h2": "header2"
            }, loop=self.loop)
        headers = session._prepare_headers([("h1", "h1")])
        self.assertIsInstance(headers, CIMultiDict)
        self.assertEqual(headers, CIMultiDict([
            ("h2", "header2"),
            ("h1", "h1")
        ]))
        session.close()

    def test_merge_headers_with_list_of_tuples_duplicated_names(self):
        session = ClientSession(
            headers={
                "h1": "header1",
                "h2": "header2"
            }, loop=self.loop)
        headers = session._prepare_headers([("h1", "v1"),
                                            ("h1", "v2")])
        self.assertIsInstance(headers, CIMultiDict)
        self.assertEqual(headers, CIMultiDict([
            ("H2", "header2"),
            ("H1", "v1"),
            ("H1", "v2"),
        ]))
        session.close()

    def _make_one(self, **kwargs):
        session = ClientSession(loop=self.loop, **kwargs)
        params = dict(
            headers={"Authorization": "Basic ..."},
            max_redirects=2,
            encoding="latin1",
            version=aiohttp.HttpVersion10,
            compress="deflate",
            chunked=True,
            expect100=True,
            read_until_eof=False)
        return session, params

    @mock.patch("aiohttp.client.ClientSession._request")
    def test_http_GET(self, patched):
        session, params = self._make_one()
        session.get(
            "http://test.example.com",
            params={"x": 1},
            **params)
        self.assertTrue(patched.called, "`ClientSession._request` not called")
        self.assertEqual(
            list(patched.call_args),
            [("GET", "http://test.example.com",),
             dict(
                 params={"x": 1},
                 allow_redirects=True,
                 **params)])
        session.close()

    @mock.patch("aiohttp.client.ClientSession._request")
    def test_http_OPTIONS(self, patched):
        session, params = self._make_one()
        session.options(
            "http://opt.example.com",
            params={"x": 2},
            **params)
        self.assertTrue(patched.called, "`ClientSession._request` not called")
        self.assertEqual(
            list(patched.call_args),
            [("OPTIONS", "http://opt.example.com",),
             dict(
                params={"x": 2},
                allow_redirects=True,
                **params)])
        session.close()

    @mock.patch("aiohttp.client.ClientSession._request")
    def test_http_HEAD(self, patched):
        session, params = self._make_one()
        session.head(
            "http://head.example.com",
            params={"x": 2},
            **params)
        self.assertTrue(patched.called, "`ClientSession._request` not called")
        self.assertEqual(
            list(patched.call_args),
            [("HEAD", "http://head.example.com",),
             dict(
                params={"x": 2},
                allow_redirects=False,
                **params)])
        session.close()

    @mock.patch("aiohttp.client.ClientSession._request")
    def test_http_POST(self, patched):
        session, params = self._make_one()
        session.post(
            "http://post.example.com",
            params={"x": 2},
            data="Some_data",
            **params)
        self.assertTrue(patched.called, "`ClientSession._request` not called")
        self.assertEqual(
            list(patched.call_args),
            [("POST", "http://post.example.com",),
             dict(
                params={"x": 2},
                data="Some_data",
                **params)])
        session.close()

    @mock.patch("aiohttp.client.ClientSession._request")
    def test_http_PUT(self, patched):
        session, params = self._make_one()
        session.put(
            "http://put.example.com",
            params={"x": 2},
            data="Some_data",
            **params)
        self.assertTrue(patched.called, "`ClientSession._request` not called")
        self.assertEqual(
            list(patched.call_args),
            [("PUT", "http://put.example.com",),
             dict(
                 params={"x": 2},
                 data="Some_data",
                 **params)])
        session.close()

    @mock.patch("aiohttp.client.ClientSession._request")
    def test_http_PATCH(self, patched):
        session, params = self._make_one()
        session.patch(
            "http://patch.example.com",
            params={"x": 2},
            data="Some_data",
            **params)
        self.assertTrue(patched.called, "`ClientSession._request` not called")
        self.assertEqual(
            list(patched.call_args),
            [("PATCH", "http://patch.example.com",),
             dict(
                params={"x": 2},
                data="Some_data",
                **params)])
        session.close()

    @mock.patch("aiohttp.client.ClientSession._request")
    def test_http_DELETE(self, patched):
        session, params = self._make_one()
        session.delete(
            "http://delete.example.com",
            params={"x": 2},
            **params)
        self.assertTrue(patched.called, "`ClientSession._request` not called")
        self.assertEqual(
            list(patched.call_args),
            [("DELETE", "http://delete.example.com",),
             dict(
                params={"x": 2},
                **params)])
        session.close()

    def test_close(self):
        conn = self.make_open_connector()
        session = ClientSession(loop=self.loop, connector=conn)

        session.close()
        self.assertIsNone(session.connector)
        self.assertTrue(conn.closed)

    def test_closed(self):
        session = ClientSession(loop=self.loop)
        self.assertFalse(session.closed)
        session.close()
        self.assertTrue(session.closed)

    def test_connector(self):
        connector = TCPConnector(loop=self.loop)
        session = ClientSession(connector=connector, loop=self.loop)
        self.assertIs(session.connector, connector)
        session.close()

    def test_connector_loop(self):
        loop = asyncio.new_event_loop()
        connector = TCPConnector(loop=loop)
        with self.assertRaisesRegex(
                ValueError,
                "loop argument must agree with connector"):
            ClientSession(connector=connector, loop=self.loop)
        connector.close()
        loop.close()

    def test_cookies_are_readonly(self):
        session = ClientSession(loop=self.loop)
        with self.assertRaises(AttributeError):
            session.cookies = 123
        session.close()

    def test_detach(self):
        session = ClientSession(loop=self.loop)
        conn = session.connector
        self.assertFalse(conn.closed)
        session.detach()
        self.assertIsNone(session.connector)
        self.assertTrue(session.closed)
        self.assertFalse(conn.closed)
        conn.close()

    def test_request_closed_session(self):
        @asyncio.coroutine
        def go():
            session = ClientSession(loop=self.loop)
            session.close()
            with self.assertRaises(RuntimeError):
                yield from session.request('get', '/')

        self.loop.run_until_complete(go())

    def test_close_flag_for_closed_connector(self):
        session = ClientSession(loop=self.loop)
        conn = session.connector
        self.assertFalse(session.closed)
        conn.close()
        self.assertTrue(session.closed)

    def test_double_close(self):
        conn = self.make_open_connector()
        session = ClientSession(loop=self.loop, connector=conn)

        session.close()
        self.assertIsNone(session.connector)
        session.close()
        self.assertTrue(session.closed)
        self.assertTrue(conn.closed)

    def test_del(self):
        conn = self.make_open_connector()
        session = ClientSession(loop=self.loop, connector=conn)
        self.loop.set_exception_handler(lambda loop, ctx: None)

        with self.assertWarns(ResourceWarning):
            del session
            gc.collect()

    def test_context_manager(self):
        conn = self.make_open_connector()
        with ClientSession(loop=self.loop, connector=conn) as session:
            pass

        self.assertTrue(session.closed)

    def test_borrow_connector_loop(self):
        conn = self.make_open_connector()
        session = ClientSession(connector=conn)
        self.assertIs(session._loop, self.loop)
        session.close()

    def test_reraise_os_error(self):
        @asyncio.coroutine
        def go():
            err = OSError(1, "permission error")
            req = mock.Mock()
            req_factory = mock.Mock(return_value=req)
            req.send = mock.Mock(side_effect=err)
            session = ClientSession(loop=self.loop, request_class=req_factory)

            @asyncio.coroutine
            def create_connection(req):
                # return self.transport, self.protocol
                return mock.Mock(), mock.Mock()
            session._connector._create_connection = create_connection

            with self.assertRaises(aiohttp.ClientOSError) as ctx:
                yield from session.request('get', 'http://example.com')
            e = ctx.exception
            self.assertEqual(e.errno, err.errno)
            self.assertEqual(e.strerror, err.strerror)

        self.loop.run_until_complete(go())
