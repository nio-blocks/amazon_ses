from unittest.mock import patch
from nio.common.signal.base import Signal
from nio.util.support.block_test_case import NIOBlockTestCase
from boto.ses.connection import SESConnection
from ..amazon_ses_block import AmazonSES


@patch("boto.ses.connection.SESConnection.send_email")
@patch(AmazonSES.__module__ + '.connect_to_region',
       return_value=SESConnection())
class TestAmazonSES(NIOBlockTestCase):

    def test_connect(self, connect_func, send_func):
        """ Test that we connect with the right credentials """
        blk = AmazonSES()
        self.configure_block(blk, {
            "region": "us_east_1",
            "creds": {
                "access_key": "SAMPLE KEY",
                "access_secret": "SAMPLE SECRET"
            }
        })
        connect_func.assert_called_once_with(
            'us-east-1',
            aws_access_key_id='SAMPLE KEY',
            aws_secret_access_key='SAMPLE SECRET')

    def test_send(self, connect_func, send_func):
        """ Test that we send to the right people """
        blk = AmazonSES()
        self.configure_block(blk, {
            "recipients": [{
                'recip': 'recip@mail.com'
            }],
            "sender": 'sender@mail.com',
            "message": {
                "subject": '{{ $sub }}',
                "body": '{{ $body }}'
            }
        })

        blk.process_signals([Signal({
            "sub": "My Subject",
            "body": "My Body"
        })])
        self.assertEqual(1, send_func.call_count)
        send_func.assert_called_once_with(
            source="sender@mail.com",
            subject="My Subject",
            body="My Body",
            to_addresses=["recip@mail.com"],
            html_body="My Body")

    def test_send_default_subject(self, connect_func, send_func):
        """ Test that we use the default subject if it's not found """
        blk = AmazonSES()
        self.configure_block(blk, {
            "recipients": [{
                'recip': 'recip@mail.com'
            }],
            "sender": 'sender@mail.com',
            "message": {
                "subject": '{{ $sub }}',
                "body": '{{ $body }}'
            }
        })

        blk.process_signals([Signal({
            "not_a_sub": "My Subject",
            "body": "My Body"
        })])
        self.assertEqual(1, send_func.call_count)
        send_func.assert_called_once_with(
            source="sender@mail.com",
            subject="No Subject",
            body="My Body",
            to_addresses=["recip@mail.com"],
            html_body="My Body")

    def test_send_default_body(self, connect_func, send_func):
        """ Test that we use the default body if it's not found """
        blk = AmazonSES()
        self.configure_block(blk, {
            "recipients": [{
                'recip': 'recip@mail.com'
            }],
            "sender": 'sender@mail.com',
            "message": {
                "subject": '{{ $sub }}',
                "body": '{{ $body }}'
            }
        })

        blk.process_signals([Signal({
            "sub": "My Subject",
            "not_a_body": "My Body"
        })])
        self.assertEqual(1, send_func.call_count)
        send_func.assert_called_once_with(
            source="sender@mail.com",
            subject="My Subject",
            body="",
            to_addresses=["recip@mail.com"],
            html_body="")

    def test_no_send_no_recip(self, connect_func, send_func):
        """ Test that we don't send if we have no recipients """
        blk = AmazonSES()
        self.configure_block(blk, {
            "recipients": [],
            "sender": 'sender@mail.com',
            "message": {
                "subject": '{{ $sub }}',
                "body": '{{ $body }}'
            }
        })

        blk.process_signals([Signal({
            "sub": "My Subject",
            "body": "My Body"
        })])
        self.assertEqual(0, send_func.call_count)

    def test_send_expr(self, connect_func, send_func):
        """ Test that we can send to a value in an expression """
        blk = AmazonSES()
        self.configure_block(blk, {
            "recipients": [{
                "recip": "{{ $recip }}"
            }],
            "sender": 'sender@mail.com',
            "message": {
                "subject": '{{ $sub }}',
                "body": '{{ $body }}'
            }
        })

        blk.process_signals([Signal({
            "sub": "My Subject",
            "body": "My Body",
            "recip": "recip@mail.com"
        })])
        self.assertEqual(1, send_func.call_count)
        send_func.assert_called_once_with(
            source="sender@mail.com",
            subject="My Subject",
            body="My Body",
            to_addresses=["recip@mail.com"],
            html_body="My Body")

    def test_send_expr_list(self, connect_func, send_func):
        """ Test that we can send to a list in an expression """
        blk = AmazonSES()
        self.configure_block(blk, {
            "recipients": [{
                "recip": "{{ $recip }}"
            }],
            "sender": 'sender@mail.com',
            "message": {
                "subject": '{{ $sub }}',
                "body": '{{ $body }}'
            }
        })

        blk.process_signals([Signal({
            "sub": "My Subject",
            "body": "My Body",
            "recip": ["recip1@mail.com", "recip2@mail.com"]
        })])
        self.assertEqual(1, send_func.call_count)
        send_func.assert_called_once_with(
            source="sender@mail.com",
            subject="My Subject",
            body="My Body",
            to_addresses=["recip1@mail.com", "recip2@mail.com"],
            html_body="My Body")

    def test_no_send_bad_recips(self, connect_func, send_func):
        """ Test that we don't send to any bad recipients """
        blk = AmazonSES()
        self.configure_block(blk, {
            "recipients": [{
                "recip": "{{ $recip1 }}"
            }, {
                "recip": "{{ $recip2 }}"
            }],
            "sender": 'sender@mail.com',
            "message": {
                "subject": '{{ $sub }}',
                "body": '{{ $body }}'
            }
        })

        blk.process_signals([Signal({
            "sub": "My Subject",
            "body": "My Body",
            "recip2": "recip2@mail.com"
        })])
        self.assertEqual(1, send_func.call_count)
        # We should still send, but only to the second recipient
        send_func.assert_called_once_with(
            source="sender@mail.com",
            subject="My Subject",
            body="My Body",
            to_addresses=["recip2@mail.com"],
            html_body="My Body")
