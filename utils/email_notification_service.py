"""
Email Notification Service for Godfather Office Mafia Game
Uses Node.js nodemailer to send beautiful HTML emails
"""

import subprocess
import json
import os
from typing import List, Dict, Any

class GodfatherEmailService:
    def __init__(self):
        self.node_mailer_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../email/godfather_mailer.js"))
        self.mailer_dir = os.path.dirname(self.node_mailer_path)

        # Ensure email directory exists
        os.makedirs(self.mailer_dir, exist_ok=True)

    def send_day_start_reminder(self, player_emails: List[str], day: int) -> Dict[str, Any]:
        """
        Send day start reminder email

        Args:
            player_emails: List of player email addresses
            day: Current game day

        Returns:
            dict with success status and message
        """
        try:
            if not player_emails:
                return {
                    "success": False,
                    "message": "No recipient emails provided",
                    "sent_count": 0
                }

            # Prepare email data
            email_data = {
                "type": "day_start",
                "recipients": player_emails,
                "day": day
            }

            # Call nodemailer
            result = self._send_via_nodemailer(email_data)

            if result["success"]:
                return {
                    "success": True,
                    "message": f"Day {day} start email sent successfully",
                    "sent_count": len(player_emails),
                    "preview_url": result.get("preview_url")
                }
            else:
                return result

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to send day start email: {str(e)}",
                "sent_count": 0
            }

    def send_mission_reminder(self, player_emails: List[str], day: int, unlock_hour: int) -> Dict[str, Any]:
        """
        Send mission unlock reminder email

        Args:
            player_emails: List of player email addresses
            day: Current game day
            unlock_hour: Hour when missions unlock

        Returns:
            dict with success status and message
        """
        try:
            if not player_emails:
                return {
                    "success": False,
                    "message": "No recipient emails provided",
                    "sent_count": 0
                }

            email_data = {
                "type": "mission_unlock",
                "recipients": player_emails,
                "day": day,
                "unlock_hour": unlock_hour
            }

            result = self._send_via_nodemailer(email_data)

            if result["success"]:
                return {
                    "success": True,
                    "message": f"Mission unlock reminder sent successfully",
                    "sent_count": len(player_emails),
                    "preview_url": result.get("preview_url")
                }
            else:
                return result

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to send mission unlock email: {str(e)}",
                "sent_count": 0
            }

    def send_blackmarket_reminder(self, player_emails: List[str], open_time: str, items_count: int = 0) -> Dict[str, Any]:
        """
        Send black market reminder email

        Args:
            player_emails: List of player email addresses
            open_time: Time when black market opens
            items_count: Number of items available

        Returns:
            dict with success status and message
        """
        try:
            if not player_emails:
                return {
                    "success": False,
                    "message": "No recipient emails provided",
                    "sent_count": 0
                }

            email_data = {
                "type": "blackmarket",
                "recipients": player_emails,
                "open_time": open_time,
                "items_count": items_count
            }

            result = self._send_via_nodemailer(email_data)

            if result["success"]:
                return {
                    "success": True,
                    "message": f"Black market reminder sent successfully",
                    "sent_count": len(player_emails),
                    "preview_url": result.get("preview_url")
                }
            else:
                return result

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to send black market email: {str(e)}",
                "sent_count": 0
            }

    def _send_via_nodemailer(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send email via Node.js nodemailer

        Args:
            email_data: Email configuration data

        Returns:
            dict with success status
        """
        try:
            # Convert email data to JSON
            email_json = json.dumps(email_data)

            # Call Node.js mailer
            node_command = ['node', self.node_mailer_path, email_json]

            print(f"Executing: {' '.join(node_command)}")

            result = subprocess.run(
                node_command,
                cwd=self.mailer_dir,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=30
            )

            if result.returncode == 0:
                print(f"[SUCCESS] Email sent successfully")
                print(f"Output: {result.stdout}")

                # Extract preview URL if using Ethereal
                preview_url = None
                for line in result.stdout.split('\n'):
                    if '[INFO] Preview URL:' in line:
                        preview_url = line.split('[INFO] Preview URL:')[1].strip()
                        break

                message = "Email sent successfully"
                if preview_url:
                    message = f"Test email sent! View at: {preview_url}"

                return {
                    "success": True,
                    "message": message,
                    "output": result.stdout,
                    "preview_url": preview_url
                }
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                print(f"[ERROR] Email failed: {error_msg}")
                return {
                    "success": False,
                    "message": f"Nodemailer error: {error_msg}",
                    "output": error_msg
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Email sending timed out after 30 seconds"
            }
        except FileNotFoundError:
            return {
                "success": False,
                "message": f"Node.js mailer not found at: {self.node_mailer_path}. Please ensure Node.js is installed and the mailer file exists."
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}"
            }

# Create singleton instance
godfather_email_service = GodfatherEmailService()
