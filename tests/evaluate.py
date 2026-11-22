"""
evaluate.py — Performance Evaluation
Simulates ground-truth scenarios and measures:
  Accuracy, Precision, Recall, F1-score per detection mode.
Saves report to tests/reports/evaluation_report.json

Run: python tests/evaluate.py
"""

import sys
import os
import json
import time
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from fusion import FusionEngine

SLOTS      = ["P1", "P2", "P3", "P4"]
REPORT_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORT_DIR, exist_ok=True)


# ── Metric helpers ────────────────────────────────────────────────

def compute_metrics(tp, tn, fp, fn):
    total     = tp + tn + fp + fn
    accuracy  = (tp + tn) / total if total else 0
    precision = tp / (tp + fp)    if (tp + fp) else 0
    recall    = tp / (tp + fn)    if (tp + fn) else 0
    f1        = (2 * precision * recall / (precision + recall)
                 if (precision + recall) else 0)
    return {
        "accuracy":  round(accuracy,  4),
        "precision": round(precision, 4),
        "recall":    round(recall,    4),
        "f1_score":  round(f1,        4),
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
    }


# ── Scenario generator ────────────────────────────────────────────

def run_scenario(mode: str, n_trials: int = 200, noise: float = 0.1):
    """
    mode: 'camera' | 'sensor' | 'hybrid'
    noise: probability of a wrong reading (simulates detection errors)
    """
    tp = tn = fp = fn = 0
    latencies = []

    for _ in range(n_trials):
        ground_truth = random.choice([True, False])
        engine = FusionEngine(SLOTS)

        t0 = time.perf_counter()

        for _ in range(3):  # stability window
            cam_read    = ground_truth if random.random() > noise else not ground_truth
            sensor_read = ground_truth if random.random() > noise else not ground_truth

            if mode in ("camera", "hybrid"):
                conf = random.uniform(0.7, 0.95) if cam_read else 0.0
                engine.update_camera("P1", cam_read, conf)

            if mode in ("sensor", "hybrid"):
                dist = random.uniform(5, 30) if sensor_read else random.uniform(80, 150)
                engine.update_sensor("P1", sensor_read, dist)

        latency_ms = (time.perf_counter() - t0) * 1000
        latencies.append(latency_ms)

        predicted = engine.get_state("P1")["occupied"]

        if ground_truth and predicted:      tp += 1
        elif not ground_truth and not predicted: tn += 1
        elif not ground_truth and predicted: fp += 1
        else:                               fn += 1

    metrics = compute_metrics(tp, tn, fp, fn)
    metrics["avg_latency_ms"] = round(sum(latencies) / len(latencies), 3)
    metrics["max_latency_ms"] = round(max(latencies), 3)
    metrics["trials"]         = n_trials
    metrics["noise_rate"]     = noise
    return metrics


# ── Lighting / occlusion stress tests ────────────────────────────

def run_stress_tests():
    """Simulate degraded conditions by increasing noise."""
    results = {}
    conditions = {
        "normal":          0.05,
        "low_light":       0.15,
        "partial_occlusion": 0.25,
        "sensor_failure":  0.40,
    }
    for condition, noise in conditions.items():
        results[condition] = run_scenario("hybrid", n_trials=100, noise=noise)
    return results


# ── Main ──────────────────────────────────────────────────────────

def main():
    print("\n=== Smart Parking Performance Evaluation ===\n")

    report = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "modes": {}, "stress": {}}

    for mode in ["camera", "sensor", "hybrid"]:
        print(f"[{mode.upper()}] Running 200 trials...")
        metrics = run_scenario(mode, n_trials=200, noise=0.1)
        report["modes"][mode] = metrics
        print(f"  Accuracy:  {metrics['accuracy']*100:.1f}%")
        print(f"  Precision: {metrics['precision']*100:.1f}%")
        print(f"  Recall:    {metrics['recall']*100:.1f}%")
        print(f"  F1-Score:  {metrics['f1_score']*100:.1f}%")
        print(f"  Avg Latency: {metrics['avg_latency_ms']:.2f} ms\n")

    print("[STRESS] Running degraded condition tests...")
    stress = run_stress_tests()
    report["stress"] = stress
    for cond, m in stress.items():
        print(f"  {cond:25s} -> F1: {m['f1_score']*100:.1f}%  Acc: {m['accuracy']*100:.1f}%")

    # Save report
    report_path = os.path.join(REPORT_DIR, "evaluation_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n[SAVED] Report -> {report_path}")

    # Print comparison table
    print("\n=== Mode Comparison ===")
    print(f"{'Mode':<10} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1':>10} {'Latency(ms)':>12}")
    print("-" * 60)
    for mode, m in report["modes"].items():
        print(f"{mode:<10} {m['accuracy']*100:>9.1f}% {m['precision']*100:>9.1f}% "
              f"{m['recall']*100:>9.1f}% {m['f1_score']*100:>9.1f}% {m['avg_latency_ms']:>11.2f}")


if __name__ == "__main__":
    main()
