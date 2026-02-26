# state.py file

from typing import Any
import operator 
from typing import Annotated, List, Dict, Optional, TypedDict


class ComplianceIssue(TypedDict):
    category: str #eg : FTC DIS
    severity: str # specific detail of violation
    description: str # critical | warning
    timestamp: Optional[str]

class VideoAuditState(TypedDict):
    """
    Define the data schema for langgraph execution content
    Main  container  : holds all the information about the audit 
    right from the initial URL to the final compliance report 
    
    """

    video_url : str
    video_id : str
    
    # Ingestion and extraction data

    local_file_path : Optional[str]
    video_metadata : Dict[str,Any]
    transcript : Optional[str]
    ocr_text : List[str]

    # analysis output
    # stores the list of all the violations found by AI 
    compliance_result : Annotated[List[ComplianceIssue],operator.add]
    
    # final deliverables:
    final_status : str  # PASS | FAIL | PENDING
    final_report : str # markdown format

    # system observability
    # errors : API timeout, system level errors
    errors : Annotated[List[str], operator.add]