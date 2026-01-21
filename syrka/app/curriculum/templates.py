"""LangChain prompt templates for curriculum generation."""

CURRICULUM_SYSTEM_PROMPT = """You are an expert curriculum designer specializing in workforce development and vocational training.
Your role is to create comprehensive, industry-aligned curricula that prepare learners for real-world employment."""

MODULE_GENERATION_TEMPLATE = """Generate a curriculum module for the {sector} sector focusing on these skills: {skills}.

The module should include:
- Clear title and description
- Duration estimate (in hours)
- List of units to cover

Format as structured JSON."""

UNIT_GENERATION_TEMPLATE = """Create a detailed curriculum unit for: {topic}

Include:
- Title
- Competencies to develop
- Learning outcomes (using Bloom's taxonomy)
- Assessment criteria

Format as JSON."""

COMPETENCY_TEMPLATE = """Extract competencies from these skills for curriculum design: {skills}

For each competency provide:
- Name
- Description
- Proficiency level (Beginner/Intermediate/Advanced/Expert)"""

ASSESSMENT_TEMPLATE = """Design assessment criteria for this unit: {unit_title}

Competencies: {competencies}

Provide:
- Assessment type (Quiz/Project/Exam/Portfolio)
- Evaluation criteria
- Weightage
- Rubric guidelines"""

MICROCREDENTIAL_TEMPLATE = """Design a microcredential for skills: {skills}

Duration: {duration} hours

Include:
- Credential name
- Skills covered
- Badge criteria
- Assessment requirements"""
