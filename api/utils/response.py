from typing import Optional
from flask import Request

def negotiate_content_type(req: Request) -> str:
    accept = (req.headers.get("Accept") or "").lower()
    if "text/plain" in accept:
        return "text/plain"
    if "application/xml" in accept:
        return "application/xml"
    if "application/json" in accept or "application/*" in accept or accept == "":
        return "application/json"
    return "text/plain"

def to_xml(obj: dict, root="response") -> str:
    def esc(x: str) -> str:
        return (x.replace("&","&amp;").replace("<","&lt;")
                  .replace(">","&gt;").replace('"',"&quot;").replace("'","&apos;"))
    parts = [f"<{root}>"]
    for k, v in obj.items():
        if v is None:
            parts.append(f"  <{k}/>")
        else:
            parts.append(f"  <{k}>{esc(str(v))}</{k}>")
    parts.append(f"</{root}>")
    return "\n".join(parts)
