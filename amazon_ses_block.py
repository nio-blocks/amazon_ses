from nio.common.block.base import Block
from nio.common.discovery import Discoverable, DiscoverableType
from nio.metadata.properties.holder import PropertyHolder
from nio.metadata.properties.expression import ExpressionProperty
from nio.metadata.properties.object import ObjectProperty
from nio.metadata.properties.select import SelectProperty
from nio.metadata.properties.list import ListProperty
from nio.metadata.properties.string import StringProperty
from nio.metadata.properties.version import VersionProperty
from nio.common.command import command

import re
from boto.ses import connect_to_region
from enum import Enum


class Region(Enum):
    us_east_1 = 0
    us_west_2 = 1
    eu_west_1 = 2


class AWSCreds(PropertyHolder):
    access_key = StringProperty(title="Access Key",
                                default="[[AMAZON_ACCESS_KEY_ID]]")
    access_secret = StringProperty(title="Access Secret",
                                   default="[[AMAZON_SECRET_ACCESS_KEY]]")


class Recipient(PropertyHolder):
    recip = ExpressionProperty(
        title="Recipient", default="info@n.io", attr_default=AttributeError)


class Message(PropertyHolder):
    subject = ExpressionProperty(
        title="Subject", default="<No Value>", attr_default="No Subject")
    body = ExpressionProperty(
        title="Body", default="<No Value>", attr_default="")


@command("quota")
@command("stats")
@Discoverable(DiscoverableType.block)
class AmazonSES(Block):

    """ A block that sends email using Amazon Simple Email Service

    Properties:
        region (enum): AWS region for SES (us_east_1, us_west_2, or eu_west_1)
        creds (AWSCreds): Access Key and Secret for AWS
        sender (str): Email address of the sender. Must be verified with SES.
        recipients (list): List of email addresses for recipients.
        message (obj): evaluated for each incoming signal
            subject (expression): The subject line of the email.
            body (expression): The body of the email

    """
    version = VersionProperty("0.2.0")
    region = SelectProperty(
        Region, default=Region.us_east_1, title="AWS Region")
    creds = ObjectProperty(AWSCreds, title="AWS Credentials")
    sender = StringProperty(title="Sender Email")
    recipients = ListProperty(Recipient, title="Recipient Emails")
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
                body = self.message.body(signal)
            except:
                self._logger.exception("Could not compute subject/body")
                continue

            recipients = self._get_recipients(signal)
            if len(recipients) == 0:
                # Don't send if we have no recipients
                continue

            try:
                self._conn.send_email(
                    source=self.sender,
                    subject=subject,
                    body=body,
                    html_body=body,
                    to_addresses=recipients
                )
            except:
                self._logger.exception("Error sending mail")

    def _get_recipients(self, signal):
        """ Return a list of destination recipients based on a signal """
        recipients = []
        for configured_recip in self.recipients:
            try:
                recip_result = configured_recip.recip(signal)
                if isinstance(recip_result, list):
                    # Allow the expression to evaluate to a list of recipients
                    recipients.extend(recip_result)
                else:
                    recipients.append(recip_result)
            except:
                self._logger.exception("Could not compute recipient")
                continue
        return recipients

    def quota(self):
        response = self._conn.get_send_quota().get('GetSendQuotaResponse')
        result = response if not response else response.get(
            'GetSendQuotaResult')
        return result

    def stats(self):
        response = self._conn.get_send_statistics().get(
            'GetSendStatisticsResponse')
        result = response if not response else response.get(
            'GetSendStatisticsResult')
        return result
