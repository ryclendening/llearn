# lLearn Project Ideas

This is the persistent backlog for project ideas explicitly requested by the
project owner.

## Improve Student User Experience

- Create a clear student dashboard showing active classes, current objectives, assignments, and progress.
- Make the tutoring interface easier to navigate with suggested prompts, clear next actions, and visible session goals.
- Provide immediate, encouraging feedback that explains mistakes without overwhelming the student.
- Let students control pacing, request different explanations, and choose between hints, examples, and concept reviews.
- Improve mobile responsiveness, loading states, error recovery, keyboard navigation, and screen-reader accessibility.
- Preserve session context so students can leave and resume learning without losing their place.
- Test workflows with students and measure task completion, engagement, confusion points, and learning outcomes.

## Improve Streaming Text Functionality With LLM Chat

- Stream tutor responses incrementally from the LLM through the backend to the frontend.
- Render partial text smoothly without duplicating, reordering, or dropping tokens.
- Support stopping generation and clearly indicate when a response is generating, complete, or failed.
- Preserve citations, markdown, equations, and formatting while content is still streaming.
- Handle reconnects, timeouts, provider errors, and interrupted streams without losing conversation state.
- Measure time to first token, total response time, rendering performance, and perceived responsiveness.

## Improve Guardrail Enforcement To Prevent Answer Leakage

- Detect when tutor responses directly reveal protected answers, decisive final steps, or equivalent paraphrases.
- Validate generated responses against protected examples before returning them to students.
- Regenerate or replace unsafe responses with hints, guiding questions, or concept explanations.
- Prevent answer leakage across multi-turn conversations, citations, retrieved context, and streaming output.
- Add adversarial tests for direct requests, prompt injection, indirect requests, and answer-confirmation attempts.
- Measure guardrail accuracy, false refusals, tutoring usefulness, and response latency.

## Improve Example Problem Detection Algorithm

- Detect worked examples across varied textbook layouts, headings, numbering schemes, and page boundaries.
- Distinguish solved examples from unsolved exercises, practice questions, definitions, and explanatory passages.
- Associate each problem with its complete solution, diagrams, equations, and source-page references.
- Improve detection quality when source text contains OCR errors or unusual formatting.
- Combine structural heuristics and model-based extraction while reducing duplicates and incomplete examples.
- Build an evaluation dataset and measure precision, recall, duplicate rate, and extraction completeness.

## Segment Class Creation And Example Problem Upload UIs

- Separate class creation and example problem upload into focused teacher workflows.
- Keep class setup centered on class details, learning objectives, enrollment, and configuration.
- Move material upload, example extraction, review, and publishing into a dedicated interface.
- Clearly communicate prerequisites and guide teachers to the appropriate next workflow.
- Preserve progress and provide clear success, processing, and error states in each interface.
- Test whether the segmented workflows reduce confusion and improve task completion.

## Multimodal Embeddings And RAG

- Extract and index diagrams, charts, equations, tables, and page images alongside text.
- Generate embeddings that place related visual and textual content in a shared retrieval space.
- Preserve page coordinates and relationships between visuals, captions, and surrounding text.
- Retrieve both text passages and relevant visuals when answering student questions.
- Let the tutor reason over retrieved images instead of relying only on OCR descriptions.
- Evaluate retrieval quality, answer accuracy, latency, storage requirements, and model cost against text-only RAG.
