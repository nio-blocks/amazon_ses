from unittest.mock import patch
from nio.common.signal.base import Signal
from nio.util.support.block_test_case import NIOBlockTestCase
from ..amazon_ses_block import AmazonSES


@patch(AmazonSES.__module__ + '.connect_to_region')
class TestAmazonSES(NIOBlockTestCase):

    def test_connect(self, connect_func):
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

    def test_send(self, connect_func):
        """ Test that we send to the right people """
        blk = AmazonSES()
        self.configure_block(blk, {
            "to_recipients": [{
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
        self.assertEqual(1, blk._conn.send_email.call_count)
        blk._conn.send_email.assert_called_once_with(
            source="sender@mail.com",
            subject="My Subject",
            body="My Body",
            to_addresses=["recip@mail.com"],
            cc_addresses=[],
            bcc_addresses=[],
            html_body="My Body")

    def test_send_default_subject(self, connect_func):
        """ Test that we use the default subject if it's not found """
        blk = AmazonSES()
        self.configure_block(blk, {
            "to_recipients": [{
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
        self.assertEqual(1, blk._conn.send_email.call_count)
        blk._conn.send_email.assert_called_once_with(
            source="sender@mail.com",
            subject="No Subject",
            body="My Body",
            to_addresses=["recip@mail.com"],
            cc_addresses=[],
            bcc_addresses=[],
            html_body="My Body")

    def test_send_default_body(self, connect_func):
        """ Test that we use the default body if it's not found """
        blk = AmazonSES()
        self.configure_block(blk, {
            "to_recipients": [{
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
        self.assertEqual(1, blk._conn.send_email.call_count)
        blk._conn.send_email.assert_called_once_with(
            source="sender@mail.com",
            subject="My Subject",
            body="",
            to_addresses=["recip@mail.com"],
            cc_addresses=[],
            bcc_addresses=[],
            html_body="")

    def test_no_send_no_recip(self, connect_func):
        """ Test that we don't send if we have no recipients """
        blk = AmazonSES()
        self.configure_block(blk, {
            "to_recipients": [],
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

    def test_send_expr(self, connect_func):
        """ Test that we can send to a value in an expression """
        blk = AmazonSES()
        self.configure_block(blk, {
            "to_recipients": [{
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
        self.assertEqual(1, blk._conn.send_email.call_count)
        blk._conn.send_email.assert_called_once_with(
            source="sender@mail.com",
            subject="My Subject",
            body="My Body",
            to_addresses=["recip@mail.com"],
            cc_addresses=[],
            bcc_addresses=[],
            html_body="My Body")

    def test_send_expr_list(self, connect_func):
        """ Test that we can send to a list in an expression """
        blk = AmazonSES()
        self.configure_block(blk, {
            "to_recipients": [{
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
        self.assertEqual(1, blk._conn.send_email.call_count)
        blk._conn.send_email.assert_called_once_with(
            source="sender@mail.com",
            subject="My Subject",
            body="My Body",
            to_addresses=["recip1@mail.com", "recip2@mail.com"],
            cc_addresses=[],
            bcc_addresses=[],
            html_body="My Body")

    def test_no_send_bad_recips(self, connect_func):
        """ Test that we don't send to any bad recipients """
        blk = AmazonSES()
        self.configure_block(blk, {
            "to_recipients": [{
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
        self.assertEqual(1, blk._conn.send_email.call_count)
        # We should still send, but only to the second recipient
        blk._conn.send_email.assert_called_once_with(
            source="sender@mail.com",
            subject="My Subject",
            body="My Body",
            to_addresses=["recip2@mail.com"],
            cc_addresses=[],
            bcc_addresses=[],
            html_body="My Body")

    def test_send_cc_only(self, connect_func):
        """ Test that we can send only CC emails """
        blk = AmazonSES()
        self.configure_block(blk, {
            "cc_recipients": [{
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
        self.assertEqual(1, blk._conn.send_email.call_count)
        blk._conn.send_email.assert_called_once_with(
            source="sender@mail.com",
            subject="My Subject",
            body="My Body",
            to_addresses=[],
            cc_addresses=["recip@mail.com"],
            bcc_addresses=[],
            html_body="My Body")

    def test_send_bcc_only(self, connect_func):
        """ Test that we can send only CC emails """
        blk = AmazonSES()
        self.configure_block(blk, {
            "bcc_recipients": [{
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
        self.assertEqual(1, blk._conn.send_email.call_count)
        blk._conn.send_email.assert_called_once_with(
            source="sender@mail.com",
            subject="My Subject",
            body="My Body",
            to_addresses=[],
            cc_addresses=[],
            bcc_addresses=["recip@mail.com"],
            html_body="My Body")

    def test_all_three(self, connect_func):
        """ Test that we can send to, cc, and bcc emails """
        blk = AmazonSES()
        self.configure_block(blk, {
            "to_recipients": [{
                'recip': 'to.recip@mail.com'
            }],
            "cc_recipients": [{
                'recip': 'cc.recip@mail.com'
            }],
            "bcc_recipients": [{
                'recip': 'bcc.recip@mail.com'
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
        self.assertEqual(1, blk._conn.send_email.call_count)
        blk._conn.send_email.assert_called_once_with(
            source="sender@mail.com",
            subject="My Subject",
            body="My Body",
            to_addresses=["to.recip@mail.com"],
            cc_addresses=["cc.recip@mail.com"],
            bcc_addresses=["bcc.recip@mail.com"],
            html_body="My Body")
