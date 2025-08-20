import sqlite3
import re
from typing import Any, Text, Dict, List
from rasa_sdk import Tracker, FormValidationAction, Action
from rasa_sdk.executor import CollectingDispatcher

# ✅ Language detection helper
def is_english(text: Text) -> bool:
    bengali_pattern = re.compile(r'[\u0980-\u09FF]')
    if bengali_pattern.search(text):
        return False
    ascii_chars = sum(c.isascii() for c in text)
    total_chars = len(text)
    ascii_ratio = ascii_chars / max(total_chars, 1)
    return ascii_ratio > 0.8

# ✅ Centralized bilingual response
def respond_by_language(dispatcher, user_text, en_response, bn_response):
    if is_english(user_text):
        dispatcher.utter_message(text=en_response)
    else:
        dispatcher.utter_message(text=bn_response)

# ✅ Leave Form Validation
class ValidateLeaveForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_leave_form"

    def validate_leave_type(self, value: Text, dispatcher: CollectingDispatcher,
                            tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        allowed_types = [
            "annual", "sick", "casual", "maternity", "paternity",
            "unpaid", "study", "emergency leave", "compensatory", "bereavement leave"
        ]
        clean_value = value.strip().lower()
        if clean_value in [t.lower() for t in allowed_types]:
            return {"leave_type": clean_value}

        respond_by_language(dispatcher, value,
            "❌ Invalid leave type. Please choose a valid type.",
            "❌ সঠিক ছুটির ধরন দিন।"
        )
        return {"leave_type": None}

    def validate_date(self, value: Text, dispatcher: CollectingDispatcher,
                      tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        requested_slot = tracker.get_slot("requested_slot")
        if re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", value) or re.match(r"^\d{4}-\d{2}-\d{2}$", value):
            return {requested_slot: value}

        respond_by_language(dispatcher, value,
            "❌ Invalid date format. Please use DD/MM/YYYY or YYYY-MM-DD.",
            "❌ সঠিক তারিখের ফরম্যাট দিন (DD/MM/YYYY বা YYYY-MM-DD)।"
        )
        return {requested_slot: None}

    def validate_reason(self, value: Text, dispatcher: CollectingDispatcher,
                        tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        if value and len(value.strip()) > 2:
            return {"reason": value}

        respond_by_language(dispatcher, value,
            "⚠️ Please provide a short reason for your leave.",
            "⚠️ অনুগ্রহ করে ছুটির একটি ছোট কারণ লিখুন।"
        )
        return {"reason": None}

    def validate_leave_days(self, value: Any, dispatcher: CollectingDispatcher,
                            tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        try:
            days = int(value)
            if 0 < days <= 365:
                return {"leave_days": days}
        except ValueError:
            pass

        respond_by_language(dispatcher, str(value),
            "❌ Enter a valid number of leave days (1–365).",
            "❌ সঠিক দিনের সংখ্যা দিন (১–৩৬৫)।"
        )
        return {"leave_days": None}

# ✅ Leave Submission to SQLite DB
class ActionSubmitLeave(Action):
    def name(self) -> Text:
        return "action_submit_leave"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        leave_type = tracker.get_slot("leave_type")
        start_date = tracker.get_slot("start_date")
        end_date = tracker.get_slot("end_date")
        reason = tracker.get_slot("reason")
        leave_days = tracker.get_slot("leave_days")

        conn = sqlite3.connect("leave_applications.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO leave_applications (leave_type, start_date, end_date, reason, leave_days)
            VALUES (?, ?, ?, ?, ?)
        """, (leave_type, start_date, end_date, reason, leave_days))
        conn.commit()
        conn.close()

        user_text = tracker.latest_message.get("text", "")
        respond_by_language(dispatcher, user_text,
            f"✅ Leave request submitted!\nType: {leave_type}\nFrom: {start_date} To: {end_date}\nDays: {leave_days}\nReason: {reason}",
            f"✅ ছুটির আবেদন জমা হয়েছে!\nধরন: {leave_type}\nতারিখ: {start_date} থেকে {end_date}\nদিন: {leave_days}\nকারণ: {reason}"
        )
        return []

# ✅ Bangla-only Leave Handler (for apply_leave_bn intent)
class ActionApplyLeaveBN(Action):
    def name(self) -> Text:
        return "action_apply_leave_bn"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        leave_type = tracker.get_slot("leave_type") or "ছুটি"
        date = tracker.get_slot("start_date") or "নির্দিষ্ট তারিখ"
        end_date = tracker.get_slot("end_date") or "নির্দিষ্ট তারিখ"
        reason = tracker.get_slot("reason") or "উল্লেখ নেই"
        leave_days = tracker.get_slot("leave_days") or "নির্দিষ্ট দিন"

        response = (
            f"✅ ছুটির আবেদন গ্রহণ করা হয়েছে!\n"
            f"ধরন: {leave_type}\n"
            f"তারিখ: {date} থেকে {end_date}\n"
            f"দিন: {leave_days}\n"
            f"কারণ: {reason}"
        )
        dispatcher.utter_message(text=response)
        return []
