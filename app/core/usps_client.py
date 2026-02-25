import requests
import time
from datetime import datetime
from typing import List, Dict, Optional
import xml.etree.ElementTree as ET


class USPSClient:
    """USPS Tracking Client to fetch delivery status and delivered_at time."""

    USPS_ENDPOINT = "https://secure.shippingapis.com/ShippingAPI.dll"

    def __init__(self, user_id: str):
        self.user_id = user_id

    # -----------------------------
    # PUBLIC METHOD
    # -----------------------------
    def get_bulk_delivery_status(self, tracking_numbers: List[str]) -> List[Dict]:
        """
        Fetch delivery info for list of tracking numbers.

        Returns:
        [
            {
                "tracking_number": "...",
                "status": "Delivered / In Transit / Not Found",
                "delivered_at": datetime or None,
                "raw_message": str
            }
        ]
        """

        results = []
        batch_size = 30  # safe batch size

        for i in range(0, len(tracking_numbers), batch_size):
            batch = tracking_numbers[i:i + batch_size]

            xml_payload = self._build_xml(batch)
            response = self._call_usps(xml_payload)

            parsed = self._parse_response(response)
            results.extend(parsed)

            # Avoid USPS blocking
            time.sleep(1.5)

        return results

    # -----------------------------
    # BUILD XML REQUEST
    # -----------------------------
    def _build_xml(self, tracking_numbers: List[str]) -> str:
        root = ET.Element("TrackRequest", USERID=self.user_id)

        for tn in tracking_numbers:
            ET.SubElement(root, "TrackID", ID=tn)

        xml_string = ET.tostring(root, encoding="unicode")
        return xml_string

    # -----------------------------
    # CALL USPS API
    # -----------------------------
    def _call_usps(self, xml_payload: str) -> str:
        params = {
            "API": "TrackV2",
            "XML": xml_payload
        }

        response = requests.get(self.USPS_ENDPOINT, params=params, timeout=30)

        if response.status_code != 200:
            raise Exception(f"USPS API Error: {response.text}")

        return response.text

    # -----------------------------
    # PARSE RESPONSE
    # -----------------------------
    def _parse_response(self, xml_response: str) -> List[Dict]:
        results = []

        root = ET.fromstring(xml_response)

        for track_info in root.findall("TrackInfo"):

            tracking_number = track_info.attrib.get("ID")
            status = "Unknown"
            delivered_at: Optional[datetime] = None
            message = ""

            # Delivered event
            event = track_info.findtext("TrackSummary")

            if event:
                message = event

            # Check detailed events
            for detail in track_info.findall("TrackDetail"):
                event_text = detail.text or ""

                if "Delivered" in event_text:
                    status = "Delivered"

                    # Extract date & time
                    event_date = track_info.findtext("EventDate")
                    event_time = track_info.findtext("EventTime")

                    if event_date and event_time:
                        try:
                            delivered_at = datetime.strptime(
                                f"{event_date} {event_time}",
                                "%B %d, %Y %I:%M %p"
                            )
                        except:
                            delivered_at = None
                    break

            # If summary contains Delivered
            if "Delivered" in message and delivered_at is None:
                status = "Delivered"

            if status != "Delivered":
                status = "In Transit"

            results.append({
                "tracking_number": tracking_number,
                "status": status,
                "delivered_at": delivered_at,
                "raw_message": message
            })

        return results