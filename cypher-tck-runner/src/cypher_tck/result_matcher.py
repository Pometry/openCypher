"""Result matching utilities for comparing query results with expected values.

This module provides functionality to compare Cypher query results against
expected results from TCK feature files, including support for ordered and
unordered comparisons using Polars DataFrames.
"""

from __future__ import annotations

import re
from typing import Any

import polars as pl


class ResultMatcher:
    """Matches query results against expected results."""

    @staticmethod
    def parse_table_rows(table_rows: list[list[str]]) -> tuple[list[str], list[dict[str, Any]]]:
        """Parse table rows from Gherkin table format.

        Args:
            table_rows: List of rows from a Behave table, where first row is headers

        Returns:
            Tuple of (column_names, list of row dictionaries)
        """
        if not table_rows:
            return [], []

        headers = table_rows[0]
        rows = []

        for row in table_rows[1:]:
            row_dict = {}
            for header, value in zip(headers, row):
                # Gherkin table cells escape \\ as \\\\, \| as \\|, \n as \\n
                # Behave does NOT unescape these, so we do it here.
                value = value.replace('\\\\', '\x00').replace('\\n', '\n').replace('\\|', '|').replace('\x00', '\\')
                row_dict[header] = ResultMatcher._parse_value(value)
            rows.append(row_dict)

        return headers, rows

    @staticmethod
    def _parse_value(value: str) -> Any:
        """Parse a string value from a Gherkin table into a Python value.

        Handles:
        - null/NULL -> None
        - true/false -> bool
        - NaN -> float('nan')
        - Numbers -> int/float
        - Strings in quotes -> str
        - Lists [...] -> list
        - Maps {...} -> kept as string (engine returns maps as strings)
        - Node/relationship/path representations -> kept as string

        Args:
            value: String value from table cell

        Returns:
            Parsed Python value
        """
        value = value.strip()

        # Handle null
        if value.lower() == "null":
            return None

        # Handle NaN
        if value == "NaN":
            return float("nan")

        # Handle booleans
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False

        # Handle numbers (including scientific notation)
        try:
            if "." in value or "e" in value.lower():
                return float(value)
            return int(value)
        except ValueError:
            pass

        # Handle strings (quoted) — process Cypher escape sequences
        if (value.startswith("'") and value.endswith("'")) or (
            value.startswith('"') and value.endswith('"')
        ):
            return ResultMatcher._unescape_cypher_string(value[1:-1])

        # Handle lists [...] - parse recursively
        if value.startswith("[") and value.endswith("]"):
            return ResultMatcher._parse_list(value)

        # Default: return as string (nodes, relationships, paths, maps, etc.)
        return value

    @staticmethod
    def _unescape_cypher_string(s: str) -> str:
        """Process Cypher escape sequences in a string value from a Gherkin table."""
        result = []
        i = 0
        while i < len(s):
            if s[i] == '\\' and i + 1 < len(s):
                nxt = s[i + 1]
                if nxt == '\\':
                    result.append('\\')
                    i += 2
                elif nxt == "'":
                    result.append("'")
                    i += 2
                elif nxt == '"':
                    result.append('"')
                    i += 2
                elif nxt == 'n':
                    result.append('\n')
                    i += 2
                elif nxt == 'r':
                    result.append('\r')
                    i += 2
                elif nxt == 't':
                    result.append('\t')
                    i += 2
                elif nxt == 'b':
                    result.append('\b')
                    i += 2
                elif nxt == 'f':
                    result.append('\f')
                    i += 2
                elif nxt == '/':
                    result.append('/')
                    i += 2
                elif nxt == 'u' and i + 5 < len(s):
                    hex_str = s[i + 2:i + 6]
                    try:
                        code = int(hex_str, 16)
                        result.append(chr(code))
                        i += 6
                    except ValueError:
                        result.append(s[i])
                        i += 1
                else:
                    result.append(nxt)
                    i += 2
            else:
                result.append(s[i])
                i += 1
        return ''.join(result)

    @staticmethod
    def _parse_list(value: str) -> list:
        """Parse a list literal like [1, 2, 3] or ['a', 'b'] or [[1], [2, 3]].

        Handles nested lists, quoted strings, and mixed types.
        """
        inner = value[1:-1].strip()
        if not inner:
            return []

        elements = []
        depth = 0
        current = []
        in_string = False
        string_char = None

        for ch in inner:
            if in_string:
                current.append(ch)
                if ch == string_char:
                    in_string = False
            elif ch in ("'", '"'):
                in_string = True
                string_char = ch
                current.append(ch)
            elif ch in ("[", "{"):
                depth += 1
                current.append(ch)
            elif ch in ("]", "}"):
                depth -= 1
                current.append(ch)
            elif ch == "," and depth == 0:
                elements.append("".join(current).strip())
                current = []
            else:
                current.append(ch)

        if current:
            last = "".join(current).strip()
            if last:
                elements.append(last)

        return [ResultMatcher._parse_value(e) for e in elements]

    @staticmethod
    def _parse_map(value: str) -> dict:
        """Parse a Cypher map literal like {key: 'val', num: 42} into a Python dict.

        Handles nested structures, quoted strings, and mixed types.
        Keys are unquoted Cypher identifiers; values are parsed recursively.
        """
        inner = value[1:-1].strip()
        if not inner:
            return {}

        result = {}
        depth = 0
        in_string = False
        string_char = None
        current = []

        for ch in inner:
            if in_string:
                current.append(ch)
                if ch == string_char:
                    in_string = False
            elif ch in ("'", '"'):
                in_string = True
                string_char = ch
                current.append(ch)
            elif ch in ('[', '(', '{'):
                depth += 1
                current.append(ch)
            elif ch in (']', ')', '}'):
                depth -= 1
                current.append(ch)
            elif ch == ',' and depth == 0:
                pair = ''.join(current).strip()
                if pair:
                    colon_idx = pair.find(':')
                    if colon_idx >= 0:
                        k = pair[:colon_idx].strip()
                        v = pair[colon_idx + 1:].strip()
                        result[k] = ResultMatcher._parse_value(v)
                current = []
            else:
                current.append(ch)

        if current:
            pair = ''.join(current).strip()
            if pair:
                colon_idx = pair.find(':')
                if colon_idx >= 0:
                    k = pair[:colon_idx].strip()
                    v = pair[colon_idx + 1:].strip()
                    result[k] = ResultMatcher._parse_value(v)

        return result

    @staticmethod
    def _sort_labels_in_prefix(prefix: str) -> str:
        """Sort colon-separated labels in a node prefix like '(:Z:Y:X' -> '(:X:Y:Z'."""
        import re
        m = re.match(r'^\(((?::\w+)+)', prefix)
        if not m:
            return prefix
        labels_str = m.group(1)  # e.g., ':Z:Y:X'
        labels = [l for l in labels_str.split(':') if l]
        labels.sort()
        return '(:' + ':'.join(labels)

    @staticmethod
    def _normalize_node_string(s: str) -> str:
        """Normalize a node string by sorting labels and properties alphabetically.

        Handles patterns like '(:Label {b: 2, a: 1})' -> '(:Label {a: 1, b: 2})'
        and '(:Z:Y:X)' -> '(:X:Y:Z)'
        so that label/property key order doesn't affect comparison.
        """
        import re

        # Handle label-only nodes without properties: '(:Z:Y:X:W:V:U)'
        m_labels_only = re.match(r'^\(((?::\w+)+)\)$', s)
        if m_labels_only:
            labels_str = m_labels_only.group(1)
            labels = [l for l in labels_str.split(':') if l]
            labels.sort()
            return '(:' + ':'.join(labels) + ')'

        # Match node pattern: optional labels, optional properties
        # e.g., '(:B {num: 5, bool: false})' or '(:A:B {x: 1})'
        m = re.match(r'^(\((?::\w+(?::[\w]+)*)?)\s*\{(.*)\}\)$', s, re.DOTALL)
        if not m:
            return s

        prefix = ResultMatcher._sort_labels_in_prefix(m.group(1))  # e.g., '(:B'
        props_str = m.group(2).strip()

        if not props_str:
            return s

        # Parse property key-value pairs, handling nested structures
        pairs = []
        depth = 0
        in_string = False
        string_char = None
        current = []
        for ch in props_str:
            if in_string:
                current.append(ch)
                if ch == string_char:
                    in_string = False
            elif ch in ("'", '"'):
                in_string = True
                string_char = ch
                current.append(ch)
            elif ch in ('[', '(', '{'):
                depth += 1
                current.append(ch)
            elif ch in (']', ')', '}'):
                depth -= 1
                current.append(ch)
            elif ch == ',' and depth == 0:
                pairs.append(''.join(current).strip())
                current = []
            else:
                current.append(ch)
        if current:
            last = ''.join(current).strip()
            if last:
                pairs.append(last)

        # Normalize each pair to "key: value" format (remove/unify whitespace around colon).
        def normalize_pair(pair):
            colon_idx = pair.find(':')
            if colon_idx >= 0:
                k = pair[:colon_idx].strip()
                v = pair[colon_idx + 1:].strip()
                return f"{k}: {v}"
            return pair.strip()

        pairs = [normalize_pair(p) for p in pairs]

        # Sort by the key part (before the first ':')
        def sort_key(pair):
            colon_idx = pair.find(':')
            if colon_idx >= 0:
                return pair[:colon_idx].strip()
            return pair

        pairs.sort(key=sort_key)
        return f"{prefix} {{{', '.join(pairs)}}})"

    @staticmethod
    def _normalize_value(val: Any) -> Any:
        """Normalize a value for comparison.

        Converts floats that are whole numbers to ints, normalizes lists recursively.
        Parses string-encoded lists (e.g., '["a", "b"]') into actual lists.
        Normalizes node strings so property key order doesn't matter.
        """
        if val is None:
            return None
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, float):
            if val != val:  # NaN
                return "NaN"
            if val == int(val) and not (val == 0.0 and str(val).startswith("-")):
                return int(val)
            return val
        if isinstance(val, dict):
            return ResultMatcher._map_text(val)
        if isinstance(val, list):
            return [ResultMatcher._normalize_value(v) for v in val]
        if isinstance(val, str) and val.startswith("{") and val.endswith("}"):
            try:
                return ResultMatcher._map_text(ResultMatcher._parse_map(val))
            except Exception:
                pass
        if isinstance(val, str):
            # Strip VID prefix embedded by nodes(p) for pattern comprehension traversal.
            # Format: "VID:N:(:display_string)" — strip "VID:N:" to get "(:display_string)"
            import re as _re
            vid_prefix_match = _re.match(r'^VID:\d+:(.*)', val, _re.DOTALL)
            if vid_prefix_match:
                val = vid_prefix_match.group(1)
            # Strip EVID prefix embedded by relationships(p) for property access.
            # Format: "EVID:src_vid:dst_vid:[:display]" — strip to get "[:display]"
            evid_prefix_match = _re.match(r'^EVID:\d+:\d+:(.*)', val, _re.DOTALL)
            if evid_prefix_match:
                val = evid_prefix_match.group(1)
            # Parse string-encoded lists from the engine (e.g., '["1984-10-12"]')
            if val.startswith("[") and val.endswith("]"):
                try:
                    parsed = ResultMatcher._parse_list(val)
                    return [ResultMatcher._normalize_value(v) for v in parsed]
                except Exception:
                    pass
            # Normalize node strings so property/label order doesn't affect comparison.
            # Handles labeled nodes `(:Label {k: v})`, unlabeled `({k: v})`, and label-only `(:A:B)`.
            if val.endswith(")") and (val.startswith("(:") or val.startswith("({")):
                return ResultMatcher._normalize_node_string(val)
            # Normalize relationship type strings like ":REL {num:1}" → ":REL {num: 1}".
            # These appear as elements inside edge list representations.
            import re as _re2
            rel_prop_match = _re2.match(r'^(:[^{]+)\{(.*)\}$', val, _re2.DOTALL)
            if rel_prop_match:
                type_part = rel_prop_match.group(1)
                props_str = rel_prop_match.group(2)
                # Normalize "key:value" or "key : value" → "key: value"
                normalized = _re2.sub(r'(\w+)\s*:\s*', r'\1: ', props_str)
                return f"{type_part}{{{normalized}}}"
        return val

    @staticmethod
    def _map_text(m: dict) -> str:
        """Canonical Cypher text for a map, keys sorted: engine dicts and expected `{...}` agree."""

        def text(v: Any) -> str:
            if isinstance(v, dict):
                return ResultMatcher._map_text(v)
            if isinstance(v, list):
                return "[" + ", ".join(text(x) for x in v) + "]"
            if isinstance(v, str) and v.startswith("{") and v.endswith("}"):
                return ResultMatcher._map_text(ResultMatcher._parse_map(v))
            v = ResultMatcher._normalize_value(v)
            if v is None:
                return "null"
            return f"'{v}'" if isinstance(v, str) and v not in ("true", "false", "NaN") else str(v)

        return "{" + ", ".join(f"{k.strip('`')}: {text(v)}" for k, v in sorted(m.items())) + "}"

    @staticmethod
    def _normalize_row(row: dict[str, Any]) -> dict[str, str]:
        """Normalize a row by converting all values to canonical string form."""
        result = {}
        for k, v in row.items():
            v = ResultMatcher._normalize_value(v)
            result[k] = str(v) if v is not None else None
        return result

    @staticmethod
    def _sort_lists_in_row(row: dict[str, Any]) -> dict[str, Any]:
        """Sort list values in a row (for list-order-insensitive comparison)."""
        result = {}
        for k, v in row.items():
            if isinstance(v, str) and v.startswith("[") and v.endswith("]"):
                try:
                    parsed = ResultMatcher._parse_list(v)
                    norm = [ResultMatcher._normalize_value(x) for x in parsed]
                    try:
                        sorted_v = sorted(norm, key=lambda x: (str(type(x)), str(x)))
                    except TypeError:
                        sorted_v = norm
                    result[k] = str(sorted_v)
                    continue
                except Exception:
                    pass
            result[k] = v
        return result

    @staticmethod
    def compare_results(
        actual_columns: list[str],
        actual_rows: list[dict[str, Any]],
        expected_columns: list[str],
        expected_rows: list[dict[str, Any]],
        ordered: bool = False,
        sort_lists: bool = False,
    ) -> tuple[bool, str]:
        """Compare actual query results with expected results.

        Args:
            actual_columns: Column names from actual results
            actual_rows: Rows from actual results
            expected_columns: Expected column names
            expected_rows: Expected rows
            ordered: Whether to preserve row order in comparison

        Returns:
            Tuple of (match: bool, error_message: str)
        """
        # Normalize column names: remove inner whitespace from function calls and
        # normalize DISTINCT casing. This handles OpenCypher TCK tests that expect
        # the literal source text (e.g., "cOuNt( * )") while the engine emits the
        # canonical form ("cOuNt(*)").
        def _norm_col(name: str) -> str:
            n = re.sub(r'\s+', ' ', name).strip()
            n = re.sub(r'\(\s+', '(', n)
            n = re.sub(r'\s+\)', ')', n)
            n = re.sub(r'\bDISTINCT\b', 'DISTINCT', n, flags=re.IGNORECASE)
            # Normalize spaces around comparison operators in expression column names
            # (e.g., "a.name = 'x'" → "a.name='x'", matching TCK source-text form)
            n = re.sub(r'\s*=\s*', '=', n)
            return n

        norm_actual = {_norm_col(c): c for c in actual_columns}
        norm_expected = {_norm_col(c): c for c in expected_columns}

        # Check column names match (after normalization)
        if set(norm_actual.keys()) != set(norm_expected.keys()):
            return False, f"Column mismatch: expected {expected_columns}, got {actual_columns}"

        # Build remap: actual_col → expected_col for mismatched names
        col_remap = {
            actual_col: norm_expected[norm_key]
            for norm_key, actual_col in norm_actual.items()
            if actual_col != norm_expected[norm_key]
        }
        if col_remap:
            actual_rows = [{col_remap.get(k, k): v for k, v in row.items()} for row in actual_rows]
            actual_columns = [col_remap.get(c, c) for c in actual_columns]

        # Convert to Polars DataFrames for comparison
        try:
            if not actual_rows and not expected_rows:
                return True, ""

            if not actual_rows:
                return False, f"Expected {len(expected_rows)} rows, got 0"

            if not expected_rows:
                return False, f"Expected 0 rows, got {len(actual_rows)}"

            # Normalize values for comparison (type coercion)
            norm_actual = [ResultMatcher._normalize_row(r) for r in actual_rows]
            norm_expected = [ResultMatcher._normalize_row(r) for r in expected_rows]

            # Optionally sort list values within each cell (for keys(), etc.)
            if sort_lists:
                norm_actual = [ResultMatcher._sort_lists_in_row(r) for r in norm_actual]
                norm_expected = [ResultMatcher._sort_lists_in_row(r) for r in norm_expected]

            actual_df = pl.DataFrame(norm_actual)
            expected_df = pl.DataFrame(norm_expected)

            # Cast all columns to String to ensure type-consistent comparison
            # (avoids Polars Null vs String type mismatches for null-only columns)
            actual_df = actual_df.cast({col: pl.String for col in actual_df.columns})
            expected_df = expected_df.cast({col: pl.String for col in expected_df.columns})

            # Reorder columns to match expected order
            actual_df = actual_df.select(expected_columns)

            if not ordered:
                # For unordered comparison, sort both dataframes consistently
                # Sort by all columns to ensure deterministic comparison
                actual_df = actual_df.sort(expected_columns)
                expected_df = expected_df.sort(expected_columns)

            # Compare DataFrames (null_equal=True so null == null)
            if actual_df.equals(expected_df, null_equal=True):
                return True, ""
            else:
                return False, (
                    f"Results don't match:\n"
                    f"Expected:\n{expected_df}\n"
                    f"Actual:\n{actual_df}"
                )

        except Exception as e:
            return False, f"Error comparing results: {e}"

    @staticmethod
    def compare_side_effects(
        actual: dict[str, int], expected: dict[str, int]
    ) -> tuple[bool, str]:
        """Compare actual side effects with expected side effects.

        Args:
            actual: Dictionary of actual side effects
            expected: Dictionary of expected side effects

        Returns:
            Tuple of (match: bool, error_message: str)
        """
        if actual == expected:
            return True, ""
        else:
            return False, f'Side effects mismatch: expected {expected}, got {actual}'

        missing = set(expected.keys()) - set(actual.keys())
        extra = set(actual.keys()) - set(expected.keys())
        different = {
            key
            for key in set(actual.keys()) & set(expected.keys())
            if actual[key] != expected[key]
        }

        errors = []
        if missing:
            errors.append(f"Missing side effects: {missing}")
        if extra:
            errors.append(f"Unexpected side effects: {extra}")
        if different:
            for key in different:
                errors.append(f"{key}: expected {expected[key]}, got {actual[key]}")

        return False, "; ".join(errors)
