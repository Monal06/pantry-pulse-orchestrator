from __future__ import annotations

import json
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from app.services import gemini_service, receipt_fallback_service


class ReceiptFallbackTests(IsolatedAsyncioTestCase):
    async def test_uses_gemini_when_successful(self) -> None:
        """Gemini executes successfully and returns valid JSON."""
        mock_response_json = {
            "items": [
                {
                    "name": "Milk",
                    "category": "dairy",
                    "quantity": 1,
                    "unit": "item",
                    "is_perishable": True,
                }
            ],
            "store_name": "Target",
            "date": "2026-04-10",
            "description": "Receipt parsed by Gemini",
        }
        
        with patch.object(gemini_service, "_generate_with_retry") as mock_gen:
            mock_gen.return_value = json.dumps(mock_response_json)
            with patch.object(receipt_fallback_service, "analyze_receipt_photo") as mock_fallback:
                result = await gemini_service.analyze_receipt_photo(b"image-bytes")

                self.assertEqual(result.get("extraction_source"), "gemini")
                self.assertEqual(len(result.get("items", [])), 1)
                self.assertFalse("fallback_reason" in result or result.get("fallback_reason") == "")
                mock_fallback.assert_not_called()

    async def test_falls_back_to_heuristic_when_gemini_fails(self) -> None:
        """Gemini throws exception → fallback heuristic parser is called."""
        with patch.object(gemini_service, "_generate_with_retry") as mock_gen:
            mock_gen.side_effect = RuntimeError("Gemini API unavailable")
            
            with patch.object(receipt_fallback_service, "analyze_receipt_photo") as mock_fallback:
                mock_fallback.return_value = {
                    "items": [
                        {
                            "name": "Bread",
                            "category": "bread",
                            "quantity": 1,
                            "unit": "item",
                            "is_perishable": True,
                        }
                    ],
                    "store_name": "Store",
                    "date": "",
                    "description": "Parsed by fallback heuristic",
                }
                
                result = await gemini_service.analyze_receipt_photo(b"image-bytes")
                
                self.assertEqual(result.get("extraction_source"), "fallback_heuristic")
                self.assertEqual(result.get("fallback_reason"), "gemini_failure")
                self.assertEqual(len(result.get("items", [])), 1)

    async def test_fallback_filters_ocr_noise_tokens(self) -> None:
        """Fallback parser should reject OCR junk like '7 A' while keeping plausible item names."""
        lines = [
            "7 A",
            "Awes 4.99 A",
            "H Milk 3.50 A",
            "Banana 1.20",
            "Aid A0000000041010 1.00",
            "Otal Includes 0.00",
            "Cl Eeard Toints 0.00",
            "Chocolate 2.99 A",
        ]

        items = receipt_fallback_service._extract_items(lines)
        names = [item["name"] for item in items]

        self.assertIn("H Milk", names)
        self.assertIn("Banana", names)
        self.assertIn("Chocolate", names)
        self.assertNotIn("7 A", names)
        self.assertNotIn("Awes", names)
        self.assertNotIn("Aid A0000000041010", names)
        self.assertNotIn("Otal Includes", names)
        self.assertNotIn("Cl Eeard Toints", names)

    async def test_falls_back_when_gemini_returns_invalid_json(self) -> None:
        """Gemini returns unparseable response → fallback parser handles it."""
        invalid_json = "Not valid JSON at all"
        
        with patch.object(gemini_service, "_generate_with_retry") as mock_gen:
            mock_gen.return_value = invalid_json
            
            with patch.object(receipt_fallback_service, "analyze_receipt_photo") as mock_fallback:
                mock_fallback.return_value = {
                    "items": [
                        {
                            "name": "Cheese",
                            "category": "dairy",
                            "quantity": 1,
                            "unit": "item",
                            "is_perishable": True,
                        }
                    ],
                    "store_name": "",
                    "date": "",
                    "description": "Parsed by fallback",
                }
                
                result = await gemini_service.analyze_receipt_photo(b"image-bytes")
                
                self.assertEqual(result.get("extraction_source"), "fallback_heuristic")
                self.assertEqual(result.get("fallback_reason"), "gemini_failure")
                self.assertEqual(len(result.get("items", [])), 1)
                mock_fallback.assert_called_once()
