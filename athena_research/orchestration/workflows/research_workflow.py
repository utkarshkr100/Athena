from typing import Dict, List, Any, Optional
import asyncio
from ag2 import ConversableAgent, initiate_chats
from ...agents import (
    PlanningAgent, ResearchAgent, SectionWriterAgent, FinalWriterAgent,
    ResearchPlan, SectionContent
)
from ...data_sources import BaseSearchTool
from ...memory import MemoryManager
from ..tools.search_tools import AthenaSearchTools
from ..tools.memory_tools import AthenaMemoryTools
from ...config import settings

class AthenaResearchWorkflow:
    """Multi-agent research workflow orchestrated with AG2"""

    def __init__(
        self,
        search_tools: List[BaseSearchTool],
        memory_manager: Optional[MemoryManager] = None
    ):
        self.search_tools = search_tools
        self.memory_manager = memory_manager or MemoryManager()

        # Initialize tool wrappers
        self.search_tools_wrapper = AthenaSearchTools(search_tools)
        self.memory_tools_wrapper = AthenaMemoryTools(self.memory_manager)

        # Initialize agents
        self.planning_agent = self._create_planning_agent()
        self.research_agent = self._create_research_agent()
        self.section_writer_agent = self._create_section_writer_agent()
        self.final_writer_agent = self._create_final_writer_agent()
        self.user_proxy = self._create_user_proxy()

        # Store research state
        self.current_plan = None
        self.research_results = {}
        self.section_contents = []

    def _create_planning_agent(self) -> ConversableAgent:
        """Create AG2 planning agent"""
        return ConversableAgent(
            name="planning_agent",
            system_message="""You are a research planning expert. Your role is to:
1. Analyze research topics and create comprehensive research plans
2. Break down topics into logical sections
3. Generate targeted search queries for each section
4. Refine plans based on research findings

Always provide structured, actionable plans that guide the research process.""",
            llm_config={
                "config_list": [{
                    "model": settings.planning_model,
                    "temperature": settings.default_temperature,
                    "max_tokens": settings.max_tokens
                }]
            },
            tools=self.memory_tools_wrapper.get_tools(),
            human_input_mode="NEVER"
        )

    def _create_research_agent(self) -> ConversableAgent:
        """Create AG2 research agent"""
        all_tools = (
            self.search_tools_wrapper.get_tools() +
            self.memory_tools_wrapper.get_tools()
        )

        return ConversableAgent(
            name="research_agent",
            system_message="""You are a thorough research specialist. Your role is to:
1. Execute comprehensive searches using available tools
2. Gather high-quality information from multiple sources
3. Store important findings in memory for later reference
4. Evaluate source credibility and relevance
5. Provide detailed research summaries

Always prioritize accuracy and comprehensive coverage of research topics.""",
            llm_config={
                "config_list": [{
                    "model": settings.research_model,
                    "temperature": settings.default_temperature,
                    "max_tokens": settings.max_tokens
                }]
            },
            tools=all_tools,
            human_input_mode="NEVER"
        )

    def _create_section_writer_agent(self) -> ConversableAgent:
        """Create AG2 section writer agent"""
        return ConversableAgent(
            name="section_writer_agent",
            system_message="""You are an expert content writer specializing in research reports. Your role is to:
1. Transform research findings into well-structured sections
2. Create engaging, informative content that flows logically
3. Properly cite sources and maintain academic integrity
4. Adapt writing style to match report requirements
5. Ensure each section contributes meaningfully to the overall report

Focus on clarity, accuracy, and professional presentation.""",
            llm_config={
                "config_list": [{
                    "model": settings.writing_model,
                    "temperature": settings.default_temperature + 0.1,
                    "max_tokens": settings.max_tokens
                }]
            },
            tools=self.memory_tools_wrapper.get_tools(),
            human_input_mode="NEVER"
        )

    def _create_final_writer_agent(self) -> ConversableAgent:
        """Create AG2 final writer agent"""
        return ConversableAgent(
            name="final_writer_agent",
            system_message="""You are a report compilation expert. Your role is to:
1. Combine individual sections into a cohesive final report
2. Create executive summaries and abstracts
3. Ensure consistent formatting and style throughout
4. Generate proper citations and bibliographies
5. Add metadata and document structure
6. Perform final quality checks

Deliver polished, professional reports that meet high standards.""",
            llm_config={
                "config_list": [{
                    "model": settings.writing_model,
                    "temperature": settings.default_temperature,
                    "max_tokens": settings.max_tokens
                }]
            },
            tools=self.memory_tools_wrapper.get_tools(),
            human_input_mode="NEVER"
        )

    def _create_user_proxy(self) -> ConversableAgent:
        """Create user proxy agent"""
        return ConversableAgent(
            name="user_proxy",
            system_message="You coordinate the research workflow and communicate with users.",
            llm_config=False,  # No LLM needed for proxy
            human_input_mode="NEVER",
            code_execution_config=False
        )

    async def execute_research(
        self,
        topic: str,
        report_style: str = "comprehensive",
        user_requirements: str = ""
    ) -> Dict[str, Any]:
        """Execute the complete multi-agent research workflow"""

        try:
            # Phase 1: Planning
            print("Phase 1: Research Planning")
            plan_result = await self._execute_planning_phase(topic, report_style, user_requirements)

            if not plan_result["success"]:
                return {"success": False, "error": "Planning phase failed", "details": plan_result}

            # Phase 2: Research
            print("Phase 2: Information Gathering")
            research_result = await self._execute_research_phase(plan_result["plan"])

            if not research_result["success"]:
                return {"success": False, "error": "Research phase failed", "details": research_result}

            # Phase 3: Section Writing
            print("Phase 3: Content Creation")
            writing_result = await self._execute_writing_phase(
                plan_result["plan"],
                research_result["research_data"]
            )

            if not writing_result["success"]:
                return {"success": False, "error": "Writing phase failed", "details": writing_result}

            # Phase 4: Final Report Assembly
            print("Phase 4: Report Assembly")
            final_result = await self._execute_final_phase(
                topic,
                writing_result["sections"],
                report_style
            )

            return {
                "success": True,
                "report": final_result.get("report"),
                "metadata": {
                    "topic": topic,
                    "report_style": report_style,
                    "phases_completed": ["planning", "research", "writing", "assembly"],
                    "total_sources": sum(len(data.get("sources", [])) for data in research_result["research_data"].values()),
                    "total_sections": len(writing_result["sections"])
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Workflow execution failed: {str(e)}"
            }

    async def _execute_planning_phase(
        self,
        topic: str,
        report_style: str,
        user_requirements: str
    ) -> Dict[str, Any]:
        """Execute the planning phase"""
        try:
            # Create planning prompt
            planning_prompt = f"""
            Create a comprehensive research plan for the topic: "{topic}"

            Requirements:
            - Report style: {report_style}
            - User requirements: {user_requirements}
            - Create 4-6 main sections
            - Generate 2-4 specific search queries per section
            - Prioritize sections by importance

            Use the store_fact tool to save important planning decisions.
            """

            # Initiate planning conversation
            chat_result = initiate_chats([{
                "sender": self.user_proxy,
                "recipient": self.planning_agent,
                "message": planning_prompt,
                "max_turns": 3,
                "summary_method": "reflection_with_llm"
            }])

            # Extract plan from conversation (simplified - in practice would parse structured output)
            # For now, create a basic plan structure
            plan_sections = [
                {"title": f"Introduction to {topic}", "queries": [f"what is {topic}", f"{topic} definition"]},
                {"title": f"Current State of {topic}", "queries": [f"{topic} 2024", f"latest {topic} developments"]},
                {"title": f"Applications and Use Cases", "queries": [f"{topic} applications", f"{topic} examples"]},
                {"title": f"Future Outlook", "queries": [f"future of {topic}", f"{topic} predictions"]}
            ]

            plan = {
                "topic": topic,
                "sections": plan_sections,
                "report_style": report_style,
                "user_requirements": user_requirements
            }

            # Store plan in memory
            await self.memory_manager.store_plan(plan)

            return {"success": True, "plan": plan}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_research_phase(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the research phase"""
        try:
            research_data = {}

            # Create research tasks for each section
            for section in plan["sections"]:
                section_title = section["title"]
                queries = section["queries"]

                research_prompt = f"""
                Research the section: "{section_title}"

                Use these specific queries:
                {chr(10).join(f"- {query}" for query in queries)}

                Instructions:
                1. Use multi_source_search for comprehensive coverage
                2. Store important findings using store_fact
                3. Store valuable sources using store_source
                4. Focus on recent, credible information
                5. Gather at least 10 quality sources per section
                """

                # Execute research conversation
                chat_result = initiate_chats([{
                    "sender": self.user_proxy,
                    "recipient": self.research_agent,
                    "message": research_prompt,
                    "max_turns": 5,
                    "summary_method": "reflection_with_llm"
                }])

                # In a real implementation, would extract structured research data
                # For now, store basic research metadata
                research_data[section_title] = {
                    "queries_executed": queries,
                    "chat_summary": chat_result[0].summary if chat_result else "",
                    "sources": []  # Would be populated from actual research
                }

            return {"success": True, "research_data": research_data}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_writing_phase(
        self,
        plan: Dict[str, Any],
        research_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the section writing phase"""
        try:
            sections = []

            # Write each section
            for section_info in plan["sections"]:
                section_title = section_info["title"]
                section_research = research_data.get(section_title, {})

                writing_prompt = f"""
                Write a comprehensive section for: "{section_title}"

                Research context:
                - Queries executed: {section_research.get('queries_executed', [])}
                - Research summary: {section_research.get('chat_summary', '')}

                Instructions:
                1. Use retrieve_facts to get relevant stored facts
                2. Use retrieve_sources to get stored research sources
                3. Write 600-1000 words for this section
                4. Include proper citations
                5. Maintain {plan['report_style']} writing style
                6. Create engaging, informative content

                Focus on accuracy and comprehensive coverage.
                """

                # Execute writing conversation
                chat_result = initiate_chats([{
                    "sender": self.user_proxy,
                    "recipient": self.section_writer_agent,
                    "message": writing_prompt,
                    "max_turns": 4,
                    "summary_method": "reflection_with_llm"
                }])

                # Create section object (simplified)
                section = {
                    "title": section_title,
                    "content": chat_result[0].summary if chat_result else f"Content for {section_title}",
                    "word_count": 800,  # Would calculate actual count
                    "citations": []  # Would extract from content
                }

                sections.append(section)

            return {"success": True, "sections": sections}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_final_phase(
        self,
        topic: str,
        sections: List[Dict[str, Any]],
        report_style: str
    ) -> Dict[str, Any]:
        """Execute the final report assembly phase"""
        try:
            final_prompt = f"""
            Compile the final research report for: "{topic}"

            Sections to include:
            {chr(10).join(f"- {section['title']}" for section in sections)}

            Instructions:
            1. Create an executive summary
            2. Organize sections logically
            3. Generate a comprehensive bibliography
            4. Add proper formatting and metadata
            5. Ensure consistent style throughout
            6. Perform quality checks

            Report style: {report_style}
            Total sections: {len(sections)}
            """

            # Execute final assembly conversation
            chat_result = initiate_chats([{
                "sender": self.user_proxy,
                "recipient": self.final_writer_agent,
                "message": final_prompt,
                "max_turns": 3,
                "summary_method": "reflection_with_llm"
            }])

            # Create final report structure
            final_report = {
                "title": f"Research Report: {topic}",
                "executive_summary": f"Executive summary for {topic} research report.",
                "sections": sections,
                "bibliography": [],  # Would be populated from citations
                "metadata": {
                    "topic": topic,
                    "report_style": report_style,
                    "total_sections": len(sections),
                    "generated_by": "Athena Multi-Agent Research System"
                }
            }

            return {"success": True, "report": final_report}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def refine_research(
        self,
        feedback: str,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Refine research based on feedback"""
        # Implementation would handle iterative refinement
        pass

    async def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        return {
            "current_plan": self.current_plan,
            "research_progress": len(self.research_results),
            "sections_completed": len(self.section_contents),
            "memory_stats": await self.memory_manager.get_memory_stats()
        }