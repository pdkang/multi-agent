import os
import unittest
from pathlib import Path
from src.document_processor import DocumentProcessor

class TestDocumentProcessor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create test directory
        cls.test_dir = Path("tests/test_data")
        cls.test_dir.mkdir(exist_ok=True)
        
        # Create a simple PDF for testing
        pdf_path = cls.test_dir / "sample.pdf"
        if not pdf_path.exists():
            import fitz
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((50, 50), "This is a test PDF document.")
            doc.save(str(pdf_path))
            doc.close()
        cls.sample_pdf = str(pdf_path)
        
        # Initialize processor
        cls.processor = DocumentProcessor()

    def test_extract_text(self):
        """Test PDF text extraction"""
        text = self.processor.extract_text(self.sample_pdf)
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 0)
        self.assertIn("test PDF document", text)

    def test_split_text(self):
        """Test text splitting"""
        text = "This is a test document. " * 10  # Create a longer text
        chunks = self.processor.split_text(text)
        
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)
        self.assertTrue(all(isinstance(chunk, str) for chunk in chunks))
        self.assertTrue(all(len(chunk) <= 1000 for chunk in chunks))  # Default chunk size

    def test_get_metadata(self):
        """Test metadata extraction"""
        metadata = self.processor.get_metadata(self.sample_pdf)
        
        self.assertIsInstance(metadata, dict)
        self.assertIn("filename", metadata)
        self.assertIn("page_count", metadata)
        self.assertEqual(metadata["filename"], "sample.pdf")

    def test_process_document(self):
        """Test document processing and vector storage"""
        # Process document
        self.processor.process_document(self.sample_pdf)
        
        # Test search
        query = "test PDF document"
        results = self.processor.search(query, k=1)
        
        self.assertEqual(len(results), 1)
        self.assertIn("test PDF document", results[0]["text"])
        self.assertEqual(results[0]["source"], "sample.pdf")

    def test_error_handling(self):
        """Test error handling for invalid files"""
        # Test with non-existent file
        with self.assertRaises(Exception):
            self.processor.process_document("nonexistent.pdf")
        
        # Test with invalid PDF
        invalid_pdf = self.test_dir / "invalid.pdf"
        with open(invalid_pdf, "w") as f:
            f.write("This is not a PDF")
        
        with self.assertRaises(Exception):
            self.processor.process_document(str(invalid_pdf))

    def test_end_to_end_10k_processing(self):
        """Test end-to-end processing of actual 10-K documents"""
        # Process Uber 10-K
        pdf_path = Path("10-K/Uber-2021-Annual-Report.pdf")
        if pdf_path.exists():
            self.processor.process_document(str(pdf_path))
            
            # Test search functionality
            test_queries = [
                "What is Uber's revenue in 2021?",
                "What are Uber's main business segments?",
                "What are the key risks to Uber's business?"
            ]
            
            for query in test_queries:
                results = self.processor.search(query, k=3)
                self.assertEqual(len(results), 3)
                self.assertTrue(all(isinstance(result, dict) for result in results))
                self.assertTrue(all("text" in result for result in results))
                self.assertTrue(all("source" in result for result in results))
                self.assertTrue(all("metadata" in result for result in results))

if __name__ == '__main__':
    unittest.main() 