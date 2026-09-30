"""
Tests for safety decision layer.
Tests Phase 2 negative knowledge and safety decision logic.
"""
import pytest
from unittest.mock import MagicMock
from src.safety_decision import SafetyDecision, make_safety_decision, check_for_conflicts, format_safety_response
from src.config import SafetyConfig


class TestSafetyDecision:
    """Test safety decision logic."""
    
    def test_safety_decision_no_evidence(self):
        """Test safety decision with no evidence."""
        decision = make_safety_decision([], [], None, None)
        
        assert not decision.is_safe
        assert decision.requires_warning
        assert "No reliable evidence" in decision.warning_message
        assert decision.risk_level == "unknown"
    
    def test_safety_decision_low_identification_confidence(self):
        """Test safety decision with low identification confidence."""
        decision = make_safety_decision(
            [MagicMock()],
            [MagicMock()],
            identification_confidence=0.50,
            plant_name="Test Plant"
        )
        
        assert not decision.is_safe
        assert decision.requires_warning
        assert "identification confidence is low" in decision.warning_message.lower()
    
    def test_safety_decision_critical_toxicity(self):
        """Test safety decision with critical toxicity evidence."""
        safety_doc = MagicMock()
        safety_doc.metadata = {
            'category': 'toxic_plant',
            'risk_level': 'critical',
            'safety_status': 'unsafe'
        }
        
        decision = make_safety_decision(
            [safety_doc],
            [MagicMock()],
            identification_confidence=0.95,
            plant_name="Oleander"
        )
        
        assert not decision.is_safe
        assert decision.requires_warning
        assert "CRITICAL TOXICITY WARNING" in decision.warning_message
        assert decision.risk_level == "critical"
    
    def test_safety_decision_high_toxicity(self):
        """Test safety decision with high toxicity evidence."""
        safety_doc = MagicMock()
        safety_doc.metadata = {
            'category': 'toxic_plant',
            'risk_level': 'high',
            'safety_status': 'unsafe'
        }
        
        decision = make_safety_decision(
            [safety_doc],
            [MagicMock()],
            identification_confidence=0.95,
            plant_name="Foxglove"
        )
        
        assert not decision.is_safe
        assert decision.requires_warning
        assert "TOXICITY WARNING" in decision.warning_message
        assert decision.risk_level == "high"
    
    def test_safety_decision_dangerous_look_alike(self):
        """Test safety decision with dangerous look-alike evidence."""
        safety_doc = MagicMock()
        safety_doc.metadata = {
            'category': 'dangerous_look_alike',
            'risk_level': 'high',
            'safety_status': 'high_risk_confusion'
        }
        
        decision = make_safety_decision(
            [safety_doc],
            [MagicMock()],
            identification_confidence=0.95,
            plant_name="Wild Carrot"
        )
        
        assert not decision.is_safe
        assert decision.requires_warning
        assert "DANGEROUS LOOK-ALIKE WARNING" in decision.warning_message
    
    def test_safety_decision_caution_required(self):
        """Test safety decision with caution required status."""
        safety_doc = MagicMock()
        safety_doc.metadata = {
            'category': 'toxic_parts',
            'risk_level': 'moderate',
            'safety_status': 'caution_required'
        }
        
        decision = make_safety_decision(
            [safety_doc],
            [MagicMock()],
            identification_confidence=0.95,
            plant_name="Rhubarb"
        )
        
        assert not decision.is_safe
        assert decision.requires_warning
        assert "CAUTION REQUIRED" in decision.warning_message
    
    def test_safety_decision_medicinal_only(self):
        """Test safety decision with only medicinal evidence (no safety evidence)."""
        medicinal_doc = MagicMock()
        medicinal_doc.metadata = {'source_type': 'authoritative_pdf'}
        
        decision = make_safety_decision(
            [],
            [medicinal_doc],
            identification_confidence=0.95,
            plant_name="Ginger"
        )
        
        assert not decision.is_safe  # Default to unsafe without safety evidence
        assert decision.requires_warning
        assert "LIMITED SAFETY INFORMATION" in decision.warning_message
    
    def test_safety_decision_medicinal_and_safe(self):
        """Test safety decision with medicinal and safe safety evidence."""
        medicinal_doc = MagicMock()
        medicinal_doc.metadata = {'source_type': 'authoritative_pdf'}
        
        safety_doc = MagicMock()
        safety_doc.metadata = {
            'category': 'general_safety',
            'risk_level': 'low',
            'safety_status': 'safe'
        }
        
        decision = make_safety_decision(
            [safety_doc],
            [medicinal_doc],
            identification_confidence=0.95,
            plant_name="Chamomile"
        )
        
        assert decision.is_safe
        assert not decision.requires_warning


class TestConflictDetection:
    """Test conflict detection between safety and medicinal evidence."""
    
    def test_no_conflict_no_safety_docs(self):
        """Test conflict detection with no safety documents."""
        has_conflict, desc = check_for_conflicts([], [MagicMock()])
        
        assert not has_conflict
        assert desc == ""
    
    def test_no_conflict_no_medicinal_docs(self):
        """Test conflict detection with no medicinal documents."""
        has_conflict, desc = check_for_conflicts([MagicMock()], [])
        
        assert not has_conflict
        assert desc == ""
    
    def test_conflict_toxicity_with_medicinal(self):
        """Test conflict detection when toxicity exists with medicinal evidence."""
        safety_doc = MagicMock()
        safety_doc.metadata = {'category': 'toxic_plant'}
        
        has_conflict, desc = check_for_conflicts(
            [safety_doc],
            [MagicMock()]
        )
        
        assert has_conflict
        assert "Conflict detected" in desc
        assert "toxicity concerns" in desc.lower()
    
    def test_no_conflict_safe_with_medicinal(self):
        """Test no conflict when safety evidence is safe."""
        safety_doc = MagicMock()
        safety_doc.metadata = {'category': 'general_safety'}
        
        has_conflict, desc = check_for_conflicts(
            [safety_doc],
            [MagicMock()]
        )
        
        assert not has_conflict
        assert desc == ""


class TestSafetyResponseFormatting:
    """Test safety response formatting."""
    
    def test_format_with_plant_name(self):
        """Test formatting with plant name."""
        decision = SafetyDecision(
            is_safe=False,
            requires_warning=True,
            warning_message="Test warning",
            risk_level="high",
            confidence="moderate"
        )
        
        response = format_safety_response(
            decision,
            [MagicMock()],
            [MagicMock()],
            plant_name="Test Plant"
        )
        
        assert "Test Plant" in response
        assert "Test warning" in response
        assert "HIGH" in response
    
    def test_format_without_plant_name(self):
        """Test formatting without plant name."""
        decision = SafetyDecision(
            is_safe=False,
            requires_warning=True,
            warning_message="Test warning",
            risk_level="unknown",
            confidence="low"
        )
        
        response = format_safety_response(
            decision,
            [],
            []
        )
        
        assert "Test warning" in response
        assert "Risk Level" in response
    
    def test_format_with_conflict(self):
        """Test formatting with conflict warning."""
        decision = SafetyDecision(
            is_safe=False,
            requires_warning=True,
            warning_message="Test warning",
            risk_level="high",
            confidence="moderate"
        )
        
        safety_doc = MagicMock()
        safety_doc.metadata = {'category': 'toxic_plant'}
        
        response = format_safety_response(
            decision,
            [safety_doc],
            [MagicMock()],
            plant_name="Test Plant"
        )
        
        assert "CONFLICT WARNING" in response


class TestNegativeTestCases:
    """Comprehensive test cases for Phase 2 safety scenarios."""
    
    def test_case_a_known_medicinal_plant(self):
        """Case A: Known medicinal plant with positive evidence."""
        medicinal_doc = MagicMock()
        medicinal_doc.metadata = {'source_type': 'authoritative_pdf'}
        
        safety_doc = MagicMock()
        safety_doc.metadata = {
            'category': 'general_safety',
            'risk_level': 'low',
            'safety_status': 'safe'
        }
        
        decision = make_safety_decision(
            [safety_doc],
            [medicinal_doc],
            identification_confidence=0.95,
            plant_name="Chamomile"
        )
        
        assert decision.is_safe
        assert not decision.requires_warning
    
    def test_case_b_known_poisonous_plant(self):
        """Case B: Known poisonous plant with negative evidence."""
        safety_doc = MagicMock()
        safety_doc.metadata = {
            'category': 'toxic_plant',
            'risk_level': 'critical',
            'safety_status': 'unsafe'
        }
        
        decision = make_safety_decision(
            [safety_doc],
            [],  # No medicinal evidence
            identification_confidence=0.95,
            plant_name="Oleander"
        )
        
        assert not decision.is_safe
        assert decision.requires_warning
        assert "CRITICAL" in decision.warning_message
    
    def test_case_c_plant_with_both_medicinal_and_toxicity(self):
        """Case C: Plant with both medicinal and toxicity information."""
        medicinal_doc = MagicMock()
        medicinal_doc.metadata = {'source_type': 'authoritative_pdf'}
        
        safety_doc = MagicMock()
        safety_doc.metadata = {
            'category': 'toxic_plant',
            'risk_level': 'high',
            'safety_status': 'unsafe'
        }
        
        decision = make_safety_decision(
            [safety_doc],
            [medicinal_doc],
            identification_confidence=0.95,
            plant_name="Foxglove"
        )
        
        assert not decision.is_safe
        assert decision.requires_warning
        assert decision.risk_level == "high"
        
        # Check conflict detection
        has_conflict, _ = check_for_conflicts([safety_doc], [medicinal_doc])
        assert has_conflict
    
    def test_case_d_unknown_plant(self):
        """Case D: Unknown plant."""
        decision = make_safety_decision(
            [],  # No safety evidence
            [],  # No medicinal evidence
            identification_confidence=0.95,
            plant_name="Unknown Plant"
        )
        
        assert not decision.is_safe
        assert decision.requires_warning
        assert "No reliable evidence" in decision.warning_message
    
    def test_case_e_low_confidence_identification(self):
        """Case E: Low-confidence plant identification."""
        medicinal_doc = MagicMock()
        medicinal_doc.metadata = {'source_type': 'authoritative_pdf'}
        
        decision = make_safety_decision(
            [],
            [medicinal_doc],
            identification_confidence=0.60,  # Below threshold
            plant_name="Test Plant"
        )
        
        assert not decision.is_safe
        assert decision.requires_warning
        assert "identification confidence is low" in decision.warning_message.lower()
    
    def test_case_f_medicinal_plant_with_dangerous_look_alike(self):
        """Case F: Medicinal plant with a dangerous look-alike."""
        medicinal_doc = MagicMock()
        medicinal_doc.metadata = {'source_type': 'authoritative_pdf'}
        
        safety_doc = MagicMock()
        safety_doc.metadata = {
            'category': 'dangerous_look_alike',
            'risk_level': 'high',
            'safety_status': 'high_risk_confusion'
        }
        
        decision = make_safety_decision(
            [safety_doc],
            [medicinal_doc],
            identification_confidence=0.95,
            plant_name="Wild Carrot"
        )
        
        assert not decision.is_safe
        assert decision.requires_warning
        assert "DANGEROUS LOOK-ALIKE" in decision.warning_message
    
    def test_case_g_no_safety_evidence_retrieved(self):
        """Case G: Vector retrieval returns no safety evidence."""
        medicinal_doc = MagicMock()
        medicinal_doc.metadata = {'source_type': 'authoritative_pdf'}
        
        decision = make_safety_decision(
            [],  # No safety evidence retrieved
            [medicinal_doc],
            identification_confidence=0.95,
            plant_name="Test Plant"
        )
        
        assert not decision.is_safe
        assert decision.requires_warning
        assert "LIMITED SAFETY INFORMATION" in decision.warning_message
    
    def test_case_h_safety_retrieval_service_fails(self):
        """Case H: Safety retrieval service fails (simulated by empty lists)."""
        # In a real scenario, this would be caught by the retrieval function
        # Here we test the decision logic with no evidence
        decision = make_safety_decision(
            [],  # Safety retrieval failed
            [],  # Medicinal retrieval also failed
            identification_confidence=0.95,
            plant_name="Test Plant"
        )
        
        assert not decision.is_safe
        assert decision.requires_warning
        assert "No reliable evidence" in decision.warning_message
