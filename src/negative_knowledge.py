"""
Negative knowledge base loader and processor.
Handles loading of toxic plant information and converting to document format.
"""
import json
import logging
import os
from typing import List, Dict, Any
from langchain_core.documents import Document

from src.config import NegativeKnowledgeConfig

logger = logging.getLogger(__name__)


def load_negative_knowledge() -> List[Document]:
    """
    Load negative knowledge from JSON files and convert to Document format.
    
    Returns:
        List of Document objects with negative knowledge and metadata
    """
    negative_data_path = NegativeKnowledgeConfig.NEGATIVE_DATA_PATH
    
    if not os.path.exists(negative_data_path):
        logger.warning(f"Negative knowledge directory not found: {negative_data_path}")
        return []
    
    documents = []
    
    # Process all JSON files in the negative knowledge directory
    for filename in os.listdir(negative_data_path):
        if not filename.endswith('.json'):
            continue
            
        filepath = os.path.join(negative_data_path, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert entries to documents
            entries = data.get('entries', [])
            source_name = data.get('metadata', {}).get('source_type', 'unknown')
            
            for entry in entries:
                doc = _convert_entry_to_document(entry, filename, source_name)
                documents.append(doc)
                
            logger.info(f"Loaded {len(entries)} entries from {filename}")
            
        except Exception as e:
            logger.error(f"Failed to load negative knowledge from {filename}: {e}")
    
    logger.info(f"Total negative knowledge documents loaded: {len(documents)}")
    return documents


def _convert_entry_to_document(entry: Dict[str, Any], source_file: str, source_type: str) -> Document:
    """
    Convert a negative knowledge entry to a Document with structured metadata.
    
    Args:
        entry: Single entry from negative knowledge JSON
        source_file: Name of the source file
        source_type: Type of source (e.g., 'authoritative_compilation')
    
    Returns:
        Document with page_content and metadata
    """
    # Build comprehensive text content for embedding
    content_parts = []
    
    # Basic identification
    if entry.get('plant_name'):
        content_parts.append(f"Plant: {entry['plant_name']}")
    if entry.get('scientific_name'):
        content_parts.append(f"Scientific name: {entry['scientific_name']}")
    if entry.get('common_names'):
        content_parts.append(f"Common names: {', '.join(entry['common_names'])}")
    
    # Safety information
    if entry.get('category'):
        content_parts.append(f"Category: {entry['category']}")
    if entry.get('safety_status'):
        content_parts.append(f"Safety status: {entry['safety_status']}")
    if entry.get('risk_level'):
        content_parts.append(f"Risk level: {entry['risk_level']}")
    
    # Toxicity details
    if entry.get('dangerous_parts'):
        content_parts.append(f"Dangerous parts: {', '.join(entry['dangerous_parts'])}")
    if entry.get('safe_parts'):
        content_parts.append(f"Safe parts: {', '.join(entry['safe_parts'])}")
    if entry.get('toxic_compounds'):
        content_parts.append(f"Toxic compounds: {', '.join(entry['toxic_compounds'])}")
    if entry.get('symptoms'):
        content_parts.append(f"Symptoms: {', '.join(entry['symptoms'])}")
    
    # Look-alike information
    if entry.get('dangerous_look_alikes'):
        content_parts.append(f"Dangerous look-alikes: {', '.join(entry['dangerous_look_alikes'])}")
    
    # Contraindications and warnings
    if entry.get('contraindications'):
        content_parts.append(f"Contraindications: {', '.join(entry['contraindications'])}")
    if entry.get('traditional_use_warning'):
        content_parts.append(f"Traditional use warning: {entry['traditional_use_warning']}")
    
    # Additional notes
    if entry.get('notes'):
        content_parts.append(f"Notes: {entry['notes']}")
    
    # For look-alike entries, include both plants
    if entry.get('safe_plant'):
        safe = entry['safe_plant']
        content_parts.append(f"Safe plant: {safe.get('name')} ({safe.get('scientific_name')})")
        if safe.get('identification_features'):
            content_parts.append(f"Safe plant features: {', '.join(safe['identification_features'])}")
    
    if entry.get('dangerous_plant'):
        dangerous = entry['dangerous_plant']
        content_parts.append(f"Dangerous plant: {dangerous.get('name')} ({dangerous.get('scientific_name')})")
        if dangerous.get('identification_features'):
            content_parts.append(f"Dangerous plant features: {', '.join(dangerous['identification_features'])}")
        if dangerous.get('toxicity'):
            content_parts.append(f"Toxicity: {dangerous['toxicity']}")
    
    # Join all parts
    page_content = '. '.join(content_parts)
    
    # Build structured metadata
    metadata = {
        NegativeKnowledgeConfig.NEGATIVE_METADATA_KEY: "safety_negative",
        'category': entry.get('category', 'unknown'),
        'safety_status': entry.get('safety_status', 'unknown'),
        'risk_level': entry.get('risk_level', 'unknown'),
        'plant_name': entry.get('plant_name', ''),
        'scientific_name': entry.get('scientific_name', ''),
        'source_file': source_file,
        'source_type': source_type,
        'evidence_quality': entry.get('evidence_quality', 'unknown'),
        'entry_id': entry.get('id', ''),
    }
    
    # Add optional metadata fields if present
    if entry.get('source'):
        metadata['source'] = entry['source']
    if entry.get('dangerous_parts'):
        metadata['dangerous_parts'] = ', '.join(entry['dangerous_parts'])
    if entry.get('safe_parts'):
        metadata['safe_parts'] = ', '.join(entry['safe_parts'])
    
    return Document(page_content=page_content, metadata=metadata)


def get_safety_metadata_filter() -> Dict[str, str]:
    """
    Get metadata filter for retrieving safety/negative knowledge from vector DB.
    
    Returns:
        Dictionary with metadata filter for safety documents
    """
    return {
        NegativeKnowledgeConfig.NEGATIVE_METADATA_KEY: "safety_negative"
    }


def get_medicinal_metadata_filter() -> Dict[str, str]:
    """
    Get metadata filter for retrieving medicinal knowledge from vector DB.
    
    Returns:
        Dictionary with metadata filter for medicinal documents
    """
    return {
        NegativeKnowledgeConfig.NEGATIVE_METADATA_KEY: "medicinal"
    }
