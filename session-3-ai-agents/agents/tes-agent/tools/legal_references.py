#!/usr/bin/env python3
"""
Legal Cross-References Module

Maps TES terms to Finnish labor law (Työsopimuslaki, Työaikalaki, Vuosilomalaki, etc.)
Provides context for understanding how TES provisions relate to statutory minimums.
"""

import json
from typing import Dict, List, Optional

# Finnish Labor Laws with key sections
LABOR_LAWS = {
    "TSL": {
        "name": "Työsopimuslaki",
        "name_en": "Employment Contracts Act",
        "number": "55/2001",
        "url": "https://www.finlex.fi/fi/laki/ajantasa/2001/20010055",
        "sections": {
            "1:1": {"title": "Soveltamisala", "topic": "scope", "summary": "Lakia sovelletaan työsopimukseen"},
            "1:3": {"title": "Työsopimuksen muoto ja kesto", "topic": "contract_form", "summary": "Työsopimus voidaan tehdä suullisesti, kirjallisesti tai sähköisesti"},
            "1:4": {"title": "Koeaika", "topic": "trial_period", "summary": "Koeaika enintään 6 kuukautta"},
            "2:1": {"title": "Yleisvelvoite", "topic": "employer_obligations", "summary": "Työnantajan on edistettävä työntekijöidensä mahdollisuuksia kehittyä"},
            "2:2": {"title": "Syrjintäkielto ja tasapuolinen kohtelu", "topic": "discrimination", "summary": "Syrjintä on kielletty"},
            "2:10": {"title": "Sairausajan palkka", "topic": "sick_leave", "summary": "Työntekijällä oikeus sairastumispäivää seuranneen 9 arkipäivän palkkaan"},
            "2:11": {"title": "Palkanmaksu poissaolon ajalta", "topic": "leave_pay", "summary": "Lyhytaikainen poissaolo pakottavasta perhesyystä"},
            "4:1": {"title": "Perhevapaat", "topic": "family_leave", "summary": "Oikeus raskaus-, erityisraskaus- ja vanhempainvapaaseen"},
            "4:6": {"title": "Tilapäinen hoitovapaa", "topic": "child_sick_leave", "summary": "Alle 10-vuotiaan lapsen hoito, enintään 4 työpäivää kerrallaan"},
            "6:1": {"title": "Irtisanomisperusteet", "topic": "termination_grounds", "summary": "Asiallinen ja painava syy"},
            "6:2": {"title": "Taloudelliset ja tuotannolliset irtisanomisperusteet", "topic": "collective_dismissal", "summary": "Työn vähentyminen olennaisesti ja pysyvästi"},
            "6:3": {"title": "Irtisanomisajat", "topic": "notice_periods", "summary": "Irtisanomisaika työsuhteen keston mukaan"},
            "6:6": {"title": "Takaisinottovelvollisuus", "topic": "re_employment", "summary": "9 kuukauden takaisinottovelvollisuus"},
            "7:2": {"title": "Työsopimuksen purkaminen", "topic": "termination_immediate", "summary": "Erittäin painava syy"},
            "8:1": {"title": "Purkamisoikeus koeaikana", "topic": "trial_termination", "summary": "Koeaikana voidaan purkaa molemmin puolin"},
            "13:6": {"title": "Työehtosopimuksen yleissitovuus", "topic": "tes_binding", "summary": "Yleissitovan TES:n noudattamisvelvollisuus"}
        }
    },
    "TAL": {
        "name": "Työaikalaki",
        "name_en": "Working Hours Act",
        "number": "872/2019",
        "url": "https://www.finlex.fi/fi/laki/ajantasa/2019/20190872",
        "sections": {
            "3": {"title": "Säännöllinen työaika", "topic": "working_hours", "summary": "Enintään 8 tuntia päivässä ja 40 tuntia viikossa"},
            "4": {"title": "Vuorokautisen säännöllisen työajan pidentäminen", "topic": "extended_hours", "summary": "Säännöllinen työaika voidaan sopia pidemmäksi"},
            "5": {"title": "Keskimääräinen säännöllinen työaika", "topic": "average_hours", "summary": "Työaika voidaan järjestää keskimääräisenä"},
            "8": {"title": "Liukuva työaika", "topic": "flexible_hours", "summary": "Työntekijä voi sovituissa rajoissa määrätä päivittäisen työaikansa"},
            "14": {"title": "Työaikapankki", "topic": "time_bank", "summary": "Työaikaa voidaan säästää ja käyttää myöhemmin"},
            "16": {"title": "Lisätyö", "topic": "additional_hours", "summary": "Säännöllisen työajan lisäksi tehtävä työ"},
            "17": {"title": "Ylityö", "topic": "overtime", "summary": "Säännöllisen ja lisätyöajan ylittävä työ"},
            "18": {"title": "Ylityökorvaus", "topic": "overtime_compensation", "summary": "Vuorokautisen ylityön 2 ensimmäistä tuntia +50%, seuraavat +100%"},
            "20": {"title": "Sunnuntaityö", "topic": "sunday_work", "summary": "Sunnuntaina tai kirkollisena juhlapyhänä tehdystä työstä 100% korvaus"},
            "24": {"title": "Lepoajat", "topic": "breaks", "summary": "Yli 6 tunnin työpäivänä vähintään puolen tunnin lepo"},
            "25": {"title": "Vuorokausilepo", "topic": "daily_rest", "summary": "Vähintään 11 tunnin keskeytymätön lepoaika"},
            "27": {"title": "Viikkolepo", "topic": "weekly_rest", "summary": "Kerran viikossa vähintään 35 tunnin keskeytymätön lepoaika"},
            "30": {"title": "Yötyö", "topic": "night_work", "summary": "Kello 23-6 välisenä aikana tehtävä työ"}
        }
    },
    "VLL": {
        "name": "Vuosilomalaki",
        "name_en": "Annual Holidays Act",
        "number": "162/2005",
        "url": "https://www.finlex.fi/fi/laki/ajantasa/2005/20050162",
        "sections": {
            "5": {"title": "Vuosiloman pituus", "topic": "vacation_days", "summary": "2 tai 2,5 arkipäivää/lomanmääräytymiskuukausi"},
            "6": {"title": "Täysi lomanmääräytymiskuukausi", "topic": "vacation_accrual", "summary": "Kuukausi, jona tehty työtä vähintään 14 päivää tai 35 tuntia"},
            "9": {"title": "Vuosilomapalkka", "topic": "vacation_pay", "summary": "Lomapalkka vastaa työaikana maksettavaa palkkaa"},
            "12": {"title": "Lomakorvaus", "topic": "vacation_compensation", "summary": "Korvaus pitämättömästä lomasta työsuhteen päättyessä"},
            "20": {"title": "Vuosiloman antaminen", "topic": "vacation_scheduling", "summary": "Kesäloma 2.5.-30.9., talviloma muuna aikana"}
        }
    },
    "YTL": {
        "name": "Yhteistoimintalaki",
        "name_en": "Act on Co-operation within Undertakings",
        "number": "1333/2021",
        "url": "https://www.finlex.fi/fi/laki/ajantasa/2021/20211333",
        "sections": {
            "16": {"title": "Jatkuva vuoropuhelu", "topic": "cooperation", "summary": "Henkilöstön edustajan kanssa käytävä säännöllinen vuoropuhelu"},
            "19": {"title": "Muutosneuvottelut", "topic": "change_negotiations", "summary": "Neuvottelut ennen työvoiman vähentämistä"}
        }
    }
}

# Topic to law section mappings
TOPIC_TO_LAW = {
    "trial_period": [("TSL", "1:4"), ("TSL", "8:1")],
    "sick_leave": [("TSL", "2:10")],
    "family_leave": [("TSL", "4:1")],
    "child_sick_leave": [("TSL", "4:6")],
    "notice_periods": [("TSL", "6:3")],
    "termination": [("TSL", "6:1"), ("TSL", "6:2"), ("TSL", "7:2")],
    "re_employment": [("TSL", "6:6")],
    "working_hours": [("TAL", "3"), ("TAL", "4"), ("TAL", "5")],
    "flexible_hours": [("TAL", "8")],
    "working_time_bank": [("TAL", "14")],
    "overtime": [("TAL", "16"), ("TAL", "17"), ("TAL", "18")],
    "sunday_work": [("TAL", "20")],
    "weekend_and_holiday_work": [("TAL", "20")],
    "breaks": [("TAL", "24")],
    "rest_periods": [("TAL", "25"), ("TAL", "27")],
    "night_work": [("TAL", "30")],
    "shift_work": [("TAL", "30")],
    "vacation": [("VLL", "5"), ("VLL", "6"), ("VLL", "9"), ("VLL", "20")],
    "vacation_pay": [("VLL", "9"), ("VLL", "12")],
    "collective_dismissal": [("TSL", "6:2"), ("YTL", "19")],
    "cooperation": [("YTL", "16"), ("YTL", "19")],
    "tes_binding": [("TSL", "13:6")]
}


def get_legal_references(topic: str) -> List[Dict]:
    """Get legal references for a TES topic."""
    refs = []
    mappings = TOPIC_TO_LAW.get(topic, [])
    
    for law_code, section in mappings:
        law = LABOR_LAWS.get(law_code, {})
        section_info = law.get("sections", {}).get(section, {})
        
        if section_info:
            refs.append({
                "law": law.get("name"),
                "law_en": law.get("name_en"),
                "law_number": law.get("number"),
                "section": section,
                "title": section_info.get("title"),
                "summary": section_info.get("summary"),
                "url": f"{law.get('url')}#L{section.replace(':', 'P')}" if law.get("url") else None
            })
    
    return refs


def get_all_references_for_tes(tes_data: dict) -> Dict[str, List[Dict]]:
    """Get all legal references relevant to a TES document."""
    references = {}
    
    # Map TES fields to topics
    field_to_topic = {
        "trial_period": "trial_period",
        "sick_leave": "sick_leave",
        "child_sick_leave": "child_sick_leave",
        "family_leave": "family_leave",
        "notice_periods": "notice_periods",
        "termination": "termination",
        "working_hours": "working_hours",
        "overtime": "overtime",
        "breaks": "breaks",
        "shift_work": "shift_work",
        "weekend_and_holiday_work": "weekend_and_holiday_work",
        "vacation": "vacation",
        "union_rights": "cooperation"
    }
    
    for field, topic in field_to_topic.items():
        if tes_data.get(field):
            refs = get_legal_references(topic)
            if refs:
                references[field] = refs
    
    return references


def compare_to_statutory_minimum(tes_data: dict) -> Dict[str, Dict]:
    """Compare TES provisions to statutory minimums."""
    comparisons = {}
    
    # Trial period
    if tes_data.get("trial_period"):
        tes_trial = tes_data["trial_period"]
        comparisons["trial_period"] = {
            "statutory_max": "6 months (TSL 1:4)",
            "tes_provision": tes_trial.get("max_duration", "Not specified"),
            "compliant": True,  # TES can't exceed statutory max
            "note": "TES may specify shorter trial period"
        }
    
    # Sick leave
    if tes_data.get("sick_leave"):
        comparisons["sick_leave"] = {
            "statutory_min": "Sairastumispäivä + 9 arkipäivää (TSL 2:10)",
            "tes_provision": tes_data["sick_leave"].get("paid_days_standard", "Not specified"),
            "note": "TES typically provides more generous sick pay than statutory minimum"
        }
    
    # Notice periods
    if tes_data.get("notice_periods"):
        comparisons["notice_periods"] = {
            "statutory": {
                "employee": ["14 days (0-5 years)", "1 month (5+ years)"],
                "employer": ["14 days (0-1 year)", "1 month (1-4 years)", "2 months (4-8 years)", "4 months (8-12 years)", "6 months (12+ years)"]
            },
            "tes_provision": tes_data["notice_periods"],
            "note": "TES notice periods must be at least statutory minimum"
        }
    
    # Working hours
    if tes_data.get("working_hours"):
        wh = tes_data["working_hours"]
        comparisons["working_hours"] = {
            "statutory_max": "8 hours/day, 40 hours/week (TAL 3§)",
            "tes_provision": f"{wh.get('daily_hours', '?')} hours/day, {wh.get('weekly_hours', '?')} hours/week",
            "note": "TES often specifies 37.5h/week, which is below statutory max"
        }
    
    # Vacation
    if tes_data.get("vacation"):
        vac = tes_data["vacation"]
        comparisons["vacation"] = {
            "statutory_min": "2 days/month (first year), 2.5 days/month (after 1 year) = 24-30 days (VLL 5§)",
            "tes_provision": f"{vac.get('days_first_year', '?')} days first year, {vac.get('days_standard', '?')} standard, {vac.get('days_senior', '?')} senior",
            "note": "TES may provide additional vacation days beyond statutory"
        }
    
    return comparisons


def format_legal_reference(ref: Dict, format_type: str = "text") -> str:
    """Format a legal reference for display."""
    if format_type == "markdown":
        return f"**{ref['law']}** {ref['section']} - {ref['title']}: {ref['summary']} [Finlex]({ref.get('url', '')})"
    elif format_type == "html":
        url = ref.get('url', '#')
        return f'<strong>{ref["law"]}</strong> {ref["section"]} - {ref["title"]}: {ref["summary"]} <a href="{url}" target="_blank">Finlex</a>'
    else:
        return f"{ref['law']} {ref['section']} - {ref['title']}: {ref['summary']}"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Legal References Tool")
    parser.add_argument("--topic", help="Get references for a topic (e.g., sick_leave, overtime)")
    parser.add_argument("--tes", help="TES JSON file to analyze")
    parser.add_argument("--list-topics", action="store_true", help="List available topics")
    
    args = parser.parse_args()
    
    if args.list_topics:
        print("Available topics:")
        for topic in sorted(TOPIC_TO_LAW.keys()):
            refs = get_legal_references(topic)
            laws = ", ".join(set(r["law"] for r in refs))
            print(f"  {topic}: {laws}")
    
    elif args.topic:
        refs = get_legal_references(args.topic)
        print(json.dumps(refs, ensure_ascii=False, indent=2))
    
    elif args.tes:
        with open(args.tes) as f:
            tes_data = json.load(f)
        
        refs = get_all_references_for_tes(tes_data)
        comparisons = compare_to_statutory_minimum(tes_data)
        
        print(json.dumps({
            "legal_references": refs,
            "statutory_comparisons": comparisons
        }, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()
