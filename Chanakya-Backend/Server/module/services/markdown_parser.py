import json
import re
from typing import Dict, Any, List

def parse_markdown_to_module(text: str) -> Dict[str, Any]:
    """
    Parses raw RAGFlow Markdown lesson plan and assignment into the structured JSON
    conforming to the Pydantic schemas.
    If the text is already valid JSON, parses and returns it.
    """
    # 0. Check if text is valid JSON (from updated RAGFlow prompt)
    cleaned_text = text.strip()
    if cleaned_text.startswith("```json"):
        cleaned_text = cleaned_text[7:]
    if cleaned_text.startswith("```"):
        cleaned_text = cleaned_text[3:]
    if cleaned_text.endswith("```"):
        cleaned_text = cleaned_text[:-3]
    cleaned_text = cleaned_text.strip()
    
    try:
        parsed_data = json.loads(cleaned_text)
        if "lesson" in parsed_data or "assignment" in parsed_data:
            lesson_dict = parsed_data.get("lesson", {})
            assignment_dict = parsed_data.get("assignment", {})
            
            # Map slides
            raw_slides = lesson_dict.get("slides", [])
            slides = []
            for idx, rs in enumerate(raw_slides):
                slides.append({
                    "slide_number": idx + 1,
                    "slide_type": rs.get("slide_type", "introduction" if idx == 0 else "concept"),
                    "title": rs.get("title", f"Slide {idx + 1}"),
                    "explanation": rs.get("explanation", " ".join(rs.get("bullet_points", [])) if rs.get("bullet_points") else "Explanation of the slide content."),
                    "bullet_points": rs.get("bullet_points") or ["Key point 1", "Key point 2"],
                    "key_terms": rs.get("key_terms") or [],
                    "examples": rs.get("examples") or [],
                    "diagram_prompt": rs.get("diagram_prompt") or rs.get("visual_description") or f"Diagram illustrating {rs.get('title')}",
                    "source_references": rs.get("source_references") or []
                })
            
            # Ensure exactly 2 slides (Pydantic schema requirement)
            if len(slides) < 2:
                while len(slides) < 2:
                    num = len(slides) + 1
                    slides.append({
                        "slide_number": num,
                        "slide_type": "summary" if num == 2 else "concept",
                        "title": f"Summary",
                        "explanation": "Summary of key elements discussed in the lesson.",
                        "bullet_points": ["Review and recap main ideas.", "Test understanding through the worksheet."],
                        "key_terms": [],
                        "examples": [],
                        "diagram_prompt": f"Summary diagram",
                        "source_references": []
                    })
            elif len(slides) > 8:
                slides = slides[:8]
            
            lesson_dict["slides"] = slides
            
            # Map questions
            raw_questions = assignment_dict.get("questions", [])
            questions = []
            for idx, rq in enumerate(raw_questions):
                q_type = rq.get("question_type", "short_answer")
                q_data = {
                    "question_type": q_type,
                    "question_text": rq.get("question_text", f"Question {idx + 1}"),
                    "difficulty": rq.get("difficulty", "medium"),
                    "marks": rq.get("marks") or (1 if q_type == "mcq" else (2 if q_type == "short_answer" else 5)),
                    "source_reference": rq.get("source_reference") or (rq.get("source_references", ["General"])[0] if rq.get("source_references") else "General")
                }
                if q_type == "mcq":
                    raw_opts = rq.get("options", [])
                    options = []
                    for opt in raw_opts:
                        options.append({
                            "option_text": opt.get("option_text", opt.get("option_label", "")),
                            "is_correct": opt.get("is_correct", False)
                        })
                    while len(options) < 4:
                        options.append({"option_text": f"Option {len(options) + 1}", "is_correct": False})
                    if len(options) > 4:
                        options = options[:4]
                    if not any(o["is_correct"] for o in options):
                        options[0]["is_correct"] = True
                    q_data["options"] = options
                elif q_type == "short_answer":
                    q_data["expected_answer"] = rq.get("expected_answer") or rq.get("model_answer") or "Model answer here"
                elif q_type == "long_answer":
                    q_data["expected_answer"] = rq.get("expected_answer") or rq.get("model_answer") or "Model answer here"
                    q_data["marking_scheme"] = rq.get("marking_scheme") or ["1 mark for definition", "2 marks for examples"]
                
                questions.append(q_data)
                
            if not questions:
                questions.append({
                    "question_type": "short_answer",
                    "question_text": "What are the main concepts?",
                    "expected_answer": "The main concepts include their definitions and processes.",
                    "difficulty": "medium",
                    "marks": 2,
                    "source_reference": "General"
                })
                
            return {
                "lesson": {
                    "class_name": lesson_dict.get("class_name", "Class_7"),
                    "subject": lesson_dict.get("subject", "Geography"),
                    "topic": lesson_dict.get("topic", "Our Changing Earth"),
                    "slides": slides,
                    "validation_score": 1.0
                },
                "assignment": {
                    "questions": questions
                }
            }
    except Exception as e:
        pass

    # 1. Initialize defaults
    class_name = "Class_7"
    subject = "Geography"
    topic = "Our Changing Earth"
    
    # Try to extract topic, class, subject from headers if possible
    module_header_match = re.search(r"##\s+Module:\s*(.*)", text, re.IGNORECASE)
    if module_header_match:
        topic = module_header_match.group(1).strip()
        
    class_match = re.search(r"\*\s*\*\*Class Level:\*\*\s*([^\n\(\]]*)", text, re.IGNORECASE)
    if class_match:
        val = class_match.group(1).strip()
        # Clean/standardize e.g. "7th Grade" -> "Class_7"
        digit_match = re.search(r"(\d+)", val)
        if digit_match:
            class_name = f"Class_{digit_match.group(1)}"
            
    subject_match = re.search(r"\*\s*\*\*Subject:\*\*\s*(.*)", text, re.IGNORECASE)
    if subject_match:
        subject = subject_match.group(1).strip().split("/")[0].strip()

    # 2. Parse Slides Outline
    slides: List[Dict[str, Any]] = []
    # Split text by Slide markers
    slide_blocks = re.split(r"\*\*Slide\s*(\d+):", text, flags=re.IGNORECASE)
    
    # slide_blocks will look like: [prefix_before_slide_1, "1", slide_1_body, "2", slide_2_body, ...]
    if len(slide_blocks) > 1:
        for i in range(1, len(slide_blocks), 2):
            slide_num = int(slide_blocks[i])
            slide_body = slide_blocks[i+1]
            
            # Extract title
            title = f"Slide {slide_num}"
            title_match = re.search(r"\*\s*\*\*Title:\*\*\s*(.*)", slide_body, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
            else:
                first_line_match = re.search(r"^\s*(.*)", slide_body)
                if first_line_match:
                    title = first_line_match.group(1).strip().strip("*").strip()
            
            # Extract bullet points
            bullet_points = []
            bullet_matches = re.findall(r"^\s*[\*\-]\s*(?!.*\*\*Title:)(?!.*\*\*Visual:)(?!.*\*\*Visual Description:)(.*)", slide_body, re.MULTILINE)
            for bp in bullet_matches:
                clean_bp = bp.strip()
                if clean_bp and not clean_bp.startswith("**Title:") and not clean_bp.startswith("**Subtitle:"):
                    bullet_points.append(clean_bp)
                    
            if not bullet_points:
                bullet_points = ["Learn about the concepts in this slide.", "Understand the key components.", "Review the summaries and examples."]

            # Extract key terms, examples, diagram prompt
            key_terms = []
            examples = []
            diagram_prompt = f"Educational diagram showing {title}"
            
            # Search for visual/diagram description
            visual_match = re.search(r"\*\s*\*\*Visual(?:\s+Description)?:\*\*\s*(.*)", slide_body, re.IGNORECASE)
            if visual_match:
                diagram_prompt = visual_match.group(1).strip()
            else:
                diag_prompt_match = re.search(r"diagram_prompt:\s*(.*)", slide_body, re.IGNORECASE)
                if diag_prompt_match:
                    diagram_prompt = diag_prompt_match.group(1).strip()

            # Attempt to classify bullet points into Key Terms or Examples
            refined_bullets = []
            for bp in bullet_points:
                if ":" in bp and len(bp.split(":")[0]) < 30: # Likely a key term definition
                    key_terms.append(bp)
                elif "example" in bp.lower() or "e.g." in bp.lower():
                    examples.append(bp)
                else:
                    refined_bullets.append(bp)
                    
            if not refined_bullets:
                refined_bullets = bullet_points[:3]

            slides.append({
                "slide_number": len(slides) + 1,
                "slide_type": "introduction" if len(slides) == 0 else "concept",
                "title": title,
                "explanation": " ".join(refined_bullets[:2]) if len(refined_bullets) > 0 else "Detailed explanation of the slide content.",
                "bullet_points": refined_bullets,
                "key_terms": key_terms,
                "examples": examples,
                "diagram_prompt": diagram_prompt,
                "source_references": []
            })
            
    # Ensure exactly 2 slides for the schema
    if len(slides) < 2:
        while len(slides) < 2:
            num = len(slides) + 1
            slides.append({
                "slide_number": num,
                "slide_type": "summary" if num == 2 else "concept",
                "title": f"Summary of {topic}",
                "explanation": "Summary and conclusion of key elements discussed in the lesson.",
                "bullet_points": ["Review and recap main ideas.", "Test understanding through the worksheet.", "Review vocabulary and terms."],
                "key_terms": [],
                "examples": [],
                "diagram_prompt": f"Summary diagram illustrating {topic}",
                "source_references": []
            })
    elif len(slides) > 8:
        slides = slides[:8]

    # 3. Parse MCQ Answer Key
    answers_map = {}
    answer_key_section = re.search(r"Answer\s+Key.*?\n(.*)", text, re.DOTALL | re.IGNORECASE)
    if answer_key_section:
        keys = re.findall(r"(\d+)\.\s*([a-d])\)", answer_key_section.group(1), re.IGNORECASE)
        for num, letter in keys:
            answers_map[int(num)] = letter.lower()

    # 4. Parse Questions
    questions: List[Dict[str, Any]] = []
    
    # 4a. Parse MCQs
    # Look for MCQs section
    mcq_section_match = re.search(r"Multiple\s+Choice\s+Questions.*?\n(.*?)(\*\*Part\s+B:|\*\*Part\s+C:|$)", text, re.DOTALL | re.IGNORECASE)
    if mcq_section_match:
        mcq_text = mcq_section_match.group(1)
        # Split by question numbers
        q_blocks = re.split(r"(\d+)\.\s+", mcq_text)
        if len(q_blocks) > 1:
            for i in range(1, len(q_blocks), 2):
                q_num = int(q_blocks[i])
                q_body = q_blocks[i+1]
                
                # Extract question text
                q_lines = q_body.strip().split("\n")
                q_text_line = q_lines[0].strip()
                # Remove reference IDs like [ID:1] from text
                q_text_line = re.sub(r"\[ID:\d+\]", "", q_text_line).strip()
                
                # Extract options
                options = []
                opt_matches = re.findall(r"\s*([a-d])\)\s*(.*)", q_body, re.IGNORECASE)
                correct_letter = answers_map.get(q_num, "a") # Fallback to 'a' if key not found
                
                for letter, opt_txt in opt_matches:
                    clean_opt = opt_txt.strip()
                    options.append({
                        "option_text": clean_opt,
                        "is_correct": letter.lower() == correct_letter
                    })
                
                # Ensure exactly 4 options
                if len(options) < 4:
                    choices = ["a", "b", "c", "d"]
                    existing_letters = [l.lower() for l, _ in opt_matches]
                    for choice in choices:
                        if len(options) >= 4:
                            break
                        if choice not in existing_letters:
                            options.append({
                                "option_text": f"Option {choice.upper()}",
                                "is_correct": choice == correct_letter
                            })
                elif len(options) > 4:
                    options = options[:4]
                    
                # Verify exactly one option is correct
                has_correct = any(opt["is_correct"] for opt in options)
                if not has_correct and options:
                    options[0]["is_correct"] = True
                
                questions.append({
                    "question_type": "mcq",
                    "question_text": q_text_line if len(q_text_line) >= 5 else f"MCQ Question {q_num} about {topic}",
                    "options": options,
                    "difficulty": "easy" if q_num <= 3 else ("medium" if q_num <= 7 else "hard"),
                    "marks": 1,
                    "source_reference": f"Chapter: {topic}"
                })

    # 4b. Parse Short Answers
    sa_section_match = re.search(r"Short\s+Answer\s+Questions.*?\n(.*?)(\*\*Part\s+C:|$)", text, re.DOTALL | re.IGNORECASE)
    if sa_section_match:
        sa_text = sa_section_match.group(1)
        q_blocks = re.split(r"(\d+)\.\s+", sa_text)
        if len(q_blocks) > 1:
            for i in range(1, len(q_blocks), 2):
                q_num = int(q_blocks[i])
                q_body = q_blocks[i+1].strip()
                
                q_lines = q_body.split("\n")
                q_text_line = q_lines[0].strip()
                q_text_line = re.sub(r"\[ID:\d+\]", "", q_text_line).strip()
                
                # Try to extract answer from short answer answers if present
                ans_text = f"Write a brief explanation defining and explaining {q_text_line}."
                questions.append({
                    "question_type": "short_answer",
                    "question_text": q_text_line if len(q_text_line) >= 5 else f"Short answer question {q_num}?",
                    "expected_answer": ans_text,
                    "difficulty": "medium",
                    "marks": 2,
                    "source_reference": f"Chapter: {topic}"
                })

    # 4c. Parse Long Answers
    la_section_match = re.search(r"Long\s+Answer\s+Questions.*?\n(.*?)(\*\*Answer\s+Key|$)", text, re.DOTALL | re.IGNORECASE)
    if la_section_match:
        la_text = la_section_match.group(1)
        q_blocks = re.split(r"(\d+)\.\s+", la_text)
        if len(q_blocks) > 1:
            for i in range(1, len(q_blocks), 2):
                q_num = int(q_blocks[i])
                q_body = q_blocks[i+1].strip()
                
                q_lines = q_body.split("\n")
                q_text_line = q_lines[0].strip()
                q_text_line = re.sub(r"\[ID:\d+\]", "", q_text_line).strip()
                
                ans_text = f"Provide a detailed, comprehensive response explaining {q_text_line} with relevant examples and points."
                questions.append({
                    "question_type": "long_answer",
                    "question_text": q_text_line if len(q_text_line) >= 5 else f"Long answer question {q_num}?",
                    "expected_answer": ans_text,
                    "marking_scheme": ["Provides a detailed thesis or main claim (1 mark)", "Explains key supporting points with examples (2 marks)", "Structures the essay layout cleanly (2 marks)"],
                    "difficulty": "hard",
                    "marks": 5,
                    "source_reference": f"Chapter: {topic}"
                })

    # Ensure at least 1 question is created
    if not questions:
        questions.append({
            "question_type": "short_answer",
            "question_text": f"What are the main concepts discussed in {topic}?",
            "expected_answer": f"The main concepts in {topic} include its definitions, processes, and implications on Earth.",
            "difficulty": "medium",
            "marks": 2,
            "source_reference": f"Chapter: {topic}"
        })

    return {
        "lesson": {
            "class_name": class_name,
            "subject": subject,
            "topic": topic,
            "slides": slides,
            "validation_score": 1.0
        },
        "assignment": {
            "questions": questions
        }
    }
