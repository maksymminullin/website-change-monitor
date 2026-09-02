from pydantic import BaseModel


class FetchedPage(BaseModel):
    url: str
    title: str
    clean_text: str
    content_hash: str
    needs_js_upgrade: bool = False
