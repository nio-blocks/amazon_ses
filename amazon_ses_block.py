from nio.common.block.base import Block
from nio.common.signal.base import Signal
from nio.common.discovery import Discoverable, DiscoverableType
from nio.metadata.properties.holder import PropertyHolder
from nio.metadata.properties.expression import ExpressionProperty
from nio.metadata.properties.object import ObjectProperty
from nio.metadata.properties.select import SelectProperty
from nio.metadata.properties.list import ListProperty
from nio.metadata.properties.string import StringProperty
from nio.common.command import command

import re
from boto.ses import connect_to_region
from enum import Enum

class Region(Enum):
    us_east_1 = 0
    us_west_2 = 1
    eu_west_1 = 2

    
class AWSCreds(PropertyHolder):
    access_key = StringProperty(title="Access Key")
    access_secret = StringProperty(title="Access Secret")


class Message(PropertyHolder):
    subject = ExpressionProperty(title="Subject", default="<No Value>")
    body = ExpressionProperty(title="Body", default="<No Value>")

    
@command("quota")
@command("stats")
@Discoverable(DiscoverableType.block)
class AmazonSESBlock(Block):

    """ A block that sends email using Amazon Simple Email Service

    """
    region = SelectProperty(Region, default=Region.us_east_1, title="AWS Region")
    creds = ObjectProperty(AWSCreds, title="AWS Credentials")
    sender = StringProperty(title="Sender Email")
    recipients = ListProperty(str, title="Recipient Emails")
    message = ObjectProperty(Message, title="Message")
    
    def __init__(self):
        super().__init__()
        self._conn = None

    def configure(self, context):
        super().configure(context)
        self._conn = connect_to_region(
            re.sub('_', '-', self.region.name),
            aws_access_key_id=self.creds.access_key,
            aws_secret_access_key=self.creds.access_secret
        )

    def process_signals(self, signals):
        for signal in signals:
            try:
                subject = self.message.subject(signal)
            except:
                subject = self.get_defaults()['message']['subject']
                self._logger.error(
                    "Email subject evaluation failed: {0}: {1}".format(
                        type(e).__name__, str(e))
                )

            try:
                body = self.message.body(signal)
            except Exception as e:
                body = self.get_defaults()['message']['body']
                self._logger.error(
                    "Email body evaluation failed: {0}: {1}".format(
                        type(e).__name__, str(e))
                )

            try:
                self._conn.send_email(
                    self.sender,
                    subject, body,
                    self.recipients
                )
            except Exception as e:
                self._logger.error(
                    "Error sending mail: {}:{}".format(
                        type(e).__name__, str(e))
                )

    def quota(self):
        response = self._conn.get_send_quota().get('GetSendQuotaResponse')
        result = response if not response else response.get('GetSendQuotaResult')
        return result

    def stats(self):
        response = self._conn.get_send_statistics().get('GetSendStatisticsResponse')
        result = response if not response else response.get('GetSendStatisticsResult')
        return result
