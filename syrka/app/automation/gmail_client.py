"""Gmail API client for email automation."""

import logging
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from app.config import settings

logger = logging.getLogger(__name__)


class GmailClient:
    """Gmail API client for sending and tracking job applications."""

    def __init__(self, credentials_path: str = None):
        """
        Initialize Gmail client.

        Args:
            credentials_path: Path to OAuth2 credentials file
        """
        self.credentials_path = credentials_path or settings.GMAIL_CREDENTIALS_PATH
        self.token_path = settings.GMAIL_TOKEN_PATH
        self.scopes = settings.GMAIL_SCOPES
        self.service = None

    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using OAuth2.

        Returns:
            True if authentication successful
        """
        creds = None

        # Load existing token
        if Path(self.token_path).exists():
            creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)

        # Refresh or get new token
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not Path(self.credentials_path).exists():
                    logger.error(f"Credentials file not found: {self.credentials_path}")
                    return False

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.scopes
                )
                creds = flow.run_local_server(port=0)

            # Save token
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        try:
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail authentication successful")
            return True
        except Exception as e:
            logger.error(f"Gmail authentication failed: {str(e)}")
            return False

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: Optional[list[str]] = None
    ) -> Optional[str]:
        """
        Send email via Gmail API.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            attachments: Optional list of file paths to attach

        Returns:
            Message ID if successful, None otherwise
        """
        if not self.service:
            if not self.authenticate():
                return None

        try:
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject

            message.attach(MIMEText(body, 'plain'))

            # Add attachments
            if attachments:
                for filepath in attachments:
                    if Path(filepath).exists():
                        with open(filepath, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename={Path(filepath).name}'
                            )
                            message.attach(part)

            # Encode message
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # Send
            send_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()

            message_id = send_message['id']
            logger.info(f"Email sent successfully: {message_id}")

            return message_id

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return None

    def check_replies(self, thread_id: str) -> list[dict]:
        """
        Check for replies in an email thread.

        Args:
            thread_id: Gmail thread ID

        Returns:
            List of reply messages
        """
        if not self.service:
            if not self.authenticate():
                return []

        try:
            thread = self.service.users().threads().get(
                userId='me',
                id=thread_id
            ).execute()

            messages = thread.get('messages', [])
            replies = []

            for msg in messages[1:]:  # Skip first message (original)
                headers = msg.get('payload', {}).get('headers', [])
                sender = next((h['value'] for h in headers if h['name'] == 'From'), '')

                replies.append({
                    'id': msg['id'],
                    'from': sender,
                    'snippet': msg.get('snippet', '')
                })

            return replies

        except Exception as e:
            logger.error(f"Failed to check replies: {str(e)}")
            return []

    def get_message_status(self, message_id: str) -> str:
        """
        Get message status.

        Args:
            message_id: Gmail message ID

        Returns:
            Status string: 'sent', 'read', 'replied', 'unknown'
        """
        if not self.service:
            if not self.authenticate():
                return 'unknown'

        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='metadata'
            ).execute()

            labels = message.get('labelIds', [])

            if 'SENT' in labels:
                thread_id = message.get('threadId')
                replies = self.check_replies(thread_id)
                if replies:
                    return 'replied'
                return 'sent'

            return 'unknown'

        except Exception as e:
            logger.error(f"Failed to get message status: {str(e)}")
            return 'unknown'
