from typing import Optional, Union, List, Dict
from flask import Request

def negotiate_content_type(req: Request) -> str:
    """
    Determines the best response content type based on the Accept header.
    Defaults to application/json if the header is missing or ambiguous.
    """
    accept = req.headers.get("Accept", "application/json").lower()
    if "text/plain" in accept:
        return "text/plain"
    if "application/xml" in accept:
        return "application/xml"
    return "application/json"

def to_xml(obj: Union[Dict, List[Dict]], root="response", item_name="item") -> str:
    """
    Serializes a dictionary or a list of dictionaries to an XML string.
    """
    def esc(x: any) -> str:
        return str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")

    def dict_to_xml_parts(d: Dict, indent: str) -> List[str]:
        parts = []
        for k, v in d.items():
            parts.append(f"{indent}<{k}/>" if v is None else f"{indent}<{k}>{esc(v)}</{k}>")
        return parts

    parts = [f"<{root}>"]
    if isinstance(obj, list):
        for item_dict in obj:
            parts.extend([f"  <{item_name}>", *dict_to_xml_parts(item_dict, indent="    "), f"  </{item_name}>"])
    elif isinstance(obj, dict):
        parts.extend(dict_to_xml_parts(obj, indent="  "))

    parts.append(f"</{root}>")
    return "\n".join(parts)
