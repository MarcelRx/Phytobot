"""
Tests for negative knowledge base loader.
Tests Phase 2 negative knowledge JSON loading and conversion.
"""
import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document
from src.negative_knowledge import load_negative_knowledge, _convert_entry_to_document, get_safety_metadata_filter, get_medicinal_metadata_filter
from src.config import NegativeKnowledgeConfig


class TestNegativeKnowledgeLoading:
    """Test negative knowledge loading from JSON files."""
    
    def test_load_negative_knowledge_directory_not_found(self):
        """Test loading when negative knowledge directory doesn't exist."""
        with patch('src.negative_knowledge.NegativeKnowledgeConfig') as mock_config:
            mock_config.NEGATIVE_DATA_PATH = "/nonexistent/path"
            
            docs = load_negative_knowledge()
            
            assert docs == []
    
    def test_load_negative_knowledge_success(self, tmp_path):
        """Test successful loading of negative knowledge."""
        # Create test JSON file
        test_file = tmp_path / "test_toxic.json"
        test_data = {
            "metadata": {
                "version": "1.0",
                "source_type": "authoritative_compilation"
            },
            "entries": [
                {
                    "id": "test_plant_1",
                    "category": "toxic_plant",
                    "safety_status": "unsafe",
                    "risk_level": "high",
                    "plant_name": "Test Plant",
                    "scientific_name": "Testus toxicus",
                    "common_names": ["Test", "Toxic Test"],
                    "dangerous_parts": ["leaves", "roots"],
                    "toxic_compounds": ["toxin"],
                    "symptoms": ["nausea"],
                    "dangerous_look_alikes": ["Safe Plant"],
                    "contraindications": ["never use"],
                    "traditional_use_warning": "Not safe",
                    "source": "Test Source",
                    "source_type": "authoritative",
                    "evidence_quality": "high",
                    "notes": "Test notes"
                }
            ]
        }
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        with patch('src.negative_knowledge.NegativeKnowledgeConfig') as mock_config:
            mock_config.NEGATIVE_DATA_PATH = str(tmp_path)
            
            docs = load_negative_knowledge()
            
            assert len(docs) == 1
            assert isinstance(docs[0], Document)
            assert "Test Plant" in docs[0].page_content
            assert docs[0].metadata['plant_name'] == "Test Plant"
            assert docs[0].metadata['risk_level'] == "high"
    
    def test_load_negative_knowledge_multiple_files(self, tmp_path):
        """Test loading from multiple JSON files."""
        # Create test files
        file1 = tmp_path / "toxic_plants.json"
        file2 = tmp_path / "toxic_parts.json"
        
        data1 = {
            "metadata": {"source_type": "authoritative"},
            "entries": [{"id": "1", "category": "toxic_plant", "safety_status": "unsafe", "risk_level": "high", "plant_name": "Plant1"}]
        }
        
        data2 = {
            "metadata": {"source_type": "authoritative"},
            "entries": [{"id": "2", "category": "toxic_parts", "safety_status": "caution_required", "risk_level": "moderate", "plant_name": "Plant2"}]
        }
        
        with open(file1, 'w') as f:
            json.dump(data1, f)
        with open(file2, 'w') as f:
            json.dump(data2, f)
        
        with patch('src.negative_knowledge.NegativeKnowledgeConfig') as mock_config:
            mock_config.NEGATIVE_DATA_PATH = str(tmp_path)
            
            docs = load_negative_knowledge()
            
            assert len(docs) == 2
    
    def test_load_negative_knowledge_non_json_files_ignored(self, tmp_path):
        """Test that non-JSON files are ignored."""
        # Create a JSON file and a non-JSON file
        json_file = tmp_path / "test.json"
        txt_file = tmp_path / "test.txt"
        
        with open(json_file, 'w') as f:
            json.dump({"metadata": {}, "entries": []}, f)
        
        with open(txt_file, 'w') as f:
            f.write("Not a JSON file")
        
        with patch('src.negative_knowledge.NegativeKnowledgeConfig') as mock_config:
            mock_config.NEGATIVE_DATA_PATH = str(tmp_path)
            
            docs = load_negative_knowledge()
            
            # Should only load the JSON file (with 0 entries)
            assert len(docs) == 0


class TestEntryConversion:
    """Test conversion of JSON entries to Document objects."""
    
    def test_convert_toxic_plant_entry(self):
        """Test conversion of toxic plant entry."""
        entry = {
            "id": "test_1",
            "category": "toxic_plant",
            "safety_status": "unsafe",
            "risk_level": "critical",
            "plant_name": "Oleander",
            "scientific_name": "Nerium oleander",
            "common_names": ["Rose Bay"],
            "dangerous_parts": ["all_parts"],
            "toxic_compounds": ["oleandrin"],
            "symptoms": ["cardiac arrest"],
            "contraindications": ["never use"],
            "traditional_use_warning": "Highly toxic",
            "source": "Test Source",
            "evidence_quality": "high",
            "notes": "Very dangerous"
        }
        
        doc = _convert_entry_to_document(entry, "test.json", "authoritative_compilation")
        
        assert isinstance(doc, Document)
        assert "Oleander" in doc.page_content
        assert "Nerium oleander" in doc.page_content
        assert "oleandrin" in doc.page_content
        assert doc.metadata['category'] == "toxic_plant"
        assert doc.metadata['risk_level'] == "critical"
        assert doc.metadata['safety_status'] == "unsafe"
        assert doc.metadata['plant_name'] == "Oleander"
        assert doc.metadata['source_file'] == "test.json"
    
    def test_convert_toxic_parts_entry(self):
        """Test conversion of toxic parts entry."""
        entry = {
            "id": "test_2",
            "category": "toxic_parts",
            "safety_status": "caution_required",
            "risk_level": "moderate",
            "plant_name": "Rhubarb",
            "scientific_name": "Rheum rhabarbarum",
            "dangerous_parts": ["leaves"],
            "safe_parts": ["stems"],
            "toxic_compounds": ["oxalic acid"],
            "contraindications": ["kidney disease"],
            "traditional_use_warning": "Leaves are toxic",
            "source": "Test Source",
            "evidence_quality": "high"
        }
        
        doc = _convert_entry_to_document(entry, "test.json", "authoritative_compilation")
        
        assert isinstance(doc, Document)
        assert "Rhubarb" in doc.page_content
        assert "leaves" in doc.page_content
        assert "stems" in doc.page_content
        assert doc.metadata['category'] == "toxic_parts"
        assert doc.metadata['safe_parts'] == "stems"
    
    def test_convert_look_alike_entry(self):
        """Test conversion of dangerous look-alike entry."""
        entry = {
            "id": "test_3",
            "category": "dangerous_look_alike",
            "safety_status": "high_risk_confusion",
            "risk_level": "critical",
            "safe_plant": {
                "name": "Wild Carrot",
                "scientific_name": "Daucus carota",
                "identification_features": ["hairy stem", "purple center"]
            },
            "dangerous_plant": {
                "name": "Poison Hemlock",
                "scientific_name": "Conium maculatum",
                "identification_features": ["smooth stem", "purple spots"],
                "toxicity": "fatal"
            },
            "confusion_risk": "high",
            "traditional_use_warning": "Fatal confusion",
            "source": "Test Source",
            "evidence_quality": "high"
        }
        
        doc = _convert_entry_to_document(entry, "test.json", "authoritative_compilation")
        
        assert isinstance(doc, Document)
        assert "Wild Carrot" in doc.page_content
        assert "Poison Hemlock" in doc.page_content
        assert "Daucus carota" in doc.page_content
        assert "Conium maculatum" in doc.page_content
        assert "fatal" in doc.page_content
        assert doc.metadata['category'] == "dangerous_look_alike"
    
    def test_convert_minimal_entry(self):
        """Test conversion with minimal required fields."""
        entry = {
            "id": "test_4",
            "category": "toxic_plant",
            "safety_status": "unsafe",
            "risk_level": "high",
            "plant_name": "Test"
        }
        
        doc = _convert_entry_to_document(entry, "test.json", "authoritative_compilation")
        
        assert isinstance(doc, Document)
        assert "Test" in doc.page_content
        assert doc.metadata['category'] == "toxic_plant"
        assert doc.metadata['plant_name'] == "Test"


class TestMetadataFilters:
    """Test metadata filter generation."""
    
    def test_get_safety_metadata_filter(self):
        """Test safety metadata filter generation."""
        with patch('src.negative_knowledge.NegativeKnowledgeConfig') as mock_config:
            mock_config.NEGATIVE_METADATA_KEY = "knowledge_type"
            
            filter_dict = get_safety_metadata_filter()
            
            assert filter_dict == {"knowledge_type": "safety_negative"}
    
    def test_get_medicinal_metadata_filter(self):
        """Test medicinal metadata filter generation."""
        with patch('src.negative_knowledge.NegativeKnowledgeConfig') as mock_config:
            mock_config.NEGATIVE_METADATA_KEY = "knowledge_type"
            
            filter_dict = get_medicinal_metadata_filter()
            
            assert filter_dict == {"knowledge_type": "medicinal"}
