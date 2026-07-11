# VeriGenX Contributing Guidelines

Thank you for contributing to VeriGenX!

## Development Rules
1. **No Hardcoded Defaults**: All extraction pipelines must support customizable design fallbacks (e.g., SPI, I2C, AXI, FIFO, UART).
2. **Correct UVM Dependency Structure**: Only UVM driver and monitor components may access or hold virtual interface handles. Scoreboards, sequences, and coverage components must depend on data containers like `sequence_item` only.
3. **Robust Unit Tests**: All modules must include accompanying unit tests placed under the `tests/unit/` folder.

## Executing the Test Suite
Run the full test suite with coverage reporting:
```bash
pytest --cov=VeriGenX tests/
```
Ensure all tests pass before making pull requests.
