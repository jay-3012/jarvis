# layers/dialogue/clarification.py

import structlog
from typing import Optional, Dict, Any, List
from enum import Enum

logger = structlog.get_logger()

class AmbiguityType(Enum):
    """Types of ambiguity that can be detected"""
    MISSING_PARAMETER = "missing_parameter"      # "Open the file" - which file?
    MULTIPLE_MATCHES = "multiple_matches"        # "Email John" - which John?
    UNCLEAR_INTENT = "unclear_intent"            # "Do the thing" - what thing?
    MISSING_CONTEXT = "missing_context"          # "Continue" - continue what?
    VAGUE_REFERENCE = "vague_reference"          # "The meeting" - which one?
    TIME_AMBIGUITY = "time_ambiguity"            # "Delete old files" - how old?
    UNCLEAR_INTENT_LLM = "unclear_intent"        # Fallback for LLM custom

class AmbiguityDetection:
    """Result of ambiguity detection"""
    def __init__(
        self, 
        is_ambiguous: bool,
        ambiguity_type: Optional[AmbiguityType] = None,
        missing_info: Optional[str] = None,
        suggestions: Optional[List[str]] = None,
        clarifying_question: Optional[str] = None
    ):
        self.is_ambiguous = is_ambiguous
        self.ambiguity_type = ambiguity_type
        self.missing_info = missing_info
        self.suggestions = suggestions or []
        self.clarifying_question = clarifying_question

class ClarificationDetector:
    """
    Detects ambiguity in user requests and generates clarifying questions.
    Uses both rule-based and LLM-based detection.
    """
    
    # Rule-based ambiguity indicators
    VAGUE_TERMS = [
        "the file", "the document", "the folder", "the app", "the program",
        "the meeting", "the email", "the report", "the project", "the presentation",
        "the code", "the script", "the website", "the link", "the video",
        "it", "that", "this", "those", "them", "these"
    ]
    
    TEMPORAL_VAGUE = [
        "old files", "old", "recent", "recently", "yesterday", 
        "last week", "last month", "a while ago",
        "soon", "later", "earlier", "before", "after"
    ]
    
    INCOMPLETE_COMMANDS = [
        "open", "delete", "send", "move", "copy", "find", "search",
        "close", "run", "execute", "install", "remove", "start", "stop"
    ]

    COMPLEX_INDICATORS = [
        "about", "regarding", "concerning",  # "email about the meeting"
        "prepare for", "set up for", "get ready for",  # Complex workflows
        "multiple", "several", "some",  # Plural ambiguity
    ]
    
    def __init__(self, llm=None):
        self.llm = llm
        self.disambiguation_context: Dict[str, Any] = {}
    
    async def detect_ambiguity(
        self, 
        user_input: str,
        conversation_context: Optional[str] = None
    ) -> AmbiguityDetection:
        """
        Main entry point for ambiguity detection.
        Uses both rule-based and LLM-based approaches.
        """
        
        # 1. Rule-based quick checks (ALWAYS)
        rule_based = self._rule_based_detection(user_input)
        if rule_based.is_ambiguous:
            logger.info("Rule-based ambiguity detected", type=rule_based.ambiguity_type)
            return rule_based
        
        # 2. LLM-based deep analysis (ONLY IF COMPLEX)
        if self.llm and self._needs_llm_analysis(user_input):
            logger.debug("Complex request detected, using LLM analysis")
            llm_based = await self._llm_based_detection(user_input, conversation_context)
            if llm_based.is_ambiguous:
                logger.info("LLM-based ambiguity detected", type=llm_based.ambiguity_type)
                return llm_based
        else:
            logger.debug("Simple request, skipping LLM analysis")
        
        # 3. No ambiguity detected
        return AmbiguityDetection(is_ambiguous=False)

    def _needs_llm_analysis(self, user_input: str) -> bool:
        """Determine if input is complex enough to warrant LLM analysis"""
        user_lower = user_input.lower()
        
        # Skip LLM for simple, clear commands
        simple_patterns = [
            r'^open \w+$',           # "open notepad"
            r'^close \w+$',          # "close chrome"
            r'^run \w+$',            # "run script"
            r'^start \w+$',          # "start server"
        ]
        
        import re
        for pattern in simple_patterns:
            if re.match(pattern, user_lower):
                return False
        
        # Use LLM for complex indicators
        return any(indicator in user_lower for indicator in self.COMPLEX_INDICATORS)
     
    def _rule_based_detection(self, user_input: str) -> AmbiguityDetection:
        """
        Fast rule-based ambiguity detection.
        Checks for common patterns that indicate missing information.
        """
        user_lower = user_input.lower().strip()
        
        # Check for vague references
        for vague_term in self.VAGUE_TERMS:
            if vague_term in user_lower:
                return AmbiguityDetection(
                    is_ambiguous=True,
                    ambiguity_type=AmbiguityType.VAGUE_REFERENCE,
                    missing_info=vague_term,
                    clarifying_question=f"Which {vague_term.replace('the ', '')} do you mean?"
                )
        
        # Check for temporal vagueness
        for temporal in self.TEMPORAL_VAGUE:
            if temporal in user_lower:
                return AmbiguityDetection(
                    is_ambiguous=True,
                    ambiguity_type=AmbiguityType.TIME_AMBIGUITY,
                    missing_info=temporal,
                    clarifying_question=self._generate_time_clarification(temporal)
                )
        
        # Check for incomplete commands (single word commands)
        words = user_lower.split()
        if len(words) < 2 and words[0] in self.INCOMPLETE_COMMANDS:
            return AmbiguityDetection(
                is_ambiguous=True,
                ambiguity_type=AmbiguityType.MISSING_PARAMETER,
                missing_info=f"target for {words[0]}",
                clarifying_question=f"{words[0].capitalize()} what?"
            )
        
        return AmbiguityDetection(is_ambiguous=False)
    
    async def _llm_based_detection(
        self, 
        user_input: str,
        conversation_context: Optional[str] = None
    ) -> AmbiguityDetection:
        """
        Use LLM to detect subtle ambiguities and generate smart questions.
        IMPROVED: More robust JSON parsing and simpler prompt.
        """
        
        context_info = f"Recent conversation:\n{conversation_context}\n\n" if conversation_context else ""
        
        # SIMPLIFIED PROMPT - More direct
        prompt = f'''{context_info}Analyze this user request for ambiguity: "{user_input}"

Is this request clear and unambiguous? 

If NO (ambiguous), respond with JSON:
{{"is_ambiguous": true, "question": "What clarification should I ask?"}}

If YES (clear), respond with JSON:
{{"is_ambiguous": false}}

Examples:
"Open notepad" → {{"is_ambiguous": false}}
"Open the file" → {{"is_ambiguous": true, "question": "Which file?"}}
"Delete old files" → {{"is_ambiguous": true, "question": "How old?"}}
"Email John about the meeting" → {{"is_ambiguous": true, "question": "Which meeting and which John?"}}

Respond ONLY with JSON, nothing else.'''
        
        try:
            response = await self.llm.generate_response(prompt)
            
            # More aggressive JSON extraction
            import json
            import re
            
            # Try to extract JSON from anywhere in the response
            json_pattern = r'\{[^{}]*"is_ambiguous"[^{}]*\}'
            json_match = re.search(json_pattern, response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                
                if not data.get('is_ambiguous', False):
                    return AmbiguityDetection(is_ambiguous=False)
                
                # Simple format - just question
                question = data.get('question', 'Can you be more specific?')
                
                return AmbiguityDetection(
                    is_ambiguous=True,
                    ambiguity_type=AmbiguityType.UNCLEAR_INTENT,
                    clarifying_question=question
                )
            else:
                logger.warning("LLM didn't return valid JSON", response=response[:100])
                return AmbiguityDetection(is_ambiguous=False)
                
        except Exception as e:
            logger.error("LLM ambiguity detection failed", error=str(e))
            return AmbiguityDetection(is_ambiguous=False)

    def _generate_time_clarification(self, temporal_term: str) -> str:
        """Generate appropriate time-based clarification questions"""
        
        time_questions = {
            "old files": "How old should the files be? From last week, month, or year?",
            "recent": "How recent? From today, this week, or this month?",
            "yesterday": "Do you mean literally yesterday, or just recently?",
            "last week": "Do you mean the past 7 days, or the previous calendar week?",
            "a while ago": "How long ago? Days, weeks, or months?",
            "soon": "How soon? Within minutes, hours, or days?",
            "later": "When later? In an hour, today, or tomorrow?",
        }
        
        return time_questions.get(temporal_term, f"Can you be more specific about '{temporal_term}'?")
    
    async def generate_options_from_context(
        self, 
        ambiguity: AmbiguityDetection,
        context_data: Optional[Dict[str, Any]] = None
    ) -> AmbiguityDetection:
        """
        Enhance clarification with concrete options from context.
        For example, if asking "which file?", list recent files.
        """
        
        # This would integrate with actual system state
        # For now, just enhance the question with examples
        
        if ambiguity.ambiguity_type == AmbiguityType.VAGUE_REFERENCE:
            if "file" in ambiguity.missing_info:
                # In real implementation, would query recent files
                ambiguity.suggestions = ["document.txt", "report.pdf", "notes.md"]
                ambiguity.clarifying_question = (
                    f"Which file? Recent files include: {', '.join(ambiguity.suggestions)}"
                )
        
        return ambiguity

class DisambiguationState:
    """
    Tracks the state of an ongoing disambiguation dialogue.
    """
    def __init__(self, original_request: str, ambiguity: AmbiguityDetection):
        self.original_request = original_request
        self.ambiguity = ambiguity
        self.clarification_attempts = 0
        self.max_attempts = 3
        self.collected_info: Dict[str, Any] = {}
    
    def add_clarification(self, key: str, value: Any):
        """Store clarified information"""
        self.collected_info[key] = value
        self.clarification_attempts += 1
    
    def is_resolved(self) -> bool:
        """Check if we have enough information"""
        return bool(self.collected_info) and self.clarification_attempts <= self.max_attempts
    
    def get_resolved_request(self) -> str:
        """Reconstruct the original request with clarified information"""
        # Simple reconstruction - in practice, would be more sophisticated
        resolved = self.original_request
        for key, value in self.collected_info.items():
            resolved += f" ({key}: {value})"
        return resolved