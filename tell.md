So basically we're working on a project called Attackbot. Read the files attached to project for full context as well as your task



Architecture.md — The full system architecture for AttackBot, an automated bug bounty discovery and reporting platform. Read this to understand the overall system design, service inventory, database schema, message queue topology, and the security principles (scope enforcement, evidence-first findings) that govern every implementation decision.

Default.md — The codebase conventions and practices that must be followed across every file. This covers project structure, naming conventions, shared library usage, logging patterns, error handling, async patterns, and testing standards. Every file you write must conform to these defaults — check here before making any structural decision.

Milestone.md — The high-level milestone roadmap for the full platform. Read this for the big-picture context of where the current milestone fits, what was built before it, and what comes after. Each milestone's Definition of Done and Goals sections are the acceptance criteria.

Flow.md — The end-to-end data and message flow through the system. Read this to understand how services connect, what messages travel between them, and how a scan job moves from ingestion through pipeline execution to report generation.

Progress.md — The current state of the codebase. This tells you exactly which files exist, which migrations have been applied, which tests are passing, and what known issues remain. Treat this as ground truth for what is already built — do not reimplement anything listed here as complete.

M3_FirstStrike.md — The low-level implementation plan for the milestone you are about to build. This is the primary document driving your work. It contains every file to create or replace, full implementation code, migration details, test cases, a verification sequence, and a known pitfalls table. Follow it step by step in the order given. Read each step fully before writing any code.

Your task: Implement the milestone defined in M3_FirstStrike.md from top to bottom. Follow the file map at the top of the document to understand the full scope of changes before starting. Adhere to Default.md conventions throughout. Do not modify any files outside the scope defined in the milestone document unless a blocking dependency requires it — and if it does, flag it explicitly before proceeding.