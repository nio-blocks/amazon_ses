from unittest.mock import patch
from nio.common.signal.base import Signal
from nio.util.support.block_test_case import NIOBlockTestCase
from ..deprecated_amazon_ses_block import AmazonSESBlock


@patch(AmazonSESBlock.__module__ + '.connect_to_region')
class TestDeprecatedAmazonSES(NIOBlockTestCase):

    def test_connect(self, connect_func):
        """ Test that we connect with the right credentials """
        blk = AmazonSESBlock()
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

    def test_send(self, connect_func):
        """ Test that we send to the right people """
        blk = AmazonSESBlock()
        self.configure_block(blk, {
            "recipients": ["recip@mail.com"],
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
        self.assertEqual(1, blk._conn.send_email.call_count)
        blk._conn.send_email.assert_called_once_with(
            source="sender@mail.com",
            subject="My Subject",
            body="My Body",
            to_addresses=["recip@mail.com"],
            html_body="My Body")

    def test_send_default_subject(self, connect_func):
        """ Test that we use the default subject if it's not found """
        blk = AmazonSESBlock()
        self.configure_block(blk, {
            "recipients": ["recip@mail.com"],
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
        self.assertEqual(1, blk._conn.send_email.call_count)
        blk._conn.send_email.assert_called_once_with(
            source="sender@mail.com",
            subject="No Subject",
            body="My Body",
            to_addresses=["recip@mail.com"],
            html_body="My Body")

    def test_send_default_body(self, connect_func):
        """ Test that we use the default body if it's not found """
        blk = AmazonSESBlock()
        self.configure_block(blk, {
            "recipients": ["recip@mail.com"],
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
        self.assertEqual(1, blk._conn.send_email.call_count)
        blk._conn.send_email.assert_called_once_with(
            source="sender@mail.com",
            subject="My Subject",
            body="",
            to_addresses=["recip@mail.com"],
            html_body="")

    def test_no_send_no_recip(self, connect_func):
        """ Test that we don't send if we have no recipients """
        blk = AmazonSESBlock()
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
        self.assertEqual(0, blk._conn.send_email.call_count)
