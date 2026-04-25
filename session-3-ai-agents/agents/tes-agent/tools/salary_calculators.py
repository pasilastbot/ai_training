#!/usr/bin/env python3
"""
Comprehensive Salary Calculators for TES Agent

Provides all salary calculation features:
- Total Compensation Calculator
- Shift Work Calculator  
- Overtime Calculator
- Salary Comparison
- Experience Progression
- Vacation Pay Calculator
- Part-time Pro-rata Calculator
- Annual Cost Calculator for Employers
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import sqlite3

# Memory path for database
MEMORY_PATH = Path(__file__).parent.parent / "memory"
DB_PATH = MEMORY_PATH / "data" / "tes.db"


def get_db_connection():
    """Get SQLite database connection."""
    return sqlite3.connect(str(DB_PATH))


def round_currency(value: float) -> float:
    """Round to 2 decimal places for currency."""
    return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def get_tes_data(tes_name_or_id: str) -> Optional[Dict]:
    """Get TES data from database by name or ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Try by name first
    cursor.execute("SELECT data_json FROM tes_documents WHERE name = ?", (tes_name_or_id,))
    row = cursor.fetchone()
    
    # If not found, try by ID
    if not row:
        cursor.execute("SELECT data_json FROM tes_documents WHERE id = ?", (tes_name_or_id,))
        row = cursor.fetchone()
    
    conn.close()
    
    if row and row[0]:
        return json.loads(row[0])
    return None


def get_salary_from_tes(tes_data: dict, job_group: str = None, experience_years: int = 0) -> Optional[float]:
    """Extract monthly salary from TES salary tables."""
    salary_tables = tes_data.get("salary_tables", [])
    if not salary_tables:
        return None
    
    # Find matching table by job group
    table = salary_tables[0]
    if job_group:
        for t in salary_tables:
            if job_group.lower() in t.get("table_name", "").lower() or \
               job_group.lower() in t.get("role_category", "").lower():
                table = t
                break
    
    # Try different level structures (levels or experience_levels)
    levels = table.get("levels", []) or table.get("experience_levels", [])
    
    if not levels:
        return None
    
    # Helper to extract salary from a level
    def extract_salary(level):
        return (level.get("monthly_salary") or 
                level.get("minimum_salary") or 
                (level.get("hourly_rate", 0) * 160))
    
    # Find matching level by job group name
    for level in levels:
        level_name = level.get("name", "") or level.get("level", "")
        if job_group and job_group.lower() in level_name.lower():
            return extract_salary(level)
    
    # Find by experience years - parse level names like "3-5 vuotta"
    def parse_experience_range(level_str):
        import re
        # Match patterns like "Alle 1 vuosi", "1-2 vuotta", "3-5 vuotta", "yli 5 vuotta"
        if "alle" in level_str.lower():
            return (0, 1)
        if "yli" in level_str.lower():
            nums = re.findall(r'\d+', level_str)
            return (int(nums[0]) if nums else 0, 99)
        nums = re.findall(r'\d+', level_str)
        if len(nums) >= 2:
            return (int(nums[0]), int(nums[1]))
        elif len(nums) == 1:
            return (int(nums[0]), int(nums[0]))
        return None
    
    # Try to find level matching experience
    best_match = None
    best_match_salary = None
    
    for level in levels:
        level_name = level.get("name", "") or level.get("level", "")
        exp_range = parse_experience_range(level_name)
        exp_years_field = level.get("experience_years")
        
        if exp_years_field is not None:
            if experience_years >= exp_years_field:
                best_match = level
                best_match_salary = extract_salary(level)
        elif exp_range:
            min_exp, max_exp = exp_range
            if min_exp <= experience_years <= max_exp:
                return extract_salary(level)
            elif experience_years >= min_exp:
                best_match = level
                best_match_salary = extract_salary(level)
    
    if best_match_salary:
        return best_match_salary
    
    # Return first level salary as fallback
    return extract_salary(levels[0])


# =============================================================================
# TOTAL COMPENSATION CALCULATOR
# =============================================================================

def calculate_total_compensation(
    base_salary: float,
    tes_data: dict,
    shift_work: dict = None,
    overtime_hours: dict = None,
    include_vacation_bonus: bool = True
) -> Dict:
    """
    Calculate total monthly/annual compensation including all components.
    
    Args:
        base_salary: Monthly base salary
        tes_data: TES document data
        shift_work: Dict with evening_hours, night_hours, saturday_hours, sunday_hours
        overtime_hours: Dict with daily_overtime, weekly_overtime
        include_vacation_bonus: Whether to include vacation bonus in annual
    
    Returns:
        Detailed compensation breakdown
    """
    result = {
        "base_salary_monthly": base_salary,
        "base_salary_annual": base_salary * 12,
        "components": {},
        "monthly_total": base_salary,
        "annual_total": base_salary * 12
    }
    
    hourly_rate = base_salary / 160  # Assuming 160 hours/month
    
    # Calculate shift work compensation
    if shift_work:
        shift_comp = calculate_shift_work(
            hourly_rate=hourly_rate,
            tes_data=tes_data,
            **shift_work
        )
        result["components"]["shift_work"] = shift_comp
        result["monthly_total"] += shift_comp.get("total_shift_compensation", 0)
    
    # Calculate overtime
    if overtime_hours:
        overtime_comp = calculate_overtime(
            hourly_rate=hourly_rate,
            tes_data=tes_data,
            **overtime_hours
        )
        result["components"]["overtime"] = overtime_comp
        result["monthly_total"] += overtime_comp.get("total_overtime_compensation", 0)
    
    # Fixed allowances from TES
    allowances = tes_data.get("allowances", {})
    if allowances:
        monthly_allowances = 0
        allowance_details = {}
        
        for key, value in allowances.items():
            if isinstance(value, dict):
                amount = value.get("amount", 0)
                period = value.get("period", "month")
                if period == "day":
                    amount *= 21  # Working days per month
                elif period == "hour":
                    amount *= 160
            else:
                amount = value if isinstance(value, (int, float)) else 0
            
            if amount > 0:
                allowance_details[key] = round_currency(amount)
                monthly_allowances += amount
        
        if allowance_details:
            result["components"]["allowances"] = allowance_details
            result["monthly_total"] += monthly_allowances
    
    # Vacation bonus
    if include_vacation_bonus:
        vacation = tes_data.get("vacation", {})
        vacation_bonus = vacation.get("vacation_bonus", "")
        
        if "50%" in str(vacation_bonus):
            vacation_bonus_amount = base_salary * 0.5
        elif vacation_bonus and isinstance(vacation_bonus, (int, float)):
            vacation_bonus_amount = float(vacation_bonus)
        else:
            vacation_bonus_amount = 0
        
        if vacation_bonus_amount > 0:
            result["components"]["vacation_bonus"] = round_currency(vacation_bonus_amount)
    
    # Calculate annual total
    monthly_additions = result["monthly_total"] - base_salary
    result["annual_total"] = (result["monthly_total"] * 12) + result["components"].get("vacation_bonus", 0)
    
    # Round all values
    result["monthly_total"] = round_currency(result["monthly_total"])
    result["annual_total"] = round_currency(result["annual_total"])
    
    return result


# =============================================================================
# SHIFT WORK CALCULATOR
# =============================================================================

def calculate_shift_work(
    hourly_rate: float,
    tes_data: dict,
    evening_hours: int = 0,
    night_hours: int = 0,
    saturday_hours: int = 0,
    sunday_hours: int = 0,
    holiday_hours: int = 0
) -> Dict:
    """
    Calculate shift work compensation.
    
    Args:
        hourly_rate: Base hourly rate
        tes_data: TES document data
        evening_hours: Hours worked during evening shift
        night_hours: Hours worked during night shift
        saturday_hours: Hours on Saturday
        sunday_hours: Hours on Sunday
        holiday_hours: Hours on public holidays
    
    Returns:
        Shift work compensation breakdown
    """
    shift_work = tes_data.get("shift_work", {})
    weekend = tes_data.get("weekend_and_holiday_work", {})
    
    result = {
        "base_hourly_rate": round_currency(hourly_rate),
        "hours_breakdown": {},
        "compensation_breakdown": {},
        "total_shift_compensation": 0
    }
    
    # Evening compensation
    if evening_hours > 0:
        evening_comp = shift_work.get("evening_compensation", "")
        if "€/h" in str(evening_comp):
            try:
                evening_rate = float(str(evening_comp).replace("€/h", "").replace(",", ".").strip())
            except:
                evening_rate = 1.50  # Default
        elif isinstance(evening_comp, (int, float)):
            evening_rate = float(evening_comp)
        else:
            evening_rate = 1.50  # Default evening premium
        
        evening_total = evening_hours * evening_rate
        result["hours_breakdown"]["evening_hours"] = evening_hours
        result["compensation_breakdown"]["evening"] = {
            "rate": evening_rate,
            "hours": evening_hours,
            "total": round_currency(evening_total)
        }
        result["total_shift_compensation"] += evening_total
    
    # Night compensation
    if night_hours > 0:
        night_comp = shift_work.get("night_compensation", "")
        if "€/h" in str(night_comp):
            try:
                night_rate = float(str(night_comp).replace("€/h", "").replace(",", ".").strip())
            except:
                night_rate = 3.00  # Default
        elif isinstance(night_comp, (int, float)):
            night_rate = float(night_comp)
        else:
            night_rate = 3.00  # Default night premium
        
        night_total = night_hours * night_rate
        result["hours_breakdown"]["night_hours"] = night_hours
        result["compensation_breakdown"]["night"] = {
            "rate": night_rate,
            "hours": night_hours,
            "total": round_currency(night_total)
        }
        result["total_shift_compensation"] += night_total
    
    # Saturday compensation
    if saturday_hours > 0:
        sat_comp = weekend.get("saturday_compensation", "")
        if "%" in str(sat_comp):
            try:
                sat_percent = float(str(sat_comp).replace("%", "").strip()) / 100
            except:
                sat_percent = 0.25  # Default 25%
        else:
            sat_percent = 0.25
        
        sat_rate = hourly_rate * sat_percent
        sat_total = saturday_hours * sat_rate
        result["hours_breakdown"]["saturday_hours"] = saturday_hours
        result["compensation_breakdown"]["saturday"] = {
            "rate": round_currency(sat_rate),
            "hours": saturday_hours,
            "total": round_currency(sat_total)
        }
        result["total_shift_compensation"] += sat_total
    
    # Sunday compensation (typically 100% extra)
    if sunday_hours > 0:
        sun_comp = weekend.get("sunday_compensation", "100%")
        if "%" in str(sun_comp):
            try:
                sun_percent = float(str(sun_comp).replace("%", "").strip()) / 100
            except:
                sun_percent = 1.0  # Default 100%
        else:
            sun_percent = 1.0
        
        sun_rate = hourly_rate * sun_percent
        sun_total = sunday_hours * sun_rate
        result["hours_breakdown"]["sunday_hours"] = sunday_hours
        result["compensation_breakdown"]["sunday"] = {
            "rate": round_currency(sun_rate),
            "hours": sunday_hours,
            "total": round_currency(sun_total)
        }
        result["total_shift_compensation"] += sun_total
    
    # Holiday compensation (typically 100% extra on top of sunday)
    if holiday_hours > 0:
        hol_comp = weekend.get("holiday_compensation", "100%")
        if "%" in str(hol_comp):
            try:
                hol_percent = float(str(hol_comp).replace("%", "").strip()) / 100
            except:
                hol_percent = 1.0
        else:
            hol_percent = 1.0
        
        hol_rate = hourly_rate * hol_percent
        hol_total = holiday_hours * hol_rate
        result["hours_breakdown"]["holiday_hours"] = holiday_hours
        result["compensation_breakdown"]["holiday"] = {
            "rate": round_currency(hol_rate),
            "hours": holiday_hours,
            "total": round_currency(hol_total)
        }
        result["total_shift_compensation"] += hol_total
    
    result["total_shift_compensation"] = round_currency(result["total_shift_compensation"])
    
    return result


# =============================================================================
# OVERTIME CALCULATOR
# =============================================================================

def calculate_overtime(
    hourly_rate: float,
    tes_data: dict,
    daily_overtime_hours: float = 0,
    weekly_overtime_hours: float = 0
) -> Dict:
    """
    Calculate overtime compensation based on TES rules.
    
    Args:
        hourly_rate: Base hourly rate
        tes_data: TES document data
        daily_overtime_hours: Daily overtime hours
        weekly_overtime_hours: Weekly overtime hours
    
    Returns:
        Overtime compensation breakdown
    """
    overtime = tes_data.get("overtime", {})
    
    # Default rates per Finnish law (TAL 18§)
    daily_first_rate = float(overtime.get("daily_first_hours", 50)) / 100  # First 2 hours
    daily_additional_rate = float(overtime.get("daily_additional", 100)) / 100  # After 2 hours
    weekly_first_rate = float(overtime.get("weekly_first_hours", 50)) / 100  # First 8 hours
    weekly_additional_rate = float(overtime.get("weekly_additional", 100)) / 100  # After 8 hours
    
    result = {
        "base_hourly_rate": round_currency(hourly_rate),
        "overtime_rates": {
            "daily_first_2h": f"{int(daily_first_rate * 100)}%",
            "daily_after_2h": f"{int(daily_additional_rate * 100)}%",
            "weekly_first_8h": f"{int(weekly_first_rate * 100)}%",
            "weekly_after_8h": f"{int(weekly_additional_rate * 100)}%"
        },
        "breakdown": {},
        "total_overtime_compensation": 0
    }
    
    # Daily overtime
    if daily_overtime_hours > 0:
        daily_first = min(daily_overtime_hours, 2)
        daily_additional = max(0, daily_overtime_hours - 2)
        
        daily_first_comp = daily_first * hourly_rate * (1 + daily_first_rate)
        daily_additional_comp = daily_additional * hourly_rate * (1 + daily_additional_rate)
        
        result["breakdown"]["daily_overtime"] = {
            "hours_at_50%": daily_first,
            "hours_at_100%": daily_additional,
            "compensation_50%": round_currency(daily_first_comp),
            "compensation_100%": round_currency(daily_additional_comp),
            "total": round_currency(daily_first_comp + daily_additional_comp)
        }
        result["total_overtime_compensation"] += daily_first_comp + daily_additional_comp
    
    # Weekly overtime
    if weekly_overtime_hours > 0:
        weekly_first = min(weekly_overtime_hours, 8)
        weekly_additional = max(0, weekly_overtime_hours - 8)
        
        weekly_first_comp = weekly_first * hourly_rate * (1 + weekly_first_rate)
        weekly_additional_comp = weekly_additional * hourly_rate * (1 + weekly_additional_rate)
        
        result["breakdown"]["weekly_overtime"] = {
            "hours_at_50%": weekly_first,
            "hours_at_100%": weekly_additional,
            "compensation_50%": round_currency(weekly_first_comp),
            "compensation_100%": round_currency(weekly_additional_comp),
            "total": round_currency(weekly_first_comp + weekly_additional_comp)
        }
        result["total_overtime_compensation"] += weekly_first_comp + weekly_additional_comp
    
    result["total_overtime_compensation"] = round_currency(result["total_overtime_compensation"])
    
    return result


# =============================================================================
# SALARY COMPARISON
# =============================================================================

def compare_salaries(
    tes_names: List[str],
    job_group: str = None,
    experience_years: int = 0
) -> Dict:
    """
    Compare salaries across multiple TES agreements.
    
    Args:
        tes_names: List of TES names to compare
        job_group: Job group/classification to compare
        experience_years: Years of experience
    
    Returns:
        Salary comparison data
    """
    comparisons = []
    
    for tes_name in tes_names:
        tes_data = get_tes_data(tes_name)
        if not tes_data:
            comparisons.append({
                "tes_name": tes_name,
                "error": "TES not found"
            })
            continue
        
        salary = get_salary_from_tes(tes_data, job_group, experience_years)
        
        comparison = {
            "tes_name": tes_name,
            "monthly_salary": salary,
            "annual_salary": salary * 12 if salary else None,
            "hourly_rate": round_currency(salary / 160) if salary else None,
            "job_group": job_group,
            "experience_years": experience_years
        }
        
        # Add extra benefits info
        vacation = tes_data.get("vacation", {})
        if vacation.get("vacation_bonus"):
            comparison["vacation_bonus"] = vacation["vacation_bonus"]
        
        if vacation.get("days_standard"):
            comparison["vacation_days"] = vacation["days_standard"]
        
        comparisons.append(comparison)
    
    # Sort by salary (highest first)
    comparisons.sort(key=lambda x: x.get("monthly_salary") or 0, reverse=True)
    
    # Calculate statistics
    salaries = [c["monthly_salary"] for c in comparisons if c.get("monthly_salary")]
    
    result = {
        "comparisons": comparisons,
        "job_group": job_group,
        "experience_years": experience_years
    }
    
    if salaries:
        result["statistics"] = {
            "highest": max(salaries),
            "lowest": min(salaries),
            "average": round_currency(sum(salaries) / len(salaries)),
            "difference_highest_lowest": round_currency(max(salaries) - min(salaries)),
            "difference_percentage": round_currency((max(salaries) - min(salaries)) / min(salaries) * 100) if min(salaries) > 0 else 0
        }
    
    return result


# =============================================================================
# EXPERIENCE PROGRESSION
# =============================================================================

def calculate_experience_progression(
    tes_name: str,
    job_group: str = None,
    max_years: int = 15
) -> Dict:
    """
    Show salary progression based on experience years.
    
    Args:
        tes_name: TES document name
        job_group: Optional job group
        max_years: Maximum years to project
    
    Returns:
        Salary progression data for visualization
    """
    tes_data = get_tes_data(tes_name)
    if not tes_data:
        return {"error": f"TES '{tes_name}' not found"}
    
    progression = []
    salary_tables = tes_data.get("salary_tables", [])
    
    if not salary_tables:
        return {"error": "No salary tables found in TES"}
    
    # Find experience-based levels (try both 'levels' and 'experience_levels')
    table = salary_tables[0]
    levels = table.get("levels", []) or table.get("experience_levels", [])
    
    # Helper to parse experience range from level name
    def parse_exp_range(level_str):
        import re
        if "alle" in level_str.lower():
            nums = re.findall(r'\d+', level_str)
            return (0, int(nums[0])) if nums else (0, 1)
        if "yli" in level_str.lower():
            nums = re.findall(r'\d+', level_str)
            return (int(nums[0]) if nums else 5, 99)
        nums = re.findall(r'\d+', level_str)
        if len(nums) >= 2:
            return (int(nums[0]), int(nums[1]))
        elif len(nums) == 1:
            return (int(nums[0]), int(nums[0]))
        return None
    
    # Helper to extract salary
    def extract_salary(level):
        return (level.get("monthly_salary") or 
                level.get("minimum_salary") or 
                (level.get("hourly_rate", 0) * 160))
    
    # Build experience thresholds from TES
    experience_thresholds = {}
    for level in levels:
        exp_years = level.get("experience_years")
        level_name = level.get("name", "") or level.get("level", "")
        
        if exp_years is not None:
            salary = extract_salary(level)
            experience_thresholds[exp_years] = salary
        elif level_name:
            exp_range = parse_exp_range(level_name)
            if exp_range:
                min_exp, _ = exp_range
                salary = extract_salary(level)
                if salary > 0:
                    experience_thresholds[min_exp] = salary
    
    # If no experience data, use first level with 2% increment
    if not experience_thresholds and levels:
        base_salary = extract_salary(levels[0])
        if base_salary > 0:
            increment = base_salary * 0.02  # Assume 2% annual increase
            for year in range(max_years + 1):
                experience_thresholds[year] = round_currency(base_salary + (increment * year))
    
    # Generate progression data
    last_salary = 0
    for year in range(max_years + 1):
        # Find applicable salary
        applicable_salary = last_salary
        for threshold_year in sorted(experience_thresholds.keys()):
            if year >= threshold_year:
                applicable_salary = experience_thresholds[threshold_year]
            else:
                break
        
        if applicable_salary == 0 and experience_thresholds:
            applicable_salary = min(experience_thresholds.values())
        
        last_salary = applicable_salary
        
        progression.append({
            "years": year,
            "monthly_salary": round_currency(applicable_salary),
            "annual_salary": round_currency(applicable_salary * 12),
            "hourly_rate": round_currency(applicable_salary / 160)
        })
    
    # Calculate total career earnings
    total_career_earnings = sum(p["annual_salary"] for p in progression)
    
    return {
        "tes_name": tes_name,
        "job_group": job_group,
        "progression": progression,
        "experience_thresholds": experience_thresholds,
        "total_career_earnings_15y": round_currency(total_career_earnings),
        "salary_growth": {
            "start": progression[0]["monthly_salary"] if progression else 0,
            "end": progression[-1]["monthly_salary"] if progression else 0,
            "growth_percentage": round_currency(
                ((progression[-1]["monthly_salary"] - progression[0]["monthly_salary"]) / progression[0]["monthly_salary"] * 100)
                if progression and progression[0]["monthly_salary"] > 0 else 0
            )
        }
    }


# =============================================================================
# VACATION PAY CALCULATOR
# =============================================================================

def calculate_vacation_pay(
    monthly_salary: float,
    tes_data: dict,
    employment_years: int = 1,
    vacation_days_taken: int = None
) -> Dict:
    """
    Calculate vacation pay and bonus.
    
    Args:
        monthly_salary: Monthly salary
        tes_data: TES document data
        employment_years: Years of employment
        vacation_days_taken: Days of vacation being taken (if calculating for specific period)
    
    Returns:
        Vacation pay calculation
    """
    vacation = tes_data.get("vacation", {})
    
    # Determine vacation days based on employment length
    if employment_years < 1:
        days_earned = int(vacation.get("days_first_year", 24))
    elif employment_years >= 15:
        days_earned = int(vacation.get("days_senior", vacation.get("days_standard", 30)))
    else:
        days_earned = int(vacation.get("days_standard", 30))
    
    if vacation_days_taken is None:
        vacation_days_taken = days_earned
    
    # Calculate daily rate
    # Finnish vacation pay: monthly salary / 25 working days
    daily_rate = monthly_salary / 25
    
    # Vacation pay
    vacation_pay = daily_rate * vacation_days_taken
    
    # Vacation bonus (lomaraha)
    vacation_bonus_text = vacation.get("vacation_bonus", "50%")
    if "50%" in str(vacation_bonus_text):
        vacation_bonus = vacation_pay * 0.5
    elif isinstance(vacation_bonus_text, (int, float)):
        vacation_bonus = float(vacation_bonus_text)
    else:
        # Try to parse percentage
        try:
            percent = float(str(vacation_bonus_text).replace("%", "").strip()) / 100
            vacation_bonus = vacation_pay * percent
        except:
            vacation_bonus = vacation_pay * 0.5  # Default 50%
    
    # Holiday pay multiplier for work done during vacation
    holiday_compensation = vacation.get("holiday_compensation", "")
    
    result = {
        "monthly_salary": round_currency(monthly_salary),
        "employment_years": employment_years,
        "calculation": {
            "days_earned": days_earned,
            "days_taken": vacation_days_taken,
            "daily_rate": round_currency(daily_rate),
            "vacation_pay": round_currency(vacation_pay),
            "vacation_bonus": round_currency(vacation_bonus),
            "total_vacation_payment": round_currency(vacation_pay + vacation_bonus)
        },
        "tes_rules": {
            "days_first_year": vacation.get("days_first_year"),
            "days_standard": vacation.get("days_standard"),
            "days_senior": vacation.get("days_senior"),
            "vacation_bonus_rule": vacation_bonus_text
        }
    }
    
    return result


# =============================================================================
# PART-TIME PRO-RATA CALCULATOR
# =============================================================================

def calculate_part_time_salary(
    full_time_monthly_salary: float,
    tes_data: dict,
    weekly_hours: float,
    full_time_hours: float = None
) -> Dict:
    """
    Calculate part-time salary pro-rata.
    
    Args:
        full_time_monthly_salary: Full-time monthly salary
        tes_data: TES document data
        weekly_hours: Part-time weekly hours
        full_time_hours: Full-time weekly hours (will use TES default if not provided)
    
    Returns:
        Part-time salary calculation
    """
    working_hours = tes_data.get("working_hours", {})
    
    if full_time_hours is None:
        full_time_hours = float(working_hours.get("weekly_hours", 37.5))
    
    # Calculate part-time ratio
    part_time_ratio = weekly_hours / full_time_hours
    
    # Pro-rata salary
    part_time_salary = full_time_monthly_salary * part_time_ratio
    
    # Calculate hourly rate
    monthly_hours = weekly_hours * 4.33  # Average weeks per month
    hourly_rate = part_time_salary / monthly_hours if monthly_hours > 0 else 0
    
    result = {
        "full_time": {
            "weekly_hours": full_time_hours,
            "monthly_salary": round_currency(full_time_monthly_salary),
            "annual_salary": round_currency(full_time_monthly_salary * 12)
        },
        "part_time": {
            "weekly_hours": weekly_hours,
            "ratio": round_currency(part_time_ratio * 100),
            "monthly_salary": round_currency(part_time_salary),
            "annual_salary": round_currency(part_time_salary * 12),
            "hourly_rate": round_currency(hourly_rate),
            "monthly_hours": round_currency(monthly_hours)
        },
        "tes_working_hours": working_hours.get("weekly_hours", "Not specified")
    }
    
    # Vacation days pro-rata
    vacation = tes_data.get("vacation", {})
    vacation_days = vacation.get("days_standard", 30)
    result["vacation_days_pro_rata"] = int(vacation_days * part_time_ratio)
    
    return result


# =============================================================================
# ANNUAL COST CALCULATOR FOR EMPLOYERS
# =============================================================================

def calculate_annual_employer_cost(
    monthly_salary: float,
    tes_data: dict,
    include_shift_work: bool = False,
    estimated_overtime_hours: int = 0,
    estimated_sick_days: int = 10
) -> Dict:
    """
    Calculate total annual cost for employer including all mandatory contributions.
    
    Args:
        monthly_salary: Monthly gross salary
        tes_data: TES document data
        include_shift_work: Whether to include estimated shift work costs
        estimated_overtime_hours: Estimated annual overtime hours
        estimated_sick_days: Estimated sick days per year
    
    Returns:
        Total employer cost breakdown
    """
    annual_salary = monthly_salary * 12
    
    # Finnish employer contributions (2024 approximate rates)
    employer_contributions = {
        "tyel_pension": 0.1715,  # TyEL pension (employer share ~17.15%)
        "unemployment_insurance": 0.0143,  # Työttömyysvakuutus
        "accident_insurance": 0.007,  # Tapaturmavakuutus (varies by industry)
        "group_life_insurance": 0.0006,  # Ryhmähenkivakuutus
        "health_insurance": 0.0134,  # Sairausvakuutus (employer share)
    }
    
    # Calculate contributions
    contribution_costs = {}
    total_contributions = 0
    
    for name, rate in employer_contributions.items():
        cost = annual_salary * rate
        contribution_costs[name] = {
            "rate": f"{rate * 100:.2f}%",
            "annual_cost": round_currency(cost)
        }
        total_contributions += cost
    
    # Vacation bonus cost
    vacation = tes_data.get("vacation", {})
    vacation_bonus_text = vacation.get("vacation_bonus", "50%")
    if "50%" in str(vacation_bonus_text):
        days_raw = vacation.get("days_standard", 30)
        try:
            vacation_days = int(days_raw) if isinstance(days_raw, (int, float)) else 30
        except (ValueError, TypeError):
            vacation_days = 30
        daily_rate = monthly_salary / 25
        vacation_pay = daily_rate * vacation_days
        vacation_bonus_cost = vacation_pay * 0.5
    else:
        vacation_bonus_cost = 0
    
    # Sick leave cost (employer pays first 9 days typically)
    sick_leave = tes_data.get("sick_leave", {})
    paid_days_raw = sick_leave.get("paid_days_standard", 9)
    try:
        if isinstance(paid_days_raw, (int, float)):
            paid_sick_days = int(paid_days_raw)
        elif isinstance(paid_days_raw, str):
            # Try to extract first number from string like "28 päivää" or "1 kk - 3 v: 28 päivää"
            import re
            numbers = re.findall(r'\d+', paid_days_raw)
            paid_sick_days = int(numbers[-1]) if numbers else 9  # Use last number found
        else:
            paid_sick_days = 9
    except (ValueError, IndexError):
        paid_sick_days = 9  # Default
    actual_sick_days = min(estimated_sick_days, paid_sick_days)
    daily_salary = monthly_salary / 21
    sick_leave_cost = actual_sick_days * daily_salary
    
    # Overtime cost
    overtime_cost = 0
    if estimated_overtime_hours > 0:
        hourly_rate = monthly_salary / 160
        # Assume average 75% overtime premium
        overtime_cost = estimated_overtime_hours * hourly_rate * 1.75
    
    # Shift work cost estimate
    shift_work_cost = 0
    if include_shift_work:
        shift_work = tes_data.get("shift_work", {})
        # Estimate based on typical shift pattern
        shift_work_cost = monthly_salary * 0.1 * 12  # Rough 10% premium
    
    # Training and development (estimate)
    training_cost = annual_salary * 0.02  # 2% of salary
    
    # Administrative overhead (recruitment, HR, payroll)
    admin_overhead = annual_salary * 0.03  # 3% estimate
    
    # Total cost calculation
    total_cost = (
        annual_salary +
        total_contributions +
        vacation_bonus_cost +
        sick_leave_cost +
        overtime_cost +
        shift_work_cost +
        training_cost +
        admin_overhead
    )
    
    result = {
        "gross_salary": {
            "monthly": round_currency(monthly_salary),
            "annual": round_currency(annual_salary)
        },
        "employer_contributions": contribution_costs,
        "total_contributions": round_currency(total_contributions),
        "additional_costs": {
            "vacation_bonus": round_currency(vacation_bonus_cost),
            "estimated_sick_leave": round_currency(sick_leave_cost),
            "estimated_overtime": round_currency(overtime_cost),
            "shift_work_premium": round_currency(shift_work_cost) if include_shift_work else 0,
            "training_development": round_currency(training_cost),
            "administrative_overhead": round_currency(admin_overhead)
        },
        "total_annual_cost": round_currency(total_cost),
        "cost_per_month": round_currency(total_cost / 12),
        "cost_multiplier": round_currency(total_cost / annual_salary),
        "notes": [
            "Employer contributions based on 2024 approximate rates",
            "Actual rates vary by company size and industry",
            f"Sick leave cost based on {estimated_sick_days} estimated sick days",
            "Training and admin costs are estimates"
        ]
    }
    
    return result


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="TES Salary Calculators")
    subparsers = parser.add_subparsers(dest="command")
    
    # Total compensation
    total_parser = subparsers.add_parser("total", help="Total compensation calculator")
    total_parser.add_argument("--tes", required=True, help="TES name")
    total_parser.add_argument("--salary", type=float, required=True, help="Monthly base salary")
    total_parser.add_argument("--evening-hours", type=int, default=0, help="Evening shift hours/month")
    total_parser.add_argument("--night-hours", type=int, default=0, help="Night shift hours/month")
    
    # Shift work
    shift_parser = subparsers.add_parser("shift", help="Shift work calculator")
    shift_parser.add_argument("--tes", required=True, help="TES name")
    shift_parser.add_argument("--hourly-rate", type=float, required=True, help="Base hourly rate")
    shift_parser.add_argument("--evening", type=int, default=0, help="Evening hours")
    shift_parser.add_argument("--night", type=int, default=0, help="Night hours")
    shift_parser.add_argument("--saturday", type=int, default=0, help="Saturday hours")
    shift_parser.add_argument("--sunday", type=int, default=0, help="Sunday hours")
    
    # Overtime
    overtime_parser = subparsers.add_parser("overtime", help="Overtime calculator")
    overtime_parser.add_argument("--tes", required=True, help="TES name")
    overtime_parser.add_argument("--hourly-rate", type=float, required=True, help="Base hourly rate")
    overtime_parser.add_argument("--daily", type=float, default=0, help="Daily overtime hours")
    overtime_parser.add_argument("--weekly", type=float, default=0, help="Weekly overtime hours")
    
    # Comparison
    compare_parser = subparsers.add_parser("compare", help="Compare salaries across TES")
    compare_parser.add_argument("--tes", nargs="+", required=True, help="TES names to compare")
    compare_parser.add_argument("--job-group", help="Job group")
    compare_parser.add_argument("--experience", type=int, default=0, help="Experience years")
    
    # Experience progression
    exp_parser = subparsers.add_parser("progression", help="Experience salary progression")
    exp_parser.add_argument("--tes", required=True, help="TES name")
    exp_parser.add_argument("--job-group", help="Job group")
    exp_parser.add_argument("--max-years", type=int, default=15, help="Max years to project")
    
    # Vacation pay
    vacation_parser = subparsers.add_parser("vacation", help="Vacation pay calculator")
    vacation_parser.add_argument("--tes", required=True, help="TES name")
    vacation_parser.add_argument("--salary", type=float, required=True, help="Monthly salary")
    vacation_parser.add_argument("--years", type=int, default=1, help="Employment years")
    vacation_parser.add_argument("--days", type=int, help="Vacation days to calculate")
    
    # Part-time
    parttime_parser = subparsers.add_parser("parttime", help="Part-time pro-rata calculator")
    parttime_parser.add_argument("--tes", required=True, help="TES name")
    parttime_parser.add_argument("--salary", type=float, required=True, help="Full-time monthly salary")
    parttime_parser.add_argument("--hours", type=float, required=True, help="Part-time weekly hours")
    
    # Annual cost
    cost_parser = subparsers.add_parser("cost", help="Annual employer cost calculator")
    cost_parser.add_argument("--tes", required=True, help="TES name")
    cost_parser.add_argument("--salary", type=float, required=True, help="Monthly salary")
    cost_parser.add_argument("--overtime-hours", type=int, default=0, help="Estimated annual overtime")
    cost_parser.add_argument("--sick-days", type=int, default=10, help="Estimated sick days")
    cost_parser.add_argument("--shift-work", action="store_true", help="Include shift work")
    
    args = parser.parse_args()
    
    if args.command == "total":
        tes_data = get_tes_data(args.tes)
        if not tes_data:
            print(json.dumps({"error": f"TES '{args.tes}' not found"}))
            sys.exit(1)
        
        shift_work = None
        if args.evening_hours or args.night_hours:
            shift_work = {
                "evening_hours": args.evening_hours,
                "night_hours": args.night_hours
            }
        
        result = calculate_total_compensation(args.salary, tes_data, shift_work=shift_work)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "shift":
        tes_data = get_tes_data(args.tes)
        if not tes_data:
            print(json.dumps({"error": f"TES '{args.tes}' not found"}))
            sys.exit(1)
        
        result = calculate_shift_work(
            args.hourly_rate, tes_data,
            evening_hours=args.evening, night_hours=args.night,
            saturday_hours=args.saturday, sunday_hours=args.sunday
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "overtime":
        tes_data = get_tes_data(args.tes)
        if not tes_data:
            print(json.dumps({"error": f"TES '{args.tes}' not found"}))
            sys.exit(1)
        
        result = calculate_overtime(
            args.hourly_rate, tes_data,
            daily_overtime_hours=args.daily,
            weekly_overtime_hours=args.weekly
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "compare":
        result = compare_salaries(args.tes, args.job_group, args.experience)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "progression":
        result = calculate_experience_progression(args.tes, args.job_group, args.max_years)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "vacation":
        tes_data = get_tes_data(args.tes)
        if not tes_data:
            print(json.dumps({"error": f"TES '{args.tes}' not found"}))
            sys.exit(1)
        
        result = calculate_vacation_pay(args.salary, tes_data, args.years, args.days)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "parttime":
        tes_data = get_tes_data(args.tes)
        if not tes_data:
            print(json.dumps({"error": f"TES '{args.tes}' not found"}))
            sys.exit(1)
        
        result = calculate_part_time_salary(args.salary, tes_data, args.hours)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "cost":
        tes_data = get_tes_data(args.tes)
        if not tes_data:
            print(json.dumps({"error": f"TES '{args.tes}' not found"}))
            sys.exit(1)
        
        result = calculate_annual_employer_cost(
            args.salary, tes_data,
            include_shift_work=args.shift_work,
            estimated_overtime_hours=args.overtime_hours,
            estimated_sick_days=args.sick_days
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()
