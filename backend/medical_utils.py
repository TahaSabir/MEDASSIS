from typing import List

def extract_medical_terms(text: str) -> List[str]:
    """
    Identify medical terms in transcript
    Returns a list of medical terms found in the text
    """
    medical_terms = [
        "hypertension", "diabetes", "myocardial", 
        "infarction", "antibiotics", "analgesic"
    ]
    return [term for term in text.lower().split() if term in medical_terms]