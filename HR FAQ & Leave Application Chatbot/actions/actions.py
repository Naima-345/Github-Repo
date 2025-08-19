

import sqlite3
from typing import Any, Text, Dict, List
import re
from rasa_sdk import Tracker, FormValidationAction, Action
from rasa_sdk.executor import CollectingDispatcher

class ValidateLeaveForm(FormValidationAction):
    """Validates leave_form slots: leave_type, start_date, end_date, reason, leave_days"""

    def name(self) -> Text:
        return "validate_leave_form"

    def validate_leave_type(
        self, value: Text, dispatcher: CollectingDispatcher,
        tracker: Tracker, domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:

        allowed_types = [
            "annual", "sick", "casual", "maternity",
            "paternity", "unpaid", "study", "emergency leave",
            "compensatory", "bereavement leave"
        ]

        # Normalize input
        clean_value = value.strip().lower()
        if clean_value in [t.lower() for t in allowed_types]:
            return {"leave_type": clean_value}

        dispatcher.utter_message(text=" Invalid leave type. Please choose a valid type.")
        return {"leave_type": None}

    def validate_date(
        self, value: Text, dispatcher: CollectingDispatcher,
        tracker: Tracker, domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:

        requested_slot = tracker.get_slot("requested_slot")
        if re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", value) or re.match(r"^\d{4}-\d{2}-\d{2}$", value):
            return {requested_slot: value}

        dispatcher.utter_message(text=" Invalid date format. Please use DD/MM/YYYY or YYYY-MM-DD.")
        return {requested_slot: None}

    def validate_reason(
        self, value: Text, dispatcher: CollectingDispatcher,
        tracker: Tracker, domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:

        if value and len(value.strip()) > 2:
            return {"reason": value}

        dispatcher.utter_message(text=" Please provide a short reason for your leave.")
        return {"reason": None}

    def validate_leave_days(
        self, value: Any, dispatcher: CollectingDispatcher,
        tracker: Tracker, domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:

        try:
            days = int(value)
            if 0 < days <= 365:
                return {"leave_days": days}
        except ValueError:
            pass

        dispatcher.utter_message(text="❌ Enter a valid number of leave days (1–365).")
        return {"leave_days": None}

# # class ActionSaveLeaveApplication(Action):
#     def name(self) -> Text:
#         return "action_save_leave_application"
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#         # Get slot values
#         leave_type = tracker.get_slot("leave_type")
#         start_date = tracker.get_slot("start_date")
#         end_date = tracker.get_slot("end_date")
#         reason = tracker.get_slot("reason")
#         leave_days = tracker.get_slot("leave_days")
#         # Connect to the SQLite database
#         conn = sqlite3.connect("leave_applications.db")
#         cursor = conn.cursor()
#         # Insert the leave application into the database
#         cursor.execute("""
#         INSERT INTO leave_applications (leave_type, start_date, end_date, reason, leave_days)
#         VALUES (?, ?, ?, ?, ?)
#         """, (leave_type, start_date, end_date, reason, leave_days))
#         conn.commit()
#         conn.close()
#         dispatcher.utter_message(text="Your leave application has been saved successfully!")
#         return []

class ActionHandleFAQ(Action):
    """Handles FAQ questions directly without triggering leave form"""

    def name(self) -> Text:
        return "action_handle_faq"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        latest_intent = tracker.latest_message['intent'].get('name')

        faq_responses = {
            'ask_leave_policy': 'utter_ask_leave_policy',
            'ask_salary_date': 'utter_ask_salary_date',
            'ask_attendance_rules': 'utter_ask_attendance_rules',
            'thank_you': 'utter_thank_you'
        }

        if latest_intent in faq_responses:
            dispatcher.utter_message(response=faq_responses[latest_intent])

        return []


class ActionSubmitLeave(Action):
    """Submits the leave application to the database"""
    def name(self) -> Text:
        return "action_submit_leave"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Get slot values
        leave_type = tracker.get_slot("leave_type")
        start_date = tracker.get_slot("start_date")
        end_date = tracker.get_slot("end_date")
        reason = tracker.get_slot("reason")
        leave_days = tracker.get_slot("leave_days")
        
        # For now, you can hardcode a name or get from a slot if available
        name = "John Doe"  # You can replace this with a dynamic value if needed
        # Connect to SQLite DB
        conn = sqlite3.connect("leave_applications.db")
        cursor = conn.cursor()
        # Insert leave application into table
        cursor.execute("""
            INSERT INTO leave_applications (leave_type, start_date, end_date, reason, leave_days)
            VALUES (?, ?, ?, ?, ?)
        """, (leave_type, start_date, end_date, reason, leave_days))
        conn.commit()
        conn.close()
        dispatcher.utter_message(
            text=f"✅ Leave request submitted!\n"
                 f"Type: {leave_type}\n"
                 f"From: {start_date} To: {end_date}\n"
                 f"Days: {leave_days}\n"
                 f"Reason: {reason}"
        )
        return []
    


def is_english(text):
    try:
        text.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    return True