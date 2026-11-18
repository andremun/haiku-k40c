# RTIOCTL: the first user interface of the driver

## Why and inputs

Answers Q2 to Q5 (docs/OPEN_QUESTIONS.md) for `haiku-k40c-llm`
(`docs/design/runtime-contract-v0.2.md`). Source: docs/design/specification.md:538-542.

## Outputs

- docs/RUNTIME-INTERFACE.md: the operations, their structures, ownership and error rules.
- A shared C header with the ioctl numbers and structures, used by both repositories.
- A host implementation behind the header for the tests of `haiku-k40c-llm`.
- Answers written into Q2 to Q5.

## Checks and limits

Host tests. No device node on a card before S3 passes. The interface is polling only.
