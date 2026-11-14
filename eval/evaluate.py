"""
评估脚本
用法: python -m eval.evaluate
"""

import json
import re
import time
import statistics

from app.retrieval import retrieve
from app.generation import generate

TEST_SET = "eval/test_set.json"
TOP_K = 5


def contains_evidence(docs: list[str], evidence: str) -> bool:
    if not evidence:
        return False
    ev = evidence.lower()
    return any(ev in d.lower() for d in docs)


def run_one(sample: dict) -> dict:
    q = sample["query"]
    cat = sample["category"]
    ev = sample["evidence"]

    start = time.time()
    try:
        retrieved = retrieve(q, top_k=TOP_K)
        gen = generate(q)
        latency_ms = int((time.time() - start) * 1000)
        error = None
    except Exception as e:
        return {
            "query": q, "category": cat,
            "recall_hit": None, "grounded": None, "refused": None,
            "latency_ms": None, "error": str(e)[:200],
        }

    if cat == "unanswerable":
        recall_hit = None  # 不适用
        correct_refusal = gen["refused"]
    else:
        recall_hit = contains_evidence(retrieved["documents"], ev)
        correct_refusal = None

    return {
        "query": q,
        "category": cat,
        "recall_hit": recall_hit,
        "grounded": gen["grounded"],
        "refused": gen["refused"],
        "correct_refusal": correct_refusal,
        "latency_ms": latency_ms,
        "error": error,
    }


def summarize(results: list[dict]):
    by_cat = {}
    for r in results:
        by_cat.setdefault(r["category"], []).append(r)

    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)

    for cat in ["normal", "exact_token", "unanswerable"]:
        rows = by_cat.get(cat, [])
        if not rows:
            continue
        n = len(rows)
        errors = sum(1 for r in rows if r["error"])

        if cat == "unanswerable":
            correct = sum(1 for r in rows if r["correct_refusal"] is True)
            print(f"\n[{cat}] n={n}  errors={errors}")
            print(f"  Correct refusal rate: {correct}/{n} = {correct/n:.2f}")
        else:
            hits = sum(1 for r in rows if r["recall_hit"] is True)
            grounded = sum(1 for r in rows if r["grounded"] is True)
            print(f"\n[{cat}] n={n}  errors={errors}")
            print(f"  Recall@{TOP_K}: {hits}/{n} = {hits/n:.2f}")
            print(f"  Grounding rate: {grounded}/{n} = {grounded/n:.2f}")

        lats = [r["latency_ms"] for r in rows if r["latency_ms"] is not None]
        if lats:
            p95 = sorted(lats)[max(0, int(len(lats) * 0.95) - 1)]
            print(f"  p95 latency: {p95} ms")

    all_lats = [r["latency_ms"] for r in results if r["latency_ms"] is not None]
    if all_lats:
        print(f"\nOverall p95 latency: {sorted(all_lats)[max(0, int(len(all_lats)*0.95)-1)]} ms")
        print(f"Overall mean latency: {int(statistics.mean(all_lats))} ms")

    # 失败案例
    print("\n" + "=" * 60)
    print("FAILURES (for analysis)")
    print("=" * 60)
    for r in results:
        if r["error"]:
            print(f"[ERROR] {r['query']}  -> {r['error']}")
        elif r["category"] != "unanswerable" and r["recall_hit"] is False:
            print(f"[MISS]  {r['query']}")
        elif r["category"] == "unanswerable" and r["correct_refusal"] is False:
            print(f"[FALSE-ANSWER] {r['query']}")


def main():
    with open(TEST_SET, encoding="utf-8") as f:
        test_set = json.load(f)

    print(f"Running {len(test_set)} samples...\n")
    results = []
    for i, sample in enumerate(test_set, 1):
        print(f"[{i}/{len(test_set)}] {sample['category']:12s} | {sample['query'][:60]}")
        r = run_one(sample)
        results.append(r)
        if r["error"]:
            print(f"     ERROR: {r['error'][:100]}")
        time.sleep(1)  # 避免限流

    summarize(results)

    with open("eval/results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\nDetailed results saved to eval/results.json")


if __name__ == "__main__":
    main()