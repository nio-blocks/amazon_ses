from nio.block.base import Block
from nio.util.discovery import discoverable
from nio.properties.holder import PropertyHolder
from nio.properties import Property
from nio.properties.object import ObjectProperty
from nio.properties.select import SelectProperty
from nio.properties.list import ListProperty
from nio.properties.string import StringProperty
from nio.properties.version import VersionProperty
from nio.command import command

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
    recip = Property(
        title="Recipient", default="info@n.io")


class Message(PropertyHolder):
    subject = Property(
        title="Subject", default="<No Value>")
    body = Property(
        title="Body", default="<No Value>")


@command("quota")
@command("stats")
@discoverable
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
    creds = ObjectProperty(
        AWSCreds, title="AWS Credentials", default=AWSCreds())
    sender = StringProperty(title="Sender Email", default="")
    to_recipients = ListProperty(
        Recipient, title="To Recipient Emails", default=[])
    cc_recipients = ListProperty(
        Recipient, title="CC Recipient Emails", default=[])
    bcc_recipients = ListProperty(
        Recipient, title="BCC Recipient Emails", default=[])
    message = ObjectProperty(Message, title="Message", default=Message())

    def __init__(self):
        super().__init__()
        self._conn = None

    def configure(self, context):
        super().configure(context)
        self._conn = connect_to_region(
            re.sub('_', '-', self.region().name),
            aws_access_key_id=self.creds().access_key(),
            aws_secret_access_key=self.creds().access_secret()
        )

    def process_signals(self, signals):
        for signal in signals:
            try:
                subject = self.message().subject(signal)
                body = self.message().body(signal)
            except:
                self.logger.exception("Could not compute subject/body")
                continue

            recipients = self._get_recipients(signal)
            if sum([len(recips) for recips in recipients.values()]) == 0:
                # Don't send if we have no recipients in any of our lists
                continue

            try:
                self._conn.send_email(
                    source=self.sender(),
                    subject=subject,
                    body=body,
                    html_body=body,
                    **recipients)
            except:
                self.logger.exception("Error sending mail")

    def _get_recipients(self, signal):
        """ Return a dict of destination recipients based on a signal.

        The return format should be ** expandable into the boto send_email
        function. This will include to, cc, and bcc recipients.
        """
        to_recipients = self._get_recipient(signal, self.to_recipients())
        cc_recipients = self._get_recipient(signal, self.cc_recipients())
        bcc_recipients = self._get_recipient(signal, self.bcc_recipients())

        return {
            "to_addresses": to_recipients,
            "cc_addresses": cc_recipients,
            "bcc_addresses": bcc_recipients
        }

    def _get_recipient(self, signal, recip_prop):
        """ Get the recipients for a configured recipient property """
        recipients = []
        for configured_recip in recip_prop:
            try:
                recip_result = configured_recip.recip(signal)
                if isinstance(recip_result, list):
                    # Allow the expression to evaluate to a list of recipients
                    recipients.extend(recip_result)
                else:
                    recipients.append(recip_result)
            except:
                self.logger.exception("Could not compute recipient")
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
