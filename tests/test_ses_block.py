from unittest.mock import patch, MagicMock, ANY
from ..amazon_ses_block import AmazonSESBlock
from nio.util.support.block_test_case import NIOBlockTestCase
from nio.modules.threading import Event
from nio.common.signal.base import Signal


class SESTestBlock(AmazonSESBlock):

    def __init__(self, event):
        super().__init__()
        self._e = event

    def process_signals(self, signals):
        super().process_signals(signals)
        self._e.set()


class TestSignal(Signal):
    def __init__(self, data):
        super().__init__()
        self.data = data

class TestAmazonSES(NIOBlockTestCase):

    def setUp(self):
        super().setUp()
        self.config = {
            "recipients": ['joe@mail.com'],
            "sender": 'oren@mail.com',
            "message": {
                "subject": '{{$data}}',
                "body": '{{$data}}'
            }
        }

    @patch("boto.ses.connection.SESConnection.__init__", return_value=None)
    @patch("boto.ses.connection.SESConnection.send_email")
    def test_sendmail(self, mock_send, mock_connect):
        process_event = Event()
        signals = [TestSignal(3)]
        blk = SESTestBlock(process_event)
        self.configure_block(blk, self.config)
        blk.start()
        blk.process_signals(signals)
        process_event.wait(1)
        self.assertEqual(1, mock_send.call_count)
        mock_send.assert_called_once_with(
            source=self.config['sender'],
            subject=3,
            body=3,
            to_addresses=self.config['recipients'],
            html_body=3)
        blk.stop()
