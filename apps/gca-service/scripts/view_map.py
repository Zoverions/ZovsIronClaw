#!/usr/bin/env python3
"""
System Map Viewer
Connects to the GCA Service to retrieve and display the current entropy, outliers, and skill landscape.
"""
import requests
import sys
import json
import time

def print_map(data):
    print("\n" + "="*60)
    print("       SYSTEM ENTROPY MAP & HORIZON SCAN")
    print("="*60)

    entropy = data.get("entropy", 0.0)
    print(f"\n[SYSTEM ENTROPY]: {entropy:.4f}")
    if entropy < 0.3:
        print("STATUS: HOMEOSTATIC (STABLE)")
    elif entropy < 0.7:
        print("STATUS: REFLEXIVE (ACTIVE CORRECTION)")
    else:
        print("STATUS: STRATEGIC (CRITICAL DIVERGENCE)")

    align = data.get("goal_alignment", 0.0)
    print(f"GOAL ALIGNMENT: {align*100:.1f}%")

    print("\n[HORIZON SCANNER]")
    horizon = data.get("horizon", {})
    variance = horizon.get("variance", 0.0)
    print(f"Variance: {variance:.6f}")
    if horizon.get("is_critical"):
        print("WARNING: CRITICAL VARIANCE DETECTED")

    pred = horizon.get("prediction")
    if pred:
        print(f"Prediction: {pred}")

    outliers = data.get("divergence_events", [])
    if outliers:
        print(f"\nDIVERGENCE EVENTS ({len(outliers)}):")
        for o in outliers[-5:]: # Show last 5
            ctx = o.get('context', '')[:80].replace('\n', ' ')
            print(f"- [Z={o.get('z_score', 0):.2f}] {ctx}...")
    else:
        print("\nNO DIVERGENCE EVENTS DETECTED.")

    print("\n[SKILL STRENGTHS]")
    skills = data.get("strong_skills", [])
    if skills:
        for s in skills[:10]:
            print(f"- {s['name']}: {s['strength']} exp")
    else:
        print("No skills recorded.")

    print("\n" + "="*60)

def main():
    url = "http://localhost:8000/v1/map"
    print(f"Connecting to {url}...")
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print_map(response.json())
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Failed to connect: {e}")
        print("Ensure the GCA Service is running.")

if __name__ == "__main__":
    main()
