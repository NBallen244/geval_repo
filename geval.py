import argparse
import os
import glob
import time
import pandas as pd
import json
import re
from langchain_ollama import ChatOllama
from deepeval.models import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase
from deepeval.metrics import BaseMetric

# 1. Configurar Ollama como motor para DeepEval
class OllamaLocal(DeepEvalBaseLLM):
    def __init__(self, model_name="qwen2.5-coder:14b"):
        self.model = ChatOllama(
            model=model_name,
            temperature=0.0,
            num_ctx=4096 # Vital para no saturar la VRAM
        )

    def load_model(self):
        return self.model

    def generate(self, prompt: str) -> str:
        return self.model.invoke(prompt).content

    async def a_generate(self, prompt: str) -> str:
        res = await self.model.ainvoke(prompt)
        return res.content

    def get_model_name(self):
        return "Ollama Local"

# 2. Definir la Métrica Personalizada (Multitema + Puntaje Graduado)
class SDDClassificationMetric(BaseMetric):
    def __init__(self, model: DeepEvalBaseLLM):
        self.model = model
        self.evaluation_result = [] 
        self.score = 0.0
        self.success = False

    def measure(self, test_case: LLMTestCase):
        prompt = f"""
Act as an expert Software Engineering judge evaluating Spec-Driven Development (SDD) Markdown (.md) specification files (e.g., OpenSpec, Tessl, SpecKit, Kiro, BMAD Method).

Identify up to FIVE (5) predominant combinations of Knowledge Area (KA) and Main Topic in the document. Use EXCLUSIVELY the following strict taxonomy based on SWEBOK v4.0a (Chapters 1 to 15), using the subtopic breakdown in parentheses as technical disambiguation guidance:

1. Software Requirements
   - Requirements Fundamentals (Definition of Software Requirement, Software Product vs. Project Requirements, Functional Requirements, Nonfunctional Requirements, Technology Constraints, QoS Constraints, System vs. Software Requirements, Derived Requirements)
   - Requirements Elicitation (Requirements Sources, Stakeholder Analysis, Common Elicitation Techniques: Interviews, JAD/JRP, Prototyping, User Story Mapping)
   - Requirements Analysis (Basic Requirements Analysis, Economics of QoS Constraints, Formal Analysis, Addressing Conflict in Requirements, Product Family Development)
   - Requirements Specification (Unstructured/Structured Natural Language, Use Cases, User Stories, Acceptance Criteria-Based/ATDD/BDD, Model-Based Requirements Specification, Requirement Attributes)
   - Requirements Validation (Requirements Reviews, Simulation and Execution, Prototyping)
   - Requirements Management Activities (Requirements Scrubbing, Requirements Change Control, Scope Matching)
   - Practical Considerations (Iterative Nature, Requirements Prioritization/Kano Model, Requirements Tracing, Requirements Stability and Volatility, Measuring Requirements/FSM)
   - Software Requirements Tools (Requirements Management Tools, Requirements Modeling Tools, Functional Test Case Generation Tools)

2. Software Architecture
   - Software Architecture Fundamentals (Senses of Architecture, Stakeholders and Concerns, Uses of Architecture)
   - Software Architecture Description (Architecture Views and Viewpoints, Architecture Patterns and Styles, Reference Architectures, Architecture Description Languages/ADLs, Architecture Frameworks, Architecture as Significant Decisions/Rationale/Technical Debt)
   - Software Architecture Process (Architecture in Context: Agile/Enterprise/Product Lines, Architectural Design: ASRs/Synthesis/Evaluation, Architecture Practices/Methods/Tactics, Architecting in the Large)
   - Software Architecture Evaluation (Goodness in Architecture, Reasoning about Architectures, Architecture Reviews: ATAM/SAAM/QAW, Architecture Metrics)

3. Software Design
   - Software Design Fundamentals (Design Thinking, Context of Software Design, Key Issues in Software Design, Software Design Principles: Abstraction, Separation of Concerns, Modularization, Encapsulation, Coupling/Cohesion, Verifiability, Ethically Aligned Design)
   - Software Design Processes (High-Level Design, Detailed Design)
   - Software Design Qualities (Concurrency, Control and Event Handling, Data Persistence, Distribution of Components, Errors and Exception Handling, Fault Tolerance, Integration and Interoperability, Assurance/Security/Safety, Variability)
   - Recording Software Designs (Model-Based Design/MBD, Structural Design Descriptions: Class/Component/CRC/ERD/IDL, Behavioral Design Descriptions: Sequence/State/DFD/Activity, Design Patterns and Styles, Domain-Specific Languages/DSLs, Design Rationale)
   - Software Design Strategies and Methods (Function-Oriented/Structured, Data-Centered, Object-Oriented/SOLID, User-Centered, Component-Based/CBD, Event-Driven, Aspect-Oriented/AOD, Domain-Driven Design/DDD)
   - Software Design Quality Analysis and Evaluation (Design Reviews and Audits, Quality Attributes, Quality Analysis and Evaluation Techniques, Measures and Metrics, Verification/Validation/Certification)

4. Software Construction
   - Software Construction Fundamentals (Minimizing Complexity, Anticipating and Embracing Change, Constructing for Verification, Reusing Assets, Applying Standards in Construction)
   - Managing Construction (Construction in Life Cycle Models, Construction Planning, Construction Measurement, Managing Dependencies)
   - Practical Considerations (Construction Design, Construction Languages, Coding, Construction Testing, Reuse in Construction, Construction Quality, Integration/CI, Cross-Platform Development and Migration)
   - Construction Technologies (API Design and Use/OpenAPI, Object-Oriented Runtime Issues, Parameterization/Templates/Generics, Assertions/Design by Contract/Defensive Programming, Error/Exception Handling/Fault Tolerance, Executable Models/xUML/MDA, State-Based and Table-Driven Techniques, Runtime Configuration/Internationalization, Concurrency Primitives, Middleware, Distributed/Cloud-Based Software, Performance Analysis and Tuning, Test-First Programming/TDD)
   - Software Construction Tools (Development Environments/AI-Assisted IDEs, Visual Programming & Low-Code/Zero-Code, Unit Testing Tools, Profiling/Performance Analysis/Slicing Tools)

5. Software Testing
   - Software Testing Fundamentals (Faults vs. Failures, Key Issues: Test Case Creation, Test Selection/Adequacy, Prioritization/Minimization, Oracle Problem, Infeasible Paths, Testability, Scalability)
   - Test Levels (Target of the Test: Unit, Integration, System, Acceptance; Objectives of Testing: Conformance, Compliance, Installation, Alpha/Beta, Regression, Prioritization, Non-functional, Security, Privacy, API, Usability)
   - Test Techniques (Specification-Based: Equivalence Partitioning, Boundary Value Analysis, Syntax, Combinatorial, Decision Tables, Cause-Effect Graphing, State Transition, Scenario-Based, Random/Fuzzing; Structure-Based: Control Flow, Data Flow; Experience-Based: Error Guessing, Exploratory, Smoke/Quick; Fault-Based & Mutation; Usage-Based)
   - Test-Related Measures (Evaluation of the SUT: Fault Types/Density, Reliability Growth Models; Evaluation of Tests: Fault Injection, Mutation Score, Relative Effectiveness)
   - Test Process (Test Sub-Processes and Activities, Staffing)
   - Software Testing in Development Processes and Application Domains (Shift-Left, Application Domains)
   - Testing of and Testing Through Emerging Technologies (Testing AI/ML, Digital Twins)
   - Software Testing Tools (Testing Tool Support, Categories of Tools)

6. Software Engineering Operations
   - Software Engineering Operations Fundamentals (Definition, Operations Processes, Software Installation, Scripting and Automating, Troubleshooting, Performance/Reliability/Load Balancing)
   - Software Engineering Operations Planning (Operations Plan & Supplier Management, Environments, SLAs/Continuity, Capacity Management, Backup/Disaster Recovery, Safety/Security Controls)
   - Software Engineering Operations Delivery (Operational Testing/Acceptance, Deployment/Release Engineering, Rollback & Data Migration, Problem Resolution)
   - Software Engineering Operations Control (Incident Management, Change Management, Monitoring/Telemetry, Operations Support, Service Reporting)
   - Software Engineering Operations Tools (Containers & Virtualization, Deployment, Automated Test, Monitoring & Telemetry)

7. Software Maintenance
   - Software Maintenance Fundamentals (Definitions/Terminology, Nature/Need, Evolution of Software, Categories of Maintenance)
   - Key Issues in Software Maintenance (Technical Issues: Program Comprehension, Impact Analysis, Maintainability; Management Issues; Maintenance Costs/Technical Debt; Measurement)
   - Software Maintenance Processes (Maintenance Activities and Tasks)
   - Software Maintenance Techniques (Program Comprehension, Software Reengineering, Reverse Engineering, CI/CD Integration, Visualizing Maintenance)
   - Software Maintenance Tools

8. Software Configuration Management
   - Management of the SCM Process (Organizational Context, Constraints, Planning for SCM, SCM Plan, Monitoring)
   - Software Configuration Identification (Identifying SCIs, Baselines, Identifiers & Attributes, Software Libraries)
   - Software Configuration Change Control (Change Requests/SCR, CCB, Implementing Changes, Deviations & Waivers)
   - Software Configuration Status Accounting (Status Information, Status Reporting)
   - Software Configuration Auditing (Functional Configuration Audit/FCA, Physical Configuration Audit/PCA)
   - Software Release Management and Delivery (Software Building, Release Management)
   - Software Configuration Management Tools

9. Software Engineering Management
   - Initiation and Scope Definition (Determination & Negotiation of Requirements, Feasibility Analysis)
   - Software Project Planning (Process Planning, Cost/Effort/Schedule Estimation, Resource Allocation, Risk Management)
   - Software Project Execution (Implementation of Plans, Supplier Management, Measurement Process, Control & Reporting)
   - Software Review and Evaluation (Determining Satisfaction of Requirements, Performance Evaluation)
   - Closure (Determining Closure, Closure Activities)
   - Software Engineering Measurement (Measurement Process Planning & Execution)
   - Software Engineering Management Tools

10. Software Engineering Process
    - Software Engineering Process Fundamentals (Process Definition, Infrastructure)
    - Life Cycles (Process Models vs. Life Cycle Models, Software Life Cycle Adaptation/Tailoring)
    - Software Process Assessment and Improvement (Overview, GQM, Frameworks: CMMI/SPICE, Agile Improvement)

11. Software Engineering Models and Methods
    - Modeling (Modeling Principles, Expression of Models, Syntax/Semantics, Pre/Postconditions & Invariants)
    - Types of Models (Structural Modeling, Behavioral Modeling)
    - Analysis of Models (Completeness, Consistency, Correctness, Traceability, Interaction)
    - Software Engineering Methods (Heuristic Methods, Formal Methods, Prototyping Methods, Agile Methods)

12. Software Quality
    - Software Quality Fundamentals (Culture & Ethics, Value & Costs of Quality, Standards/Certifications, Dependability & Integrity Levels)
    - Software Quality Management Process (Quality Improvement, Quality Management Planning, Measurement, Defect Characterization)
    - Software Quality Assurance Process (SQA, Process/Product Assurance, V&V, Static Analysis, Technical Reviews & Audits)
    - Software Quality Tools

13. Software Security
    - Software Security Fundamentals (Software Security, Information Security, Cybersecurity)
    - Security Management and Organization (CMM, ISMS, Agile Practices for Security)
    - Software Security Engineering and Processes (Security SDLC, Common Criteria/ISO 15408)
    - Security Engineering for Software Systems (Security Requirements, Security Design, Security Patterns, Construction for Security, Security Testing, Vulnerability Management)
    - Software Security Tools (Vulnerability Checking, Penetration Testing Tools)
    - Domain-Specific Software Security (Container & Cloud Security, IoT Security, ML-Based Application Security)

14. Software Engineering Professional Practice
    - Professionalism (Accreditation, Certification, Licensing, Codes of Ethics, Standards, Legal Issues: IP/Privacy/Cybercrime, Trade-Off Analysis)
    - Group Dynamics and Psychology (Team Dynamics, Individual Cognition, Dealing with Uncertainty, Diversity & Inclusivity)
    - Communication Skills (Reading/Writing, Team Communication, Presentation Skills)

15. Software Engineering Economics
    - Software Engineering Economics Fundamentals (Proposals, Cash Flow, Time-Value of Money, Intangible Assets, Business Models)
    - The Engineering Decision-Making Process (Problem Definition, Feasible Solutions, Selection Criteria, Monitoring)
    - For-Profit & Nonprofit Decision-Making (MARR, Benefit-Cost Analysis, Cost-Effectiveness Analysis)
    - Estimation (Expert Judgment, Analogy, Decomposition, Parametric Estimation)
    - Practical Considerations (Business Case, Multiple-Currency Analysis, Systems Thinking)

CRITICAL RULE: Ignore the application's domain or specific business case (e.g., Tetris, Calculator, Banking, E-commerce). Focus strictly on the technical intent, structure, syntax, and software engineering artifacts present in the document.

For each identified element (up to 5), assign an "alignment" from 1 to 10 based on this rubric:
- 9 to 10: Total focus. The document almost entirely centers on this topic/KA.
- 7 to 8: Major presence. Extensive and detailed sections dedicated to this topic.
- 4 to 6: Secondary presence. Clear code blocks, diagrams, or schemas exist, but it shares focus with other topics.
- 1 to 3: Minor mention. Touched upon very superficially or marginally.

DOCUMENT:
{test_case.input}

Return ONLY a valid JSON object containing an array named "classifications". Sort the array from highest to lowest "alignment". Do not include any extra text outside the JSON object.

Exact example structure:
{{
  "classifications": [
    {{"KA": "Software Design", "topic": "Recording Software Designs", "alignment": 9}},
    {{"KA": "Software Requirements", "topic": "Requirements Specification", "alignment": 8}},
    {{"KA": "Software Testing", "topic": "Test Techniques", "alignment": 6}},
    {{"KA": "Software Architecture", "topic": "Architecture Description", "alignment": 4}},
    {{"KA": "Software Construction", "topic": "Practical Considerations", "alignment": 2}}
  ]
}}
"""
        
        response = self.model.generate(prompt)
        
        try:
            cleaned_response = re.sub(r"^```(?:json)?\s*|\s*```$", "", response.strip(), flags=re.IGNORECASE)
            match = re.search(r"\{.*\}", cleaned_response, re.DOTALL)
            parsed = json.loads(match.group(0) if match else cleaned_response)
            classifications = parsed.get("classifications", [])
            normalized = []
            for item in classifications:
                ka = str(item.get("KA", "")).strip()
                topic = str(item.get("topic", "")).strip()
                try:
                    alignment = int(item.get("alignment"))
                except (TypeError, ValueError):
                    continue
                if ka and topic and 1 <= alignment <= 10:
                    normalized.append({"KA": ka, "topic": topic, "alignment": alignment})

            self.evaluation_result = normalized
            self.score = 1.0 if normalized else 0.0
            self.success = bool(normalized)
        except (json.JSONDecodeError, AttributeError, TypeError, ValueError) as error:
            print(f"Could not parse model response: {error}")
            self.evaluation_result = []
            self.score = 0.0
            self.success = False

        return self.score
    def is_successful(self):
        return self.success

    @property
    def name(self):
        return "SWEBOK Knowledge Area and Topic Alignment"

# 3. Ejecutar el Pipeline de Evaluación
def ejecutar_analisis(modelo, tiempo_limite_minutos=0):
    tools = ["speckit", "openspec", "kiro", "tessl", "bmad_method"]
    stages_root = "testing_files"
    reports_root = "reports"
    stages = sorted(
        entry.name for entry in os.scandir(stages_root)
        if entry.is_dir() and entry.name.lower().startswith("etapa_")
    ) if os.path.isdir(stages_root) else []

    if not stages:
        print(f"No stage folders found in '{stages_root}'.")
        return

    os.makedirs(reports_root, exist_ok=True)
    local_llm = OllamaLocal(model_name=modelo)
    sdd_metric = SDDClassificationMetric(model=local_llm)
    time_limit_seconds = tiempo_limite_minutos * 60 if tiempo_limite_minutos > 0 else None
    start_time = time.monotonic()

    def save_stage_report(stage, results):
        columns = ["tool", "KA", "topic", "alignment"]
        records = pd.DataFrame(results, columns=columns)
        report_path = os.path.join(reports_root, f"{stage}.xlsx")

        if records.empty:
            ka_weights = pd.DataFrame(columns=["tool", "KA", "alignment", "weight_percent"])
            topic_weights = pd.DataFrame(columns=["tool", "KA", "topic", "alignment", "weight_percent"])
        else:
            ka_weights = (
                records.groupby(["tool", "KA"], as_index=False)["alignment"]
                .sum()
            )
            ka_totals = ka_weights.groupby("tool")["alignment"].transform("sum")
            ka_weights["weight_percent"] = (ka_weights["alignment"] / ka_totals * 100).round(2)
            ka_weights = ka_weights.sort_values(
                ["tool", "weight_percent", "KA"], ascending=[True, False, True]
            ).reset_index(drop=True)

            topic_weights = (
                records.groupby(["tool", "KA", "topic"], as_index=False)["alignment"]
                .sum()
            )
            topic_totals = topic_weights.groupby("tool")["alignment"].transform("sum")
            topic_weights["weight_percent"] = (topic_weights["alignment"] / topic_totals * 100).round(2)
            topic_weights = topic_weights.sort_values(
                ["tool", "weight_percent", "KA", "topic"], ascending=[True, False, True, True]
            ).reset_index(drop=True)

        with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
            records.to_excel(writer, sheet_name="Records", index=False)
            ka_weights.to_excel(writer, sheet_name="KA Weights", index=False)
            topic_weights.to_excel(writer, sheet_name="Topic Weights", index=False)
        print(f"Stage report saved: {report_path}")
    for stage in stages:
        stage_results = []
        print(f"\nProcessing {stage}...")
        try:
            for tool in tools:
                tool_root = os.path.join(stages_root, stage, tool)
                markdown_files = sorted(glob.glob(os.path.join(tool_root, "**", "*.md"), recursive=True))

                for file_path in markdown_files:
                    if time_limit_seconds is not None and time.monotonic() - start_time >= time_limit_seconds:
                        print(f"Time limit reached; saving partial results for {stage}.")
                        break

                    with open(file_path, "r", encoding="utf-8") as source:
                        content = source.read()[:8000]
                    if not content.strip():
                        continue

                    print(f"Evaluating [{tool}] {file_path}")
                    test_case = LLMTestCase(input=content, actual_output="N/A")
                    sdd_metric.measure(test_case)
                    for classification in sdd_metric.evaluation_result:
                        stage_results.append({
                            "tool": tool,
                            "KA": classification["KA"],
                            "topic": classification["topic"],
                            "alignment": classification["alignment"],
                        })
                    # Save after each file so interrupted runs keep completed work.
                    save_stage_report(stage, stage_results)

                if time_limit_seconds is not None and time.monotonic() - start_time >= time_limit_seconds:
                    break
        except KeyboardInterrupt:
            print(f"\nInterrupted; saving partial results for {stage}.")
        finally:
            save_stage_report(stage, stage_results)

        if time_limit_seconds is not None and time.monotonic() - start_time >= time_limit_seconds:
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate SDD specification Markdown files by stage and tool.")
    parser.add_argument("--model", default="qwen2.5-coder:14b", help="Ollama model name (default: qwen2.5-coder:14b).")
    parser.add_argument("--time-limit-minutes", type=float, default=0, help="Optional total runtime limit; 0 means unlimited.")
    args = parser.parse_args()
    ejecutar_analisis(args.model, args.time_limit_minutes)








