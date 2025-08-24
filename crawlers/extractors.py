# 正則擷取：CVE、Email
import re


def extract_cves(text):
    """傳回去重排序後的 CVE 清單"""
    if not text:
        return []
    
    pattern = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)
    found = set(m.upper() for m in pattern.findall(text))
    return sorted(found)


def extract_emails(text):
    """傳回去重排序後的 Email 清單"""
    if not text:
        return []
    
    pattern = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    return sorted(set(pattern.findall(text)))
