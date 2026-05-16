"""
CampusBuzz Kenya - Seed Data
All 47 counties + all major universities and colleges in Kenya
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import County, University, UniversityType


COUNTIES = [
    ("Mombasa", "001"), ("Kwale", "002"), ("Kilifi", "003"), ("Tana River", "004"),
    ("Lamu", "005"), ("Taita-Taveta", "006"), ("Garissa", "007"), ("Wajir", "008"),
    ("Mandera", "009"), ("Marsabit", "010"), ("Isiolo", "011"), ("Meru", "012"),
    ("Tharaka-Nithi", "013"), ("Embu", "014"), ("Kitui", "015"), ("Machakos", "016"),
    ("Makueni", "017"), ("Nyandarua", "018"), ("Nyeri", "019"), ("Kirinyaga", "020"),
    ("Murang'a", "021"), ("Kiambu", "022"), ("Turkana", "023"), ("West Pokot", "024"),
    ("Samburu", "025"), ("Trans Nzoia", "026"), ("Uasin Gishu", "027"), ("Elgeyo-Marakwet", "028"),
    ("Nandi", "029"), ("Baringo", "030"), ("Laikipia", "031"), ("Nakuru", "032"),
    ("Narok", "033"), ("Kajiado", "034"), ("Kericho", "035"), ("Bomet", "036"),
    ("Kakamega", "037"), ("Vihiga", "038"), ("Bungoma", "039"), ("Busia", "040"),
    ("Siaya", "041"), ("Kisumu", "042"), ("Homa Bay", "043"), ("Migori", "044"),
    ("Kisii", "045"), ("Nyamira", "046"), ("Nairobi", "047"),
]

UNIVERSITIES = [
    # ── PUBLIC UNIVERSITIES ──────────────────────────────────────────────
    {"name": "University of Nairobi",                          "short": "UoN",     "type": UniversityType.PUBLIC,  "county": "Nairobi"},
    {"name": "Kenyatta University",                            "short": "KU",      "type": UniversityType.PUBLIC,  "county": "Kiambu"},
    {"name": "Jomo Kenyatta University of Agriculture and Technology", "short": "JKUAT", "type": UniversityType.PUBLIC, "county": "Kiambu"},
    {"name": "Moi University",                                 "short": "MU",      "type": UniversityType.PUBLIC,  "county": "Uasin Gishu"},
    {"name": "Egerton University",                             "short": "EU",      "type": UniversityType.PUBLIC,  "county": "Nakuru"},
    {"name": "Maseno University",                              "short": "Maseno",  "type": UniversityType.PUBLIC,  "county": "Kisumu"},
    {"name": "Masinde Muliro University of Science and Technology", "short": "MMUST", "type": UniversityType.PUBLIC, "county": "Kakamega"},
    {"name": "Dedan Kimathi University of Technology",         "short": "DeKUT",   "type": UniversityType.PUBLIC,  "county": "Nyeri"},
    {"name": "Technical University of Kenya",                  "short": "TUK",     "type": UniversityType.PUBLIC,  "county": "Nairobi"},
    {"name": "Technical University of Mombasa",                "short": "TUM",     "type": UniversityType.PUBLIC,  "county": "Mombasa"},
    {"name": "Multimedia University of Kenya",                 "short": "MMU",     "type": UniversityType.PUBLIC,  "county": "Nairobi"},
    {"name": "Cooperative University of Kenya",                "short": "CUK",     "type": UniversityType.PUBLIC,  "county": "Kiambu"},
    {"name": "Laikipia University",                            "short": "LU",      "type": UniversityType.PUBLIC,  "county": "Laikipia"},
    {"name": "Kisii University",                               "short": "KSU",     "type": UniversityType.PUBLIC,  "county": "Kisii"},
    {"name": "South Eastern Kenya University",                 "short": "SEKU",    "type": UniversityType.PUBLIC,  "county": "Kitui"},
    {"name": "Muranga University of Technology",               "short": "MUT",     "type": UniversityType.PUBLIC,  "county": "Murang'a"},
    {"name": "Chuka University",                               "short": "Chuka",   "type": UniversityType.PUBLIC,  "county": "Tharaka-Nithi"},
    {"name": "Machakos University",                            "short": "MKU",     "type": UniversityType.PUBLIC,  "county": "Machakos"},
    {"name": "Embu University",                                "short": "EmbuU",   "type": UniversityType.PUBLIC,  "county": "Embu"},
    {"name": "Kirinyaga University",                           "short": "KyU",     "type": UniversityType.PUBLIC,  "county": "Kirinyaga"},
    {"name": "Pwani University",                               "short": "PU",      "type": UniversityType.PUBLIC,  "county": "Kilifi"},
    {"name": "Rongo University",                               "short": "RU",      "type": UniversityType.PUBLIC,  "county": "Migori"},
    {"name": "Tharaka University",                             "short": "TharU",   "type": UniversityType.PUBLIC,  "county": "Tharaka-Nithi"},
    {"name": "University of Kabianga",                         "short": "UoK",     "type": UniversityType.PUBLIC,  "county": "Kericho"},
    {"name": "Jaramogi Oginga Odinga University of Science and Technology", "short": "JOOUST", "type": UniversityType.PUBLIC, "county": "Siaya"},
    {"name": "Tom Mboya University",                           "short": "TMU",     "type": UniversityType.PUBLIC,  "county": "Homa Bay"},
    {"name": "Alupe University",                               "short": "AUC",     "type": UniversityType.PUBLIC,  "county": "Busia"},
    {"name": "Kibabii University",                             "short": "KIBU",    "type": UniversityType.PUBLIC,  "county": "Bungoma"},
    {"name": "University of Eldoret",                          "short": "UoE",     "type": UniversityType.PUBLIC,  "county": "Uasin Gishu"},
    {"name": "Garissa University",                             "short": "GU",      "type": UniversityType.PUBLIC,  "county": "Garissa"},
    {"name": "Bomet University College",                       "short": "BUC",     "type": UniversityType.PUBLIC,  "county": "Bomet"},
    {"name": "Maasai Mara University",                         "short": "MMU2",    "type": UniversityType.PUBLIC,  "county": "Narok"},
    {"name": "Meru University of Science and Technology",      "short": "MUST",    "type": UniversityType.PUBLIC,  "county": "Meru"},
    {"name": "Taita Taveta University",                        "short": "TTU",     "type": UniversityType.PUBLIC,  "county": "Taita-Taveta"},
    {"name": "Karatina University",                            "short": "KarU",    "type": UniversityType.PUBLIC,  "county": "Nyeri"},
    {"name": "University of Makueni",                          "short": "UoM",     "type": UniversityType.PUBLIC,  "county": "Makueni"},
    {"name": "Turkana University College",                     "short": "TUC",     "type": UniversityType.PUBLIC,  "county": "Turkana"},
    # ── PRIVATE UNIVERSITIES ─────────────────────────────────────────────
    {"name": "Strathmore University",                          "short": "SU",      "type": UniversityType.PRIVATE, "county": "Nairobi"},
    {"name": "Daystar University",                             "short": "DU",      "type": UniversityType.PRIVATE, "county": "Nairobi"},
    {"name": "Mount Kenya University",                         "short": "MKU2",    "type": UniversityType.PRIVATE, "county": "Kirinyaga"},
    {"name": "KCA University",                                 "short": "KCAU",    "type": UniversityType.PRIVATE, "county": "Nairobi"},
    {"name": "United States International University Africa",  "short": "USIU",    "type": UniversityType.PRIVATE, "county": "Nairobi"},
    {"name": "Catholic University of Eastern Africa",          "short": "CUEA",    "type": UniversityType.PRIVATE, "county": "Nairobi"},
    {"name": "Zetech University",                              "short": "ZU",      "type": UniversityType.PRIVATE, "county": "Kiambu"},
    {"name": "Riara University",                               "short": "RU2",     "type": UniversityType.PRIVATE, "county": "Nairobi"},
    {"name": "Africa Nazarene University",                     "short": "ANU",     "type": UniversityType.PRIVATE, "county": "Kajiado"},
    {"name": "Scott Christian University",                     "short": "SCU",     "type": UniversityType.PRIVATE, "county": "Machakos"},
    {"name": "Pan Africa Christian University",                "short": "PAC",     "type": UniversityType.PRIVATE, "county": "Nairobi"},
    {"name": "Adventist University of Africa",                 "short": "AUA",     "type": UniversityType.PRIVATE, "county": "Kajiado"},
    {"name": "East Africa University",                         "short": "EAU",     "type": UniversityType.PRIVATE, "county": "Garissa"},
    {"name": "Kabarak University",                             "short": "KabU",    "type": UniversityType.PRIVATE, "county": "Nakuru"},
    {"name": "African International University",               "short": "AIU",     "type": UniversityType.PRIVATE, "county": "Nairobi"},
    {"name": "International Leadership University",            "short": "ILU",     "type": UniversityType.PRIVATE, "county": "Nairobi"},
    {"name": "Kenya Methodist University",                     "short": "KeMU",    "type": UniversityType.PRIVATE, "county": "Meru"},
    {"name": "Nkabune Technical Training Institute",           "short": "NTTI",    "type": UniversityType.PRIVATE, "county": "Meru"},
    {"name": "Management University of Africa",                "short": "MUA",     "type": UniversityType.PRIVATE, "county": "Nairobi"},
    {"name": "Nairobi Institute of Business Studies",          "short": "NIBS",    "type": UniversityType.PRIVATE, "county": "Nairobi"},
    {"name": "East African School of Aviation",                "short": "EASA",    "type": UniversityType.PRIVATE, "county": "Nairobi"},
    {"name": "Kenya Highlands Evangelical University",         "short": "KHEU",    "type": UniversityType.PRIVATE, "county": "Kericho"},
    # ── TVETs & COLLEGES ─────────────────────────────────────────────────
    {"name": "Kenya Medical Training College",                 "short": "KMTC",    "type": UniversityType.TVET,    "county": "Nairobi"},
    {"name": "Kenya Institute of Management",                  "short": "KIM",     "type": UniversityType.TVET,    "county": "Nairobi"},
    {"name": "Nairobi Technical Training Institute",           "short": "NTTI2",   "type": UniversityType.TVET,    "county": "Nairobi"},
    {"name": "Kenya School of Law",                            "short": "KSL",     "type": UniversityType.TVET,    "county": "Nairobi"},
    {"name": "Kenya National Examination Council",             "short": "KNEC",    "type": UniversityType.TVET,    "county": "Nairobi"},
    {"name": "Utalii College",                                 "short": "UC",      "type": UniversityType.TVET,    "county": "Nairobi"},
    {"name": "Kenya Wildlife Service Training Institute",      "short": "KWSTI",   "type": UniversityType.TVET,    "county": "Nakuru"},
    {"name": "Kenya Institute of Highways and Building Technology", "short": "KIHBT", "type": UniversityType.TVET, "county": "Nairobi"},
    {"name": "Kenya Water Institute",                          "short": "KEWI",    "type": UniversityType.TVET,    "county": "Nairobi"},
    {"name": "Kenya Red Cross Society College",                "short": "KRCS",    "type": UniversityType.TVET,    "county": "Nairobi"},
]


async def seed_universities(session: AsyncSession):
    """Seed counties and universities only if tables are empty."""
    existing = await session.execute(select(County).limit(1))
    if existing.scalars().first():
        return  # Already seeded

    # Insert counties
    county_map = {}
    for name, code in COUNTIES:
        county = County(name=name, code=code)
        session.add(county)
        county_map[name] = county

    await session.flush()

    # Reload counties to get IDs
    result = await session.execute(select(County))
    county_map = {c.name: c for c in result.scalars().all()}

    # Insert universities
    for data in UNIVERSITIES:
        county = county_map.get(data["county"])
        uni = University(
            name=data["name"],
            short_name=data["short"],
            type=data["type"],
            county_id=county.id if county else None,
        )
        session.add(uni)

    await session.commit()
