#!/usr/bin/env python3
"""
Requirements Verification Script

Parses pytest JUnit XML results and cross-references them against the
verification matrix to produce a requirements coverage report.

Usage:
    python verify_requirements.py \
        --test-results backend/test-results.xml \
        --matrix requirements/verification-matrix.md \
        --output requirements-report.md

    python verify_requirements.py \
        --test-results backend/test-results.xml \
        --matrix requirements/verification-matrix.md \
        --check-regressions
"""

import argparse
import re
import sys
from pathlib import Path

try:
    from lxml import etree
except ImportError:
    import xml.etree.ElementTree as etree


def parse_test_results(xml_path: str) -> dict:
    """Parse JUnit XML and return dict of test name -> passed (bool)."""
    results = {}
    tree = etree.parse(xml_path)
    root = tree.getroot()

    for testsuite in root.iter("testsuite"):
        for testcase in testsuite.iter("testcase"):
            classname = testcase.get("classname", "")
            name = testcase.get("name", "")

            # Build full test identifier
            full_name = f"{classname}::{name}" if classname else name
            # Also store short name for flexible matching
            short_name = name

            # Check if test failed or errored
            failed = (
                testcase.find("failure") is not None
                or testcase.find("error") is not None
            )
            skipped = testcase.find("skipped") is not None

            if not skipped:
                results[full_name] = not failed
                results[short_name] = not failed

                # Also store the file::test format for matching
                # e.g., test_auth.py::test_register_user
                if "." in classname:
                    parts = classname.rsplit(".", 1)
                    file_test = f"{parts[-1]}::{name}"
                    results[file_test] = not failed

    return results


def parse_matrix(matrix_path: str) -> list:
    """Parse verification matrix markdown and extract requirements."""
    requirements = []
    content = Path(matrix_path).read_text(encoding="utf-8")

    # Match table rows: | REQ-ID | Description | Method | Artifact | Status |
    row_pattern = re.compile(
        r"\|\s*((?:SYS|FT|CMP)-\d+)\s*\|"  # Req ID
        r"\s*([^|]+)\|"  # Description
        r"\s*([^|]+)\|"  # Method
        r"\s*([^|]+)\|"  # Artifact
        r"\s*(\w+)\s*\|"  # Status
    )

    for match in row_pattern.finditer(content):
        req_id = match.group(1).strip()
        description = match.group(2).strip()
        methods = match.group(3).strip()
        artifact = match.group(4).strip()
        status = match.group(5).strip()

        # Extract test references from artifact column
        test_refs = []
        # Match patterns like `test_auth.py::test_register_user`
        test_pattern = re.compile(r"`([^`]+)`")
        for test_match in test_pattern.finditer(artifact):
            ref = test_match.group(1)
            # Only include if it looks like a test reference
            if "::" in ref or ref.startswith("test_"):
                test_refs.append(ref)

        has_t_method = "T" in methods
        has_d_method = "D" in methods
        has_i_method = "I" in methods
        has_a_method = "A" in methods

        requirements.append(
            {
                "id": req_id,
                "description": description,
                "methods": methods,
                "artifact": artifact,
                "declared_status": status,
                "test_refs": test_refs,
                "has_t": has_t_method,
                "has_d": has_d_method,
                "has_i": has_i_method,
                "has_a": has_a_method,
            }
        )

    return requirements


def check_test_requirement(req: dict, test_results: dict) -> str:
    """Check if a T-method requirement's tests pass. Returns status string."""
    if not req["has_t"]:
        return "N/A"  # No T method, can't check via tests

    if not req["test_refs"]:
        return "NO_TESTS"  # T method declared but no test references

    all_pass = True
    any_found = False

    for ref in req["test_refs"]:
        # Try exact match first
        if ref in test_results:
            any_found = True
            if not test_results[ref]:
                all_pass = False
            continue

        # Try partial match (test file::class::method or just method name)
        matched = False
        for test_name, passed in test_results.items():
            if ref in test_name or test_name.endswith(ref):
                any_found = True
                matched = True
                if not passed:
                    all_pass = False
                break

        if not matched:
            # Check if it's a file-level reference like `test_auth.py`
            if "::" not in ref and ref.endswith(".py"):
                # Check if any tests from that file exist and pass
                file_tests = {
                    k: v for k, v in test_results.items() if ref.rstrip(".py") in k
                }
                if file_tests:
                    any_found = True
                    if not all(file_tests.values()):
                        all_pass = False

    if not any_found:
        return "TESTS_NOT_FOUND"

    return "PASS" if all_pass else "FAIL"


def generate_report(
    requirements: list, test_results: dict, output_path: str = None
) -> str:
    """Generate requirements coverage report."""
    lines = []
    lines.append("# Requirements Verification Report")
    lines.append("")
    lines.append(f"**Generated**: automated release check")
    lines.append(
        f"**Total tests executed**: {sum(1 for v in test_results.values() if v is not None)}"
    )
    lines.append(
        f"**Tests passed**: {sum(1 for v in test_results.values() if v is True)}"
    )
    lines.append(
        f"**Tests failed**: {sum(1 for v in test_results.values() if v is False)}"
    )
    lines.append("")

    # Categorize requirements
    verified = []
    implemented = []
    planned = []
    regressions = []
    test_verified = []

    for req in requirements:
        test_status = check_test_requirement(req, test_results)

        if req["declared_status"] == "VERIFIED" and test_status == "FAIL":
            regressions.append((req, test_status))
        elif req["declared_status"] == "VERIFIED" and test_status in (
            "PASS",
            "N/A",
        ):
            verified.append((req, test_status))
        elif req["declared_status"] == "IMPLEMENTED":
            if test_status == "PASS":
                test_verified.append((req, test_status))
            else:
                implemented.append((req, test_status))
        elif req["declared_status"] == "PLANNED":
            planned.append((req, test_status))
        elif req["declared_status"] == "PARTIAL":
            if test_status == "FAIL":
                regressions.append((req, test_status))
            else:
                verified.append((req, test_status))
        else:
            implemented.append((req, test_status))

    total_active = len(verified) + len(implemented) + len(test_verified)
    total_verified = len(verified) + len(test_verified)

    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Metric | Count |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total requirements | {len(requirements)} |")
    lines.append(f"| Verified | {len(verified)} |")
    lines.append(f"| Newly verified by tests | {len(test_verified)} |")
    lines.append(f"| Implemented (unverified) | {len(implemented)} |")
    lines.append(f"| Planned | {len(planned)} |")
    lines.append(f"| **Regressions** | **{len(regressions)}** |")
    if total_active > 0:
        pct = round(total_verified / total_active * 100, 1)
        lines.append(f"| **Verification rate** | **{pct}%** |")
    lines.append("")

    # Regressions (most critical)
    if regressions:
        lines.append("## REGRESSIONS (previously verified, now failing)")
        lines.append("")
        lines.append("| Req ID | Description | Test Status |")
        lines.append("|--------|-------------|-------------|")
        for req, status in regressions:
            lines.append(f"| {req['id']} | {req['description']} | {status} |")
        lines.append("")

    # Newly verified
    if test_verified:
        lines.append("## Newly Verified (IMPLEMENTED → tests now pass)")
        lines.append("")
        lines.append("| Req ID | Description |")
        lines.append("|--------|-------------|")
        for req, _ in test_verified:
            lines.append(f"| {req['id']} | {req['description']} |")
        lines.append("")

    # Verified
    lines.append("## Verified Requirements")
    lines.append("")
    lines.append("| Req ID | Description | Test Check |")
    lines.append("|--------|-------------|------------|")
    for req, status in verified:
        lines.append(f"| {req['id']} | {req['description']} | {status} |")
    lines.append("")

    # Implemented but unverified
    if implemented:
        lines.append("## Implemented (Awaiting Verification)")
        lines.append("")
        lines.append("| Req ID | Description | Methods | Test Check |")
        lines.append("|--------|-------------|---------|------------|")
        for req, status in implemented:
            lines.append(
                f"| {req['id']} | {req['description']} | {req['methods']} | {status} |"
            )
        lines.append("")

    # Planned
    if planned:
        lines.append("## Planned (No Implementation)")
        lines.append("")
        lines.append("| Req ID | Description |")
        lines.append("|--------|-------------|")
        for req, _ in planned:
            lines.append(f"| {req['id']} | {req['description']} |")
        lines.append("")

    report = "\n".join(lines)

    if output_path:
        Path(output_path).write_text(report, encoding="utf-8")
        print(f"Report written to {output_path}")

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Verify requirements against test results"
    )
    parser.add_argument(
        "--test-results", required=True, help="Path to JUnit XML test results"
    )
    parser.add_argument(
        "--matrix", required=True, help="Path to verification-matrix.md"
    )
    parser.add_argument("--output", help="Path to write report (default: stdout)")
    parser.add_argument(
        "--check-regressions",
        action="store_true",
        help="Exit with code 1 if any regressions found",
    )

    args = parser.parse_args()

    # Parse inputs
    test_results = parse_test_results(args.test_results)
    requirements = parse_matrix(args.matrix)

    print(f"Parsed {len(test_results)} test results")
    print(f"Parsed {len(requirements)} requirements")

    # Generate report
    report = generate_report(requirements, test_results, args.output)

    if not args.output:
        print(report)

    # Check for regressions
    if args.check_regressions:
        regressions = []
        for req in requirements:
            if req["declared_status"] in ("VERIFIED", "PARTIAL"):
                status = check_test_requirement(req, test_results)
                if status == "FAIL":
                    regressions.append(req)

        if regressions:
            print(f"\nFATAL: {len(regressions)} regression(s) detected:")
            for req in regressions:
                print(f"  - {req['id']}: {req['description']}")
            sys.exit(1)
        else:
            print("\nNo regressions detected.")


if __name__ == "__main__":
    main()
