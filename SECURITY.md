# Security policy

## Supported versions

Security fixes are provided for the latest released minor version.

## Reporting a vulnerability

Please use GitHub's private vulnerability-reporting form for this repository rather
than a public issue. Include the affected version, minimal reproduction, impact, and any
suggested mitigation. Do not attach sensitive craft images or credentials.

## Security model

PatternProof has no network feature, authentication, telemetry, plugin execution, or
shell interpolation. Its external surfaces are local JSON/image inputs and a new output
directory. Inputs are size-bounded and strictly validated, HTML text is escaped, and a
failed write does not leave a completed-looking report.

This model does not make arbitrary image decoders risk-free. Use supported releases,
keep Pillow current, and do not run PatternProof with more filesystem privileges than
its input and output directories require.
