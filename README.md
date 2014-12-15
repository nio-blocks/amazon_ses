AmazonSESBlock
==========

Block for sending email via Amazon Simple Email Service

Properties
-----------

-   **region**: AWS region for SES (us_east_1, us_west_2, eu_west_1)
-   **creds**: An object containing your IAM identity (fields: access_key (str), access_secret (str))
-   **sender**: Sender email address. Must be verified with SES. See below for detail.
-   **recipients**: A list of recipient email addresses.
-   **message**: An object defining the contents of the emails (fields: subject (expression), body (expression))

Dependencies
------------

-   [boto](https://pypi.python.org/pypi/boto/)

Commands
--------

-   **quota**: Returns send-quota information for your SES account.
-   **stats**: Returns send, bounce, and complaint statistics for your SES account.

Input
-----
Any list of signals. Messages are constructed by evaluating message.subject and message.body against each signal.

Output
------
None

Verification of email addresses
-------------------------------
Each sender address used in SES must be registered and verified before use. To do so, visit the [AWS console](console.aws.amazon.com), select **Services->SES->Dashboard->Verified Senders->Email Addresses->Verify a New Email Address** and enter the desired address. Wait for the confirmation email and follow the link. You can now send emails from that address using SES!
