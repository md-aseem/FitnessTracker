# Q2 Transient Model (C Version)

This directory contains the C implementation of the Q2 transient thermal model. Follow the instructions below to compile and run the simulation.

## Prerequisites
Ensure you have a C++ compiler (`g++` or `clang++`) installed on your system.

## 1. Compilation
The project includes a build script to simplify compilation.

First, ensure the build script has execute permissions:
```bash
chmod +x makeQ2Model
```

Then, run the script to compile the model:
```bash
./makeQ2Model
```
*(Note: If you see warnings like "treating 'c' input as 'c++'", these are expected and can be ignored. They just indicate that standard `.c` files are being compiled with a C++ compiler).*

This will generate an executable named `q2_transient_model`.

## 2. Configuration
Before running the model, you can configure the simulation parameters (such as initial temperatures, chiller models, and battery states) by editing the input file:
- `input.in`

The power profile inputs are read from:
- `powerProfile.in`

## 3. Execution
Once compiled and configured, run the generated executable:
```bash
./q2_transient_model
```

## 4. Outputs
After the simulation finishes, it will produce output files in the current directory:
- `transient.out`: Contains the main transient simulation results and data.
- `log.out`: Contains logging information from the run.
