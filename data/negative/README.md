# Negative Knowledge Base for Phytobot

This directory contains structured negative knowledge data for plant safety and toxicity information.

## Purpose

The negative knowledge base provides authoritative information about:
- Toxic and poisonous plants
- Plants with specific toxic parts
- Dangerous look-alikes that can be confused with medicinal plants
- Contraindications and safety warnings
- Traditional use warnings

This data is used by Phytobot to provide safety-critical information and prevent unsafe recommendations.

## Structure

### Files

- `toxic_plants.json` - Comprehensive list of plants that are toxic or poisonous
- `toxic_parts.json` - Plants with specific toxic parts despite potential medicinal uses
- `look_alikes.json` - Plants with dangerous look-alikes that can cause confusion

### Metadata Schema

Each entry contains structured metadata:

```json
{
  "id": "unique_identifier",
  "category": "toxic_plant | toxic_parts | dangerous_look_alike",
  "safety_status": "unsafe | caution_required | high_risk_confusion",
  "risk_level": "critical | high | moderate | low",
  "plant_name": "Common name",
  "scientific_name": "Scientific name",
  "common_names": ["Alternative common names"],
  "dangerous_parts": ["List of toxic parts"],
  "toxic_compounds": ["Known toxic compounds"],
  "symptoms": ["Symptoms of toxicity"],
  "dangerous_look_alikes": ["Plants that can be confused with this one"],
  "contraindications": ["Specific contraindications"],
  "traditional_use_warning": "Warning about traditional use",
  "source": "Authoritative source",
  "source_type": "authoritative",
  "evidence_quality": "high | moderate | low",
  "notes": "Additional safety information"
}
```

## Sources

All data is sourced from authoritative organizations including:
- USDA Poisonous Plant Research Laboratory
- National Poisons Information Service (UK)
- Cornell University College of Veterinary Medicine
- World Health Organization
- European Medicines Agency
- Royal Botanic Gardens, Kew
- Food and Drug Administration (FDA)
- European Food Safety Authority (EFSA)
- National Institutes of Health (NIH)
- American Association of Poison Control Centers

## Important Notes

1. **No Invented Data**: All entries are based on documented, authoritative sources. No botanical facts are invented.

2. **Evidence Quality**: Each entry includes an `evidence_quality` field indicating the strength of evidence.

3. **Traditional Use Warnings**: Traditional use is distinguished from modern scientific evidence. Historical use does not imply safety.

4. **Updates**: This database should be reviewed and updated regularly with new safety information.

5. **Limitations**: This database is not exhaustive. Always err on the side of caution when dealing with plant identification and safety.

## Integration

The negative knowledge base is integrated into Phytobot's vector database with metadata tags that distinguish it from medicinal knowledge. This allows the system to:
- Retrieve safety evidence separately from medicinal evidence
- Apply deterministic safety rules before generating responses
- Prioritize safety warnings in the response structure

## Safety Principles

1. **Prefer Uncertainty**: When evidence is conflicting or insufficient, the system states uncertainty rather than making unsafe assumptions.

2. **Identification ≠ Safety**: Plant identification confidence is not used as a safety score. A plant can be identified with high confidence but still be unsafe.

3. **Mandatory Warnings**: Toxic evidence triggers mandatory safety warnings regardless of medicinal evidence.

4. **Expert Verification Required**: Plants with high toxicity or dangerous look-alikes require expert verification before any use recommendation.

## Version History

- v1.0 (2026-09-30): Initial negative knowledge base creation
