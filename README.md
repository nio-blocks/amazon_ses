AmazonSES
=========
Block for sending email via Amazon Simple Email Service.  HTML message bodies are supported.

Properties
----------
- **bcc_recipients**: A list of bcc recipient email addresses. These addresses can be expressions. The expressions can also evaluate to lists for your convenience.
- **cc_recipients**: A list of cc recipient email addresses. These addresses can be expressions. The expressions can also evaluate to lists for your convenience.
- **creds**: An object containing your IAM identity (access_key: string, access_secret: string)
- **message**: An object defining the contents of the emails (subject: expression, body: expression)
- **region**: AWS region for SES (e.g.: us_east_1)
- **sender**: Sender email address. Must be verified with SES. See below for detail.
- **to_recipients**: A list of recipient email addresses. These addresses can be expressions. The expressions can also evaluate to lists for your convenience.

Inputs
------
- **default**: Any list of signals.  Messages are constructed by evaluating message.subject and message.body against each signal.

Outputs
-------

Commands
--------
- **quota**: Returns send-quota information for your SES account.
- **stats**: Returns send, bounce, and complaint statistics for your SES account.

Dependencies
------------
-   [boto](https://pypi.python.org/pypi/boto/)

Verification of email addresses
-------------------------------
Each sender address used in SES must be registered and verified before use. To do so, visit the [AWS console](console.aws.amazon.com), select **Services->SES->Dashboard->Verified Senders->Email Addresses->Verify a New Email Address** and enter the desired address. Wait for the confirmation email and follow the link. You can now send emails from that address using SES!

