"""
JalaNetra Alert Text Generator
Generates SMS and Polly voice-note text previews.
DEMO MODE: No real SMS or calls are ever sent.
"""
from __future__ import annotations

from datetime import date
from typing import Any


DEMO_DISCLAIMER = (
    "\n[DEMO ONLY — No real message will be sent in demo mode.]"
)


def generate_sms_text(forecast: dict[str, Any], language: str = "en-IN") -> str:
    """
    Generate the SMS text that WOULD be sent if this were production.
    Returns plaintext only. Never sends anything.
    """
    ward_name = forecast.get("ward_name", "your ward")
    risk = forecast.get("risk_level", "unknown")
    book_by = forecast.get("book_tanker_by", "soon")
    days = forecast.get("days_to_dry_estimate")
    confidence = forecast.get("confidence", "low")
    is_synthetic = forecast.get("synthetic", True)
    is_historical = risk == "historical_context" or not forecast.get("forecast_current", True)

    if is_historical and not forecast.get("is_scenario_simulation"):
        if language == "hi-IN":
            return (
                f"[परिदृश्य पूर्वावलोकन] JalaNetra: {ward_name} के लिए सांकेतिक पूर्वावलोकन। "
                "ऐतिहासिक CGWB डेटा — वर्तमान पूर्वानुमान अनुपलब्ध। jalanetra.demo पर स्थिति दर्ज करें।"
            )
        return (
            f"[SCENARIO PREVIEW] JalaNetra: Illustrative preview for {ward_name}. "
            "Historical CGWB observation only — current forecast unavailable. Report status at jalanetra.demo"
        )

    days_str = f"~{days} days" if days else "an unknown period"

    if language == "hi-IN":
        return _sms_hindi(ward_name, risk, book_by, days_str, confidence, is_synthetic)
    return _sms_english(ward_name, risk, book_by, days_str, confidence, is_synthetic)


def _sms_english(ward_name, risk, book_by, days_str, confidence, is_synthetic) -> str:
    demo_note = " [DEMO DATA]" if is_synthetic else ""
    confidence_note = " (low confidence)" if confidence == "low" else ""
    risk_map = {
        "critical": f"CRITICAL water shortage in {ward_name}! Act immediately.",
        "high": f"High water stress expected in {ward_name} in {days_str}.",
        "moderate": f"Moderate water stress expected in {ward_name}.",
        "low": f"Water supply in {ward_name} is currently stable.",
    }
    headline = risk_map.get(risk, f"Water stress alert for {ward_name}.")
    return (
        f"JalaNetra Alert{demo_note}: {headline} "
        f"Consider booking a tanker by {book_by}{confidence_note}. "
        f"jalanetra.demo/ward — JalaNetra Water Early Warning"
    )


def _sms_hindi(ward_name, risk, book_by, days_str, confidence, is_synthetic) -> str:
    demo_note = " [डेमो डेटा]" if is_synthetic else ""
    return (
        f"JalaNetra सूचना{demo_note}: {ward_name} में {days_str} में जल संकट संभावित है। "
        f"{book_by} तक टैंकर बुक करें। jalanetra.demo/ward"
    )


def generate_voice_text_english(forecast: dict[str, Any]) -> str:
    """Generate English Polly voice-note script (preview only)."""
    ward_name = forecast.get("ward_name", "your ward")
    risk = forecast.get("risk_level", "unknown")
    book_by = forecast.get("book_tanker_by", "soon")
    days = forecast.get("days_to_dry_estimate")
    is_synthetic = forecast.get("synthetic", True)
    is_historical = risk == "historical_context" or not forecast.get("forecast_current", True)

    if is_historical and not forecast.get("is_scenario_simulation"):
        return (
            f"Hello. This is an illustrative scenario preview for JalaNetra, the Mangaluru Water Early Warning System. "
            f"For {ward_name}, verified CGWB groundwater data is historical and a current forecast is unavailable. "
            "Please report your current water availability at jalanetra.demo. Thank you."
        )

    days_phrase = f"approximately {days} days" if days else "a limited period"
    demo_note = " This is a demo alert using sample data." if is_synthetic else ""

    if risk == "critical":
        urgency = "a critical water shortage is expected immediately"
    elif risk == "high":
        urgency = f"significant water stress is expected in {days_phrase}"
    elif risk == "moderate":
        urgency = f"moderate water stress may occur in {days_phrase}"
    else:
        urgency = "water supply is currently stable"

    return (
        f"Hello. This is JalaNetra, the Mangaluru Water Early Warning System.{demo_note} "
        f"For {ward_name}, {urgency}. "
        f"We recommend booking a water tanker by {book_by} as a precaution. "
        f"Visit jalanetra.demo for details. Thank you."
    )


def generate_voice_text_hindi(forecast: dict[str, Any]) -> str:
    """Generate Hindi Polly voice-note script (preview only)."""
    ward_name = forecast.get("ward_name", "your ward")
    book_by = forecast.get("book_tanker_by", "जल्द")
    days = forecast.get("days_to_dry_estimate")
    is_synthetic = forecast.get("synthetic", True)
    risk = forecast.get("risk_level", "unknown")
    is_historical = risk == "historical_context" or not forecast.get("forecast_current", True)

    if is_historical and not forecast.get("is_scenario_simulation"):
        return (
            f"नमस्ते। यह JalaNetra की ओर से एक सांकेतिक परिदृश्य पूर्वावलोकन है। "
            f"{ward_name} के लिए उपलब्ध भूजल डेटा ऐतिहासिक है और वर्तमान पूर्वानुमान अनुपलब्ध है। "
            "कृपया वर्तमान स्थिति jalanetra.demo पर दर्ज करें। धन्यवाद।"
        )

    days_phrase = f"लगभग {days} दिनों में" if days else "जल्द"
    demo_note = " यह एक डेमो अलर्ट है जो नमूना डेटा का उपयोग कर रहा है।" if is_synthetic else ""

    return (
        f"नमस्ते।{demo_note} यह JalaNetra मंगलुरु जल चेतावनी प्रणाली है। "
        f"{ward_name} में {days_phrase} जल संकट की संभावना है। "
        f"कृपया {book_by} तक टैंकर बुक करें। धन्यवाद।"
    )


def build_alert_preview(forecast: dict[str, Any], language: str = "en-IN") -> dict[str, Any]:
    """
    Build a full alert preview object. No SMS or call is sent.
    The preview shows what WOULD be sent in production.
    """
    risk = forecast.get("risk_level", "low")
    is_historical = risk == "historical_context" or not forecast.get("forecast_current", True)
    is_scenario = bool(forecast.get("is_scenario_simulation"))
    is_triggered = (not is_historical or is_scenario) and (risk in ("high", "critical"))

    if is_historical and not is_scenario:
        trigger_reason = "Illustrative scenario preview — not triggered by current measurements"
        disclaimer = (
            "Illustrative scenario preview — not triggered by current measurements. "
            "No SMS, WhatsApp, or phone call is sent in demo mode."
        )
    else:
        trigger_reason = (
            f"Risk level is '{risk}' which meets alert threshold" if is_triggered
            else f"Risk level is '{risk}' — below alert threshold; no alert would be sent"
        )
        disclaimer = (
            "This is a preview only. No SMS, WhatsApp, or phone call is sent "
            "in demo mode. In production, this message would be dispatched via "
            "AWS SNS and Amazon Polly."
        )

    return {
        "demo_only": True,
        "no_sms_sent": True,
        "no_call_made": True,
        "alert_triggered": is_triggered,
        "trigger_reason": trigger_reason,
        "ward_id": forecast.get("ward_id"),
        "ward_name": forecast.get("ward_name"),
        "risk_level": risk,
        "book_tanker_by": forecast.get("book_tanker_by"),
        "sms_text_en": generate_sms_text(forecast, "en-IN"),
        "sms_text_hi": generate_sms_text(forecast, "hi-IN"),
        "voice_text_en": generate_voice_text_english(forecast),
        "voice_text_hi": generate_voice_text_hindi(forecast),
        "aws_polly_voice_en": "Kajal (en-IN) — Amazon Polly",
        "aws_polly_voice_hi": "Aditi (hi-IN) — Amazon Polly",
        "aws_sns_would_send_to": "masked phone numbers in alert_subscriptions table",
        "disclaimer": disclaimer,
        "data_mode": forecast.get("data_mode", "demo"),
        "synthetic": forecast.get("synthetic", True),
    }
