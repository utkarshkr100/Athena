from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import json
from ..base_agent import BaseAgent, AgentResponse, AgentMessage
from ...config import settings

class ResearchSection(BaseModel):
    title: str
    description: str
    queries: List[str]
    priority: int = 1

class ResearchPlan(BaseModel):
    topic: str
    overview: str
    sections: List[ResearchSection]
    estimated_tokens: int
    report_type: str = "comprehensive"

class PlanningAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="PlanningAgent",
            model=settings.planning_model,
            temperature=settings.default_temperature
        )

    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        try:
            topic = input_data.get("topic", "")
            report_template = input_data.get("template", "comprehensive")
            user_requirements = input_data.get("requirements", "")

            plan = await self._generate_research_plan(topic, report_template, user_requirements)

            return AgentResponse(
                success=True,
                data=plan.dict(),
                sources=[]
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                data=None,
                error=str(e)
            )

    async def _generate_research_plan(
        self,
        topic: str,
        template: str,
        requirements: str
    ) -> ResearchPlan:
        planning_prompt = self._create_planning_prompt(topic, template, requirements)

        # Add message to conversation history
        self.add_message(AgentMessage(role="user", content=planning_prompt))

        # Generate plan using LLM
        try:
            llm_response = await self.generate_llm_response(
                prompt=planning_prompt,
                system_message="You are a research planning expert. Generate structured research plans in JSON format."
            )

            # Try to parse JSON response
            try:
                plan_data = json.loads(llm_response)
                plan = ResearchPlan(**plan_data)
            except (json.JSONDecodeError, TypeError, ValueError):
                # Fallback to structured plan if JSON parsing fails
                plan = await self._create_structured_plan(topic, template)
        except Exception as e:
            print(f"LLM generation failed, using fallback: {e}")
            plan = await self._create_structured_plan(topic, template)

        self.add_message(AgentMessage(role="assistant", content=json.dumps(plan.dict())))

        return plan

    def _create_planning_prompt(self, topic: str, template: str, requirements: str) -> str:
        return f"""
        You are a research planning expert. Create a comprehensive research plan for the following topic:

        TOPIC: {topic}
        TEMPLATE: {template}
        REQUIREMENTS: {requirements}

        Generate a structured plan that includes:
        1. An overview of the research approach
        2. 3-5 main sections with specific focus areas
        3. Targeted search queries for each section
        4. Priority levels for sections

        Format your response as a JSON structure with the following schema:
        {{
            "topic": "research topic",
            "overview": "research approach overview",
            "sections": [
                {{
                    "title": "section title",
                    "description": "what this section covers",
                    "queries": ["search query 1", "search query 2"],
                    "priority": 1-5
                }}
            ],
            "estimated_tokens": estimated_token_count,
            "report_type": "comprehensive|brief|detailed"
        }}
        """

    async def _create_structured_plan(self, topic: str, template: str) -> ResearchPlan:
        # This is a simplified version - in practice, this would call the LLM
        sections = [
            ResearchSection(
                title=f"Introduction to {topic}",
                description=f"Overview and background of {topic}",
                queries=[f"what is {topic}", f"{topic} definition", f"{topic} overview"],
                priority=1
            ),
            ResearchSection(
                title=f"Current State of {topic}",
                description=f"Current developments and trends in {topic}",
                queries=[f"{topic} 2024", f"latest {topic} developments", f"current {topic} trends"],
                priority=2
            ),
            ResearchSection(
                title=f"Applications and Use Cases",
                description=f"Practical applications and real-world use cases of {topic}",
                queries=[f"{topic} applications", f"{topic} use cases", f"{topic} examples"],
                priority=2
            ),
            ResearchSection(
                title=f"Future Outlook",
                description=f"Future trends and predictions for {topic}",
                queries=[f"future of {topic}", f"{topic} predictions", f"{topic} roadmap"],
                priority=3
            )
        ]

        return ResearchPlan(
            topic=topic,
            overview=f"Comprehensive research plan for {topic} covering current state, applications, and future outlook",
            sections=sections,
            estimated_tokens=8000,
            report_type=template
        )

    async def refine_plan(self, current_plan: ResearchPlan, feedback: str) -> ResearchPlan:
        """Refine the research plan based on feedback or intermediate results"""
        refinement_prompt = f"""
        Current research plan: {json.dumps(current_plan.dict(), indent=2)}

        Feedback/Issues: {feedback}

        Please refine the research plan addressing the feedback while maintaining the overall structure.
        """

        self.add_message(AgentMessage(role="user", content=refinement_prompt))

        # This would call the LLM to refine the plan
        # For now, return the current plan with minor adjustments
        refined_plan = current_plan.copy()
        refined_plan.overview += f" (Refined based on: {feedback[:100]}...)"

        return refined_plan