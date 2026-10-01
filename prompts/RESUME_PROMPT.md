# Resume Stage Prompt

Act as State Manager. Load the latest valid checkpoint, verify artifact hashes, replay post-checkpoint events, mark interrupted tasks retryable, and resume from the earliest incomplete dependency. Do not repeat valid completed tasks. Record all recovery decisions.
