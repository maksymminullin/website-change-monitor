from enum import Enum

class PageStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"