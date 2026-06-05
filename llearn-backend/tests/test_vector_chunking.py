from __future__ import annotations

import unittest

from vector_db.chunking import build_page_chunks, chunk_text


class VectorChunkingTests(unittest.TestCase):
    def test_chunk_text_preserves_overlap(self):
        self.assertEqual(chunk_text("abcdefgh", chunk_size=5, overlap=2), ["abcde", "defgh", "gh"])

    def test_chunk_text_rejects_non_advancing_configuration(self):
        with self.assertRaises(ValueError):
            chunk_text("text", chunk_size=5, overlap=5)

    def test_build_page_chunks_keeps_page_metadata(self):
        chunks = build_page_chunks([{"page": 7, "text": "content"}], doc_id="doc")

        self.assertEqual(chunks, [{"text": "content", "doc_id": "doc", "page": 7}])


if __name__ == "__main__":
    unittest.main()
