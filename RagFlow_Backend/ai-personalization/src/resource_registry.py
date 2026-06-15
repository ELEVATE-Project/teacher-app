"""
resource_registry.py
Curated teacher-training content sources with geo-tagging.
Used by ragflow_client.py to seed/recommend resources based on teacher location.
"""
# TODO : This is just a base to use later when multiple datasets are available. Not rn , for now as long as it works for one dataset its fine
from typing import List, Optional

RESOURCE_REGISTRY = [
    # ── NATIONAL / MULTI-STATE ──────────────────────────────────────────────
    {
        "id": "epathshala-teachers",
        "name": "ePathshala – Teacher Resources",
        "url": "https://epathshala.nic.in/epathshala.php?id=Teachers&ln=en",
        "languages": ["en", "hi"],
        "states": ["ALL"],          
        "organisations": ["NCERT"],
        "tags": ["ncert", "textbook", "digital", "teacher-resource"],
        "competency_areas": ["content_knowledge", "pedagogy", "technology_usage"],
        "priority": 1,              
        "exemplary": True,
    },
    {
        "id": "unesco-teacher",
        "name": "UNESCO Teacher Training Documents",
        "url": "https://unesdoc.unesco.org/search/72a71bb0-74c9-4ef5-a26b-934dd8b90ab8/N-5d0a3661-80fa-4e8e-8c40-23c664ae2002",
        "languages": ["en"],
        "states": ["ALL"],
        "organisations": ["UNESCO"],
        "tags": ["international", "pedagogy", "best-practices", "teacher-training"],
        "competency_areas": ["pedagogy", "student_engagement", "classroom_management"],
        "priority": 1,
        "exemplary": True,
    },

    # ── KARNATAKA ────────────────────────────────────────────────────────────
    {
        "id": "dsert-kalika-balavardhane",
        "name": "DSERT Karnataka – Kalika Balavardhane",
        "url": "https://dsert.karnataka.gov.in/42/Kalika%20Balavardhane/en",
        "languages": ["kn", "en"],
        "states": ["KA"],
        "organisations": ["DSERT", "Karnataka State"],
        "tags": ["remedial", "learning-enhancement", "activity-based", "primary"],
        "competency_areas": ["pedagogy", "student_engagement", "content_knowledge"],
        "priority": 1,
        "exemplary": True,
    },
    {
        "id": "dsert-sethubandha",
        "name": "DSERT Karnataka – Sethubandha Literature",
        "url": "https://dsert.karnataka.gov.in/40/Sethubandha%20Literature/en",
        "languages": ["kn", "en"],
        "states": ["KA"],
        "organisations": ["DSERT", "Karnataka State"],
        "tags": ["bridge-course", "foundational-literacy", "multilevel"],
        "competency_areas": ["content_knowledge", "pedagogy"],
        "priority": 1,
        "exemplary": True,
    },

    # ── KERALA ────────────────────────────────────────────────────────────────
    {
        "id": "scert-kerala",
        "name": "SCERT Kerala",
        "url": "https://scert.kerala.gov.in/",
        "languages": ["ml", "en"],
        "states": ["KL"],
        "organisations": ["SCERT Kerala"],
        "tags": ["curriculum", "teacher-training", "resource-material"],
        "competency_areas": ["content_knowledge", "pedagogy", "classroom_management"],
        "priority": 1,
        "exemplary": True,
    },

    # ── TELANGANA ─────────────────────────────────────────────────────────────
    {
        "id": "scert-telangana",
        "name": "SCERT Telangana",
        "url": "https://www.scert.telangana.gov.in/DisplayContent.aspx?encry=NDP5wlgY6AVsqA0OBlKm3w==",
        "languages": ["te", "en"],
        "states": ["TS"],
        "organisations": ["SCERT Telangana"],
        "tags": ["teacher-training", "in-service", "district-training"],
        "competency_areas": ["pedagogy", "content_knowledge", "student_engagement"],
        "priority": 1,
        "exemplary": True,
    },

    # ── ADDITIONAL DISCOVERABLE STATE RESOURCES ──────────────────────────────
    # These follow the same pattern , add more state SCERT/DIET portals here.
    {
        "id": "scert-up",
        "name": "SCERT Uttar Pradesh",
        "url": "https://scert.up.gov.in/",
        "languages": ["hi", "en"],
        "states": ["UP"],
        "organisations": ["SCERT UP"],
        "tags": ["teacher-training", "in-service", "hindi-medium"],
        "competency_areas": ["content_knowledge", "pedagogy", "classroom_management"],
        "priority": 2,
        "exemplary": False,
    },
    {
        "id": "diet-rajasthan",
        "name": "DIET Rajasthan / SIERT",
        "url": "https://siert.raj.nic.in/",
        "languages": ["hi", "en"],
        "states": ["RJ"],
        "organisations": ["SIERT Rajasthan"],
        "tags": ["teacher-training", "distance-education"],
        "competency_areas": ["pedagogy", "content_knowledge"],
        "priority": 2,
        "exemplary": False,
    },
    {
        "id": "scert-maharashtra",
        "name": "SCERT Maharashtra",
        "url": "https://www.scert.mah.nic.in/",
        "languages": ["mr", "en"],
        "states": ["MH"],
        "organisations": ["SCERT Maharashtra"],
        "tags": ["teacher-training", "marathi-medium"],
        "competency_areas": ["pedagogy", "content_knowledge"],
        "priority": 2,
        "exemplary": False,
    },
    {
        "id": "scert-gujarat",
        "name": "GCERT Gujarat",
        "url": "https://gcert.gujarat.gov.in/",
        "languages": ["gu", "en"],
        "states": ["GJ"],
        "organisations": ["GCERT Gujarat"],
        "tags": ["teacher-training", "gujarati-medium"],
        "competency_areas": ["pedagogy", "content_knowledge", "student_engagement"],
        "priority": 2,
        "exemplary": False,
    },
    {
        "id": "scert-mp",
        "name": "SCERT Madhya Pradesh",
        "url": "https://scert.mponline.gov.in/",
        "languages": ["hi", "en"],
        "states": ["MP"],
        "organisations": ["SCERT MP"],
        "tags": ["teacher-training", "hindi-medium"],
        "competency_areas": ["pedagogy", "content_knowledge"],
        "priority": 2,
        "exemplary": False,
    },
    {
        "id": "scert-wb",
        "name": "WBBSE / SCERT West Bengal",
        "url": "https://wbbse.wb.gov.in/",
        "languages": ["bn", "en"],
        "states": ["WB"],
        "organisations": ["SCERT West Bengal"],
        "tags": ["teacher-training", "bengali-medium"],
        "competency_areas": ["content_knowledge", "pedagogy"],
        "priority": 2,
        "exemplary": False,
    },
    {
        "id": "scert-odisha",
        "name": "SCERT Odisha",
        "url": "https://scertodisha.nic.in/",
        "languages": ["or", "en"],
        "states": ["OD"],
        "organisations": ["SCERT Odisha"],
        "tags": ["teacher-training", "odia-medium"],
        "competency_areas": ["content_knowledge", "pedagogy"],
        "priority": 2,
        "exemplary": False,
    },
    {
        "id": "scert-ap",
        "name": "SCERT Andhra Pradesh",
        "url": "https://scert.ap.gov.in/",
        "languages": ["te", "en"],
        "states": ["AP"],
        "organisations": ["SCERT AP"],
        "tags": ["teacher-training", "telugu-medium"],
        "competency_areas": ["pedagogy", "content_knowledge"],
        "priority": 2,
        "exemplary": False,
    },
    {
        "id": "scert-tn",
        "name": "SCERT Tamil Nadu",
        "url": "https://www.tn.gov.in/dept/scert",
        "languages": ["ta", "en"],
        "states": ["TN"],
        "organisations": ["SCERT Tamil Nadu"],
        "tags": ["teacher-training", "tamil-medium"],
        "competency_areas": ["pedagogy", "content_knowledge", "student_engagement"],
        "priority": 2,
        "exemplary": False,
    },
    {
        "id": "scert-bihar",
        "name": "Bihar SCERT / BSEB",
        "url": "https://biharscert.bih.nic.in/",
        "languages": ["hi", "en"],
        "states": ["BR"],
        "organisations": ["SCERT Bihar"],
        "tags": ["teacher-training", "hindi-medium"],
        "competency_areas": ["content_knowledge", "pedagogy"],
        "priority": 2,
        "exemplary": False,
    },
]

# ── State code → common abbreviation map ────────────────────────────────────
STATE_CLUSTER_MAP = {
    # Maps the "cluster" field stored in the teachers table (could be city/district)
    # to a state code, so we can prefer geo-relevant resources.
    # Extend this as your cluster naming convention becomes clearer.
    "karnataka": "KA", "bangalore": "KA", "bengaluru": "KA", "mysuru": "KA",
    "kerala": "KL", "thiruvananthapuram": "KL", "kochi": "KL", "kozhikode": "KL",
    "telangana": "TS", "hyderabad": "TS", "warangal": "TS", "nizamabad": "TS",
    "andhra pradesh": "AP", "vijayawada": "AP", "visakhapatnam": "AP",
    "uttar pradesh": "UP", "lucknow": "UP", "varanasi": "UP", "agra": "UP", "kanpur": "UP",
    "maharashtra": "MH", "mumbai": "MH", "pune": "MH", "nagpur": "MH",
    "rajasthan": "RJ", "jaipur": "RJ", "udaipur": "RJ", "jodhpur": "RJ",
    "gujarat": "GJ", "ahmedabad": "GJ", "surat": "GJ", "gandhinagar": "GJ",
    "madhya pradesh": "MP", "bhopal": "MP", "indore": "MP",
    "west bengal": "WB", "kolkata": "WB",
    "odisha": "OD", "bhubaneswar": "OD",
    "tamil nadu": "TN", "chennai": "TN", "coimbatore": "TN",
    "bihar": "BR", "patna": "BR",
}


def get_resources_for_cluster(cluster: str, competency_area: Optional[str] = None) -> List[dict]:
    """
    Return resources sorted by geo-relevance and priority.
    cluster: the teacher's cluster string (city / district / state)
    competency_area: optional filter (e.g. 'pedagogy')
    """
    cluster_lower = cluster.lower()
    state_code = None
    for keyword, code in STATE_CLUSTER_MAP.items():
        if keyword in cluster_lower:
            state_code = code
            break

    results = []
    for r in RESOURCE_REGISTRY:
        if competency_area and competency_area not in r["competency_areas"]:
            continue
        geo_score = 0
        if state_code and state_code in r["states"]:
            geo_score = 10
        elif "ALL" in r["states"]:
            geo_score = 5
        results.append({**r, "_geo_score": geo_score})

    results.sort(key=lambda x: (-x["_geo_score"], x["priority"]))
    return results


def get_exemplary_resources() -> List[dict]:
    return [r for r in RESOURCE_REGISTRY if r.get("exemplary")]