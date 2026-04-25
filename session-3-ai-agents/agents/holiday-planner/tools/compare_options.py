#!/usr/bin/env python3
"""
Option Comparison Tool

Compares multiple holiday options side-by-side with family fit analysis.
Generates comprehensive comparison reports.

Usage:
    python compare_options.py --trips trip1.json trip2.json trip3.json
    python compare_options.py --trip-ids "abc123,def456" --family-id "fam001"
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from memory.memory import get_trip, get_family


def compare_trips(
    trips: list,
    family_profile: dict = None,
    aspects: list = None
) -> dict:
    """
    Compare multiple trip options.
    
    Args:
        trips: List of trip data dictionaries
        family_profile: Family profile for fit analysis
        aspects: Specific aspects to compare (budget, activities, weather, etc.)
    """
    if not aspects:
        aspects = ["budget", "destinations", "activities", "weather", "family_fit"]
    
    comparison = {
        "trips_compared": len(trips),
        "trip_names": [t.get("name", f"Trip {i+1}") for i, t in enumerate(trips)],
        "aspects": {}
    }
    
    if "budget" in aspects:
        comparison["aspects"]["budget"] = compare_budgets(trips)
    
    if "destinations" in aspects:
        comparison["aspects"]["destinations"] = compare_destinations(trips)
    
    if "activities" in aspects:
        comparison["aspects"]["activities"] = compare_activities(trips)
    
    if "family_fit" in aspects and family_profile:
        comparison["aspects"]["family_fit"] = analyze_family_fit(trips, family_profile)
    
    comparison["summary"] = generate_comparison_summary(comparison, family_profile)
    comparison["recommendation"] = generate_recommendation(comparison, family_profile)
    
    return comparison


def compare_budgets(trips: list) -> dict:
    """Compare budget aspects of trips."""
    budget_data = []
    
    for trip in trips:
        budget = trip.get("budget", {})
        budget_data.append({
            "trip_name": trip.get("name", "Unknown"),
            "total": budget.get("total_estimated", 0),
            "per_person": budget.get("per_person", 0),
            "per_day": budget.get("per_day", 0),
            "breakdown": budget.get("breakdown", {})
        })
    
    if not budget_data:
        return {"error": "No budget data available"}
    
    totals = [b["total"] for b in budget_data if b["total"] > 0]
    
    return {
        "by_trip": budget_data,
        "cheapest": min(budget_data, key=lambda x: x["total"] or float('inf'))["trip_name"] if totals else None,
        "most_expensive": max(budget_data, key=lambda x: x["total"])["trip_name"] if totals else None,
        "price_range": {
            "min": min(totals) if totals else 0,
            "max": max(totals) if totals else 0,
            "difference_eur": (max(totals) - min(totals)) if totals else 0,
            "difference_percent": round((max(totals) - min(totals)) / min(totals) * 100, 1) if totals and min(totals) > 0 else 0
        }
    }


def compare_destinations(trips: list) -> dict:
    """Compare destinations across trips."""
    dest_data = []
    
    for trip in trips:
        destinations = trip.get("destinations", [])
        dest_info = {
            "trip_name": trip.get("name", "Unknown"),
            "destinations": [d.get("name", "Unknown") for d in destinations],
            "countries": list(set(d.get("country", "") for d in destinations)),
            "types": list(set(d.get("type", "") for d in destinations)),
            "total_days": sum(d.get("duration_days", 0) for d in destinations),
            "highlights": []
        }
        
        for d in destinations:
            dest_info["highlights"].extend(d.get("highlights", [])[:2])
        
        dest_data.append(dest_info)
    
    return {
        "by_trip": dest_data,
        "all_destinations": list(set(
            d for trip in dest_data for d in trip["destinations"]
        )),
        "all_countries": list(set(
            c for trip in dest_data for c in trip["countries"]
        ))
    }


def compare_activities(trips: list) -> dict:
    """Compare activities across trips."""
    activity_data = []
    
    for trip in trips:
        activities = []
        for dest in trip.get("destinations", []):
            activities.extend(dest.get("activities", []))
        
        activity_types = {}
        for act in activities:
            act_type = act.get("type", "other")
            activity_types[act_type] = activity_types.get(act_type, 0) + 1
        
        activity_data.append({
            "trip_name": trip.get("name", "Unknown"),
            "total_activities": len(activities),
            "activity_types": activity_types,
            "highlights": [a.get("name") for a in activities[:5]]
        })
    
    return {
        "by_trip": activity_data,
        "most_activities": max(activity_data, key=lambda x: x["total_activities"])["trip_name"] if activity_data else None
    }


def analyze_family_fit(trips: list, family_profile: dict) -> dict:
    """Analyze how well each trip fits the family's needs."""
    members = family_profile.get("members", [])
    constraints = family_profile.get("constraints", {})
    shared_prefs = family_profile.get("shared_preferences", {})
    
    fit_scores = []
    
    for trip in trips:
        score_details = {
            "trip_name": trip.get("name", "Unknown"),
            "overall_score": 0,
            "member_scores": {},
            "constraint_matches": {},
            "strengths": [],
            "concerns": []
        }
        
        total_score = 0
        score_count = 0
        
        for member in members:
            member_name = member.get("name", member.get("role", "member"))
            member_score = calculate_member_fit(trip, member)
            score_details["member_scores"][member_name] = member_score
            total_score += member_score
            score_count += 1
        
        budget = trip.get("budget", {})
        budget_max = constraints.get("budget", {}).get("max")
        if budget_max and budget.get("total_estimated"):
            if budget["total_estimated"] <= budget_max:
                score_details["constraint_matches"]["budget"] = "within_budget"
                score_details["strengths"].append("Within budget")
                total_score += 20
            else:
                over = budget["total_estimated"] - budget_max
                score_details["constraint_matches"]["budget"] = f"over_by_{over}"
                score_details["concerns"].append(f"Over budget by €{over}")
                total_score -= 10
            score_count += 1
        
        duration = constraints.get("duration", {})
        trip_days = trip.get("travel_dates", {}).get("duration_days", 0)
        if duration.get("preferred_days") and trip_days:
            diff = abs(trip_days - duration["preferred_days"])
            if diff <= 1:
                score_details["strengths"].append("Perfect duration")
                total_score += 10
            elif diff > 3:
                score_details["concerns"].append(f"Duration differs by {diff} days")
                total_score -= 5
            score_count += 1
        
        if score_count > 0:
            score_details["overall_score"] = round(total_score / score_count, 1)
        
        fit_scores.append(score_details)
    
    best_fit = max(fit_scores, key=lambda x: x["overall_score"]) if fit_scores else None
    
    return {
        "by_trip": fit_scores,
        "best_fit": best_fit["trip_name"] if best_fit else None,
        "best_fit_score": best_fit["overall_score"] if best_fit else 0
    }


def calculate_member_fit(trip: dict, member: dict) -> float:
    """Calculate how well a trip fits a specific family member."""
    score = 50
    
    prefs = member.get("preferences", {})
    liked_activities = set(prefs.get("activity_types", []))
    
    trip_activities = set()
    for dest in trip.get("destinations", []):
        for act in dest.get("activities", []):
            trip_activities.add(act.get("type", "").lower())
    
    matching = liked_activities & trip_activities
    if matching:
        score += len(matching) * 10
    
    must_haves = set(prefs.get("must_haves", []))
    trip_highlights = set()
    for dest in trip.get("destinations", []):
        trip_highlights.update(h.lower() for h in dest.get("highlights", []))
    
    must_have_matches = sum(1 for mh in must_haves if any(mh.lower() in h for h in trip_highlights))
    score += must_have_matches * 15
    
    deal_breakers = prefs.get("deal_breakers", [])
    for db in deal_breakers:
        if any(db.lower() in str(dest).lower() for dest in trip.get("destinations", [])):
            score -= 30
    
    return min(max(score, 0), 100)


def generate_comparison_summary(comparison: dict, family_profile: dict = None) -> dict:
    """Generate a summary of the comparison."""
    summary = {
        "trips_analyzed": comparison["trips_compared"],
        "key_differences": [],
        "trade_offs": []
    }
    
    budget_aspect = comparison["aspects"].get("budget", {})
    if budget_aspect.get("price_range", {}).get("difference_percent", 0) > 20:
        summary["key_differences"].append(
            f"Significant price difference: {budget_aspect['price_range']['difference_percent']}%"
        )
        summary["trade_offs"].append({
            "cheaper": budget_aspect.get("cheapest"),
            "expensive": budget_aspect.get("most_expensive"),
            "difference": budget_aspect["price_range"]["difference_eur"]
        })
    
    return summary


def generate_recommendation(comparison: dict, family_profile: dict = None) -> dict:
    """Generate a recommendation based on comparison."""
    recommendation = {
        "top_choice": None,
        "reasons": [],
        "caveats": []
    }
    
    fit_data = comparison["aspects"].get("family_fit", {})
    if fit_data.get("best_fit"):
        recommendation["top_choice"] = fit_data["best_fit"]
        recommendation["reasons"].append(f"Best overall family fit score: {fit_data['best_fit_score']}")
        
        for trip_fit in fit_data.get("by_trip", []):
            if trip_fit["trip_name"] == fit_data["best_fit"]:
                recommendation["reasons"].extend(trip_fit.get("strengths", []))
                recommendation["caveats"].extend(trip_fit.get("concerns", []))
    
    budget_data = comparison["aspects"].get("budget", {})
    if budget_data.get("cheapest") and budget_data["cheapest"] != recommendation.get("top_choice"):
        recommendation["caveats"].append(
            f"Note: {budget_data['cheapest']} is the most budget-friendly option"
        )
    
    return recommendation


def main():
    parser = argparse.ArgumentParser(description="Compare holiday options")
    parser.add_argument("--trips", nargs="+", help="Trip JSON files to compare")
    parser.add_argument("--trip-ids", help="Comma-separated trip IDs from database")
    parser.add_argument("--family-id", help="Family ID for fit analysis")
    parser.add_argument("--aspects", nargs="+", help="Aspects to compare")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    
    args = parser.parse_args()
    
    trips = []
    
    if args.trips:
        for trip_file in args.trips:
            with open(trip_file) as f:
                trips.append(json.load(f))
    
    if args.trip_ids:
        for trip_id in args.trip_ids.split(","):
            trip = get_trip(trip_id.strip())
            if trip:
                trips.append(trip)
    
    if not trips:
        print(json.dumps({"error": "No trips to compare"}))
        sys.exit(1)
    
    family_profile = None
    if args.family_id:
        family_profile = get_family(args.family_id)
    
    result = compare_trips(trips, family_profile, args.aspects)
    
    if args.format == "markdown":
        print(format_as_markdown(result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


def format_as_markdown(comparison: dict) -> str:
    """Format comparison as markdown."""
    lines = ["# Holiday Options Comparison\n"]
    
    lines.append(f"Comparing {comparison['trips_compared']} options: {', '.join(comparison['trip_names'])}\n")
    
    if "budget" in comparison["aspects"]:
        lines.append("## Budget Comparison\n")
        budget = comparison["aspects"]["budget"]
        lines.append("| Trip | Total | Per Person | Per Day |")
        lines.append("|------|-------|------------|---------|")
        for t in budget.get("by_trip", []):
            lines.append(f"| {t['trip_name']} | €{t['total']} | €{t['per_person']} | €{t['per_day']} |")
        lines.append("")
    
    if "family_fit" in comparison["aspects"]:
        lines.append("## Family Fit Analysis\n")
        fit = comparison["aspects"]["family_fit"]
        for t in fit.get("by_trip", []):
            lines.append(f"### {t['trip_name']} (Score: {t['overall_score']})")
            if t.get("strengths"):
                lines.append(f"**Strengths:** {', '.join(t['strengths'])}")
            if t.get("concerns"):
                lines.append(f"**Concerns:** {', '.join(t['concerns'])}")
            lines.append("")
    
    rec = comparison.get("recommendation", {})
    if rec.get("top_choice"):
        lines.append("## Recommendation\n")
        lines.append(f"**Top Choice: {rec['top_choice']}**\n")
        for reason in rec.get("reasons", []):
            lines.append(f"- {reason}")
        lines.append("")
    
    return "\n".join(lines)


if __name__ == "__main__":
    main()
