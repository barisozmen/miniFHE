# Micro Design Document: Context

## 1. Introduction

The `Context` object is a central component in the FHE library. It holds and manages all global parameters required for the CKKS scheme to operate. This includes parameters related to polynomial rings, ciphertext moduli, scaling factors, and security levels. Having a context object ensures consistency and simplifies parameter passing across different modules of the library.

## 2. Purpose

*   To centralize all scheme-wide parameters.
*   To provide a single source of truth for configuration.
*   To facilitate the initialization and setup of the HE environment.
*   To manage the chain of moduli used for rescaling.

## 3. Attributes

The `Context` class will have the following attributes:

*   **`poly_degree` (N)**: `int`
    *   The degree of the polynomial ring R = Z[X] / (X^N + 1). Must be a power of 2.
    *   Determines the number of slots available for encoding (N/2 for complex numbers, N for real if packed differently, though typically N/2 is used for CKKS).
*   **`plaintext_modulus` (t)**: `int` (Optional, less prominent in CKKS than in BGV/BFV but can be conceptual for plaintext space before scaling)
    *   While CKKS doesn't strictly use a plaintext modulus in the same way as BFV/BGV, this might represent a conceptual bound or be used in specific encoding schemes. For our simplified CKKS, the scaling factor is more critical. We might omit this or keep it for conceptual completeness if a specific encoding variant benefits.
    *   For now, we will focus on the `scaling_factor` and `ciphertext_moduli`.
*   **`scaling_factor` (delta)**: `float` or `int`
    *   The initial factor by which plaintext real/complex numbers are multiplied before being rounded to integers for encoding.
    *   Crucial for managing precision in CKKS.
*   **`ciphertext_moduli` (q_i)**: `list[int]`
    *   A list of prime numbers representing the chain of ciphertext moduli.
    *   Operations start at `q_0` (largest modulus). Rescaling moves the ciphertext to the next modulus in the chain (`q_1`, `q_2`, ...).
    *   The size of these primes affects the security and the noise capacity.
*   **`security_level`**: `int` (e.g., 128, 192, 256)
    *   A parameter indicating the target cryptographic security strength (in bits). This would typically influence the choice of `poly_degree` and `ciphertext_moduli` in a production library. In our educational version, this will be more conceptual and might just guide default parameter selection.
*   **`precision_bits`**: `int`
    *   Desired number of bits of precision for fractional parts of numbers. This helps in setting the `scaling_factor` (e.g., `delta = 2^precision_bits`).

## 4. Methods

*   **`__init__(self, poly_degree: int, scaling_factor: float, ciphertext_moduli: list[int], security_level: int = 128, precision_bits: int = 20)`**:
    *   Constructor to initialize the context with the given parameters.
    *   May perform validation (e.g., `poly_degree` is a power of 2, moduli are primes).
    *   May calculate `scaling_factor` if `precision_bits` is given and `scaling_factor` is not.
*   **`get_modulus_for_level(self, level: int) -> int`**:
    *   Returns the ciphertext modulus `q_i` corresponding to a given computation `level`. Level 0 would be the largest modulus, level 1 the next, and so on.
*   **`num_levels(self) -> int`**:
    *   Returns the total number of available computation levels (i.e., `len(ciphertext_moduli)`).

## 5. Parameter Generation (Simplified)

In a full FHE library, the context might also include methods to automatically generate suitable `ciphertext_moduli` based on `poly_degree` and `security_level`. For this educational library, we will likely require the user to provide these parameters directly, or we'll provide some pre-selected default sets.

Example of pre-selected parameters:
```python
# Example parameters for a given security level (conceptual)
DEFAULT_PARAMS = {
    128: {
        "poly_degree": 2**12, # N = 4096
        "ciphertext_moduli": [get_prime(bits=60), get_prime(bits=40), get_prime(bits=40)], # Example q_i
        "scaling_factor": 2**40,
    }
}
```
*(`get_prime` would be a utility function)*

## 6. Usage

The `Context` object will be created once at the beginning of an FHE session and passed to various components like the `Encoder`, `KeyGenerator`, and `Evaluator`.

```python
# Example
from fhe_library.utils import generate_primes # Assuming a helper

# User-defined or default parameters
poly_degree = 2**12
moduli_bits = [60, 40, 40, 60] # Bits for primes q0, q1, q2, q_special_prime_for_keyswitch
ciphertext_moduli = generate_primes(moduli_bits, poly_degree) # Helper to find suitable primes
scaling_factor = 2**40

context = Context(
    poly_degree=poly_degree,
    scaling_factor=scaling_factor,
    ciphertext_moduli=ciphertext_moduli
)

# Then, use this context for other operations
# keys = KeyGenerator(context).generate()
# encoder = Encoder(context)
# evaluator = Evaluator(context)
```

## 7. Open Questions/Considerations

*   **Prime Generation**: How will the moduli primes be generated or selected? For simplicity, we might start with fixed primes or a very basic prime generation utility. Real FHE libraries use specific forms of primes (e.g., NTT-friendly primes).
*   **Default Parameter Sets**: Should we provide default parameter sets for common `poly_degree` values? This would make the library easier to use initially.
*   **Strictness of Validation**: How strictly should parameters be validated in the constructor?

This design provides a clear role for the `Context` class, ensuring that all parts of the FHE system operate with compatible and consistent parameters.
