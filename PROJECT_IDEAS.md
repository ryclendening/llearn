# lLearn Project Ideas

This is the persistent backlog for potential lLearn improvements. Move an idea
into active development only after defining its user value, scope, and success
criteria.

## Near Term

### Add Real OCR Fallback

- Detect PDF pages that contain little or no embedded text.
- Render those pages and process them with an OCR provider.
- Feed OCR output through the existing document-processing boundary.
- Track whether page text came from native extraction or OCR.

### Material Processing Jobs

- Move PDF ingestion and example extraction out of synchronous upload requests.
- Add queued, processing, ready, and failed states.
- Let the frontend display progress and retry failed stages.
- Ensure repeated jobs are idempotent.

### Backend Test Foundation

- Adopt `pytest` and add it to development dependencies.
- Add service-level tests for material processing status transitions.
- Mock OpenAI and Weaviate in automated tests.
- Add API tests for material upload, extraction, and deletion.

### Typed Backend Contracts

- Introduce Pydantic response models for API endpoints.
- Replace loosely structured dictionaries with typed domain models where useful.
- Document the frontend/backend API contract.

### Material Processing Observability

- Replace `print` statements with structured logging.
- Add request and processing job identifiers.
- Record processing duration, extracted page count, chunk count, and failures.

## Learning Experience

### Teacher Review Workflow

- Let teachers review and edit extracted examples before publishing them.
- Show extraction confidence and source-page links.
- Support rejecting, merging, and re-extracting examples.

### Adaptive Practice

- Select practice examples based on student mastery and previous attempts.
- Adjust hint difficulty based on recent performance.
- Track which concepts cause repeated mistakes.

### Citation Viewer

- Make tutor citations clickable.
- Open the source material at the cited page.
- Highlight the supporting text when possible.

### Learning Progress Timeline

- Show students and teachers how mastery changes over time.
- Include practice attempts, tutor sessions, and objective assessments.
- Explain why an objective was marked mastered.

## Retrieval And Parsing

### Semantic Chunking

- Chunk material by headings, paragraphs, and concepts instead of fixed character counts.
- Preserve section titles and neighboring context as metadata.
- Compare retrieval quality against the current fixed-size chunking.

### Parsing Evaluation Dataset

- Create a small collection of representative educational PDFs.
- Store expected extracted examples and page references.
- Measure parser precision, recall, duplicate rate, and OCR quality.

### Multiple Material Formats

- Add support for DOCX, PPTX, images, and plain text.
- Route each format through a shared document-page representation.
- Keep format-specific extraction isolated from parsing and ingestion.

### Extraction Provider Comparison

- Compare heuristic parsing, OpenAI structured extraction, and alternative models.
- Track accuracy, latency, and cost.
- Allow selecting a provider through configuration.

## Platform And Operations

### Background Worker Architecture

- Introduce a worker process for document processing and long-running AI tasks.
- Define retry policies and dead-letter handling.
- Keep API servers responsive during large uploads.

### Authentication And Roles

- Add secure authentication.
- Define student, teacher, and administrator permissions.
- Protect solutions, class materials, and student performance data.

### Continuous Integration

- Run backend tests when backend files change.
- Run frontend tests when frontend files change.
- Run integration checks before merging.
- Add formatting, linting, and type-checking gates.

### Deployment Environments

- Define local, staging, and production configuration.
- Manage secrets outside the repository.
- Add database migrations and repeatable deployment steps.

## Larger Experiments

### Teacher-Created Tutor Policies

- Let teachers configure tutoring tone, allowed hints, and answer-reveal rules.
- Preview how policies affect generated responses.
- Version policies so class behavior is reproducible.

### Misconception Detection

- Identify recurring incorrect reasoning patterns from student attempts.
- Surface likely misconceptions to teachers.
- Recommend targeted explanations and exercises.

### Course Knowledge Graph

- Connect objectives, source sections, examples, and prerequisite concepts.
- Use the graph to improve retrieval and adaptive lesson sequencing.
- Visualize gaps between materials and learning objectives.

### Offline Or Local Model Mode

- Explore local embedding, OCR, extraction, and tutoring models.
- Compare privacy, quality, hardware requirements, and operating cost.

## Completed Structural Work

- Separated document text extraction from vector ingestion.
- Separated example extraction, parsing, normalization, and grading.
- Added an injectable OCR fallback boundary.
- Moved material processing orchestration out of the HTTP router.
- Added focused document-processing, parsing, and chunking tests.
