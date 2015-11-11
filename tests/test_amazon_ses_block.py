from unittest.mock import patch
from nio.common.signal.base import Signal
from nio.util.support.block_test_case import NIOBlockTestCase
from boto.ses.connection import SESConnection
from ..amazon_ses_block import AmazonSESBlock


@patch("boto.ses.connection.SESConnection.send_email")
@patch(AmazonSESBlock.__module__ + '.connect_to_region',
       return_value=SESConnection())
class TestAmazonSES(NIOBlockTestCase):

    def test_connect(self, connect_func, send_func):
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

    def test_send(self, connect_func, send_func):
        """ Test that we send to the right people """
        blk = AmazonSESBlock()
        self.configure_block(blk, {
            "recipients": ['recip@mail.com'],
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
