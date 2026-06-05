from __future__ import annotations

import unittest

from examples.parsing import dedupe_examples, heuristic_extract_examples, parse_model_examples


class ExampleParsingTests(unittest.TestCase):
    def test_parse_model_examples_normalizes_json_fences_and_values(self):
        examples = parse_model_examples(
            '```json\n{"examples":[{"problem_text":"Find ﬁve",'
            '"solution_text":"It is 5","page_start":"2","confidence":2}]}\n```'
        )

        self.assertEqual(examples[0]["problem_text"], "Find five")
        self.assertEqual(examples[0]["page_start"], 2)
        self.assertEqual(examples[0]["confidence"], 1.0)

    def test_heuristic_parser_extracts_worked_example(self):
        pages = [{
            "page": 4,
            "text": (
                "Example 1 Calculate the total value after combining the two quantities "
                "shown in the problem statement.\n"
                "Solution Add the first quantity to the second quantity, simplify the "
                "result carefully, and verify it against the original givens."
            ),
        }]

        examples = heuristic_extract_examples(pages)

        self.assertEqual(len(examples), 1)
        self.assertEqual(examples[0]["page_start"], 4)

    def test_dedupe_examples_uses_normalized_problem_text(self):
        examples = dedupe_examples([
            {"problem_text": "Find x.", "solution_text": "x = 2"},
            {"problem_text": "Find x", "solution_text": "x equals two"},
        ])

        self.assertEqual(len(examples), 1)


if __name__ == "__main__":
    unittest.main()
