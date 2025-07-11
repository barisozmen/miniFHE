# Micro Design Document: Plaintext

## 1. Introduction

The `Plaintext` object represents data that has been prepared for encryption or is the result of decryption before final decoding. In the CKKS scheme, this typically means a polynomial whose coefficients encode a vector of scaled real or complex numbers.

## 2. Purpose

*   To encapsulate a polynomial representing encoded data.
*   To store metadata associated with this encoded data, such as the `scaling_factor` used during encoding and the intended `level` for encryption.
*   To provide a standardized representation that the `Encoder` produces and the `EncryptionScheme` consumes (for encryption) or produces (from decryption).

## 3. Attributes

A `Plaintext` object will have the following attributes:

*   **`coeffs`**: `np.ndarray`
    *   A NumPy array representing the integer coefficients of the plaintext polynomial.
    *   These coefficients are the result of the CKKS encoding process (which includes scaling the original values and an IFFT-like transformation).
    *   The polynomial is an element of R = Z[X] / (X^N + 1).
*   **`scaling_factor`**: `float`
    *   The scaling factor `Δ` that was used by the `Encoder` to transform the original real/complex values into the integer coefficients stored in `coeffs`.
    *   `encoded_value ≈ round(original_value * scaling_factor)`.
    *   This is crucial for interpreting the magnitude of the polynomial's evaluations and for managing precision during homomorphic operations.
*   **`level`**: `int`
    *   The intended or current computation `level` for this plaintext.
    *   When a plaintext is freshly encoded, it's typically set to the highest level (e.g., `context.num_levels() - 1`), indicating it's ready for encryption with the largest modulus `q_0`.
    *   When a plaintext is the result of decryption, its `level` will match that of the decrypted ciphertext.
*   **`modulus`**: `int` (Optional, similar to Ciphertext)
    *   The plaintext polynomial coefficients themselves are integers, not necessarily modulo `q` until they are part of an encryption. However, for plaintext operations (e.g., `add_plain`, `multiply_plain`), the plaintext polynomial is added to or multiplied by ciphertext components *modulo q*.
    *   It might be useful for a `Plaintext` to know which `q` it's "compatible" with, based on its `level`.
    *   Decision: Similar to `Ciphertext`, `modulus` will not be a direct attribute. It can be inferred from `plaintext.level` and the `Context` by the `Evaluator` when needed. The raw `coeffs` are integers; their reduction modulo `q` happens during cryptographic operations.

## 4. Methods

The `Plaintext` class will primarily be a data container.

*   **`__init__(self, coeffs: np.ndarray, scaling_factor: float, level: int)`**:
    *   Initializes the plaintext with its polynomial coefficients and metadata.

It does not perform encoding/decoding or cryptographic operations itself.

## 5. Relationship with `Encoder` and `EncryptionScheme`

*   **`Encoder.encode(...)` -> `Plaintext`**: The `Encoder` takes a vector of real/complex numbers and a target scaling factor, and produces a `Plaintext` object. The `level` would typically be set to the max level.
*   **`EncryptionScheme.encrypt(Plaintext, ...)` -> `Ciphertext`**: The encryption process takes a `Plaintext` object and encrypts its `coeffs`. The `scaling_factor` and `level` from the `Plaintext` are typically transferred to the resulting `Ciphertext`.
*   **`EncryptionScheme.decrypt(Ciphertext, ...)` -> `Plaintext`**: Decryption yields a polynomial that is noisy but approximates the original encoded polynomial. This is packaged into a `Plaintext` object, retaining the `scaling_factor` and `level` of the input `Ciphertext`.
*   **`Encoder.decode(Plaintext)` -> `np.ndarray`**: The `Encoder` takes a `Plaintext` (usually from decryption) and uses its `coeffs` and `scaling_factor` to recover the approximate real/complex vector.

## 6. Plaintext Operations

While the `Plaintext` object itself won't have methods for arithmetic, the `Evaluator` will have operations like `add_plain(ciphertext, plaintext)` and `multiply_plain(ciphertext, plaintext)`. In these operations, the `plaintext.coeffs` are used directly in polynomial arithmetic with the ciphertext components, modulo the ciphertext's current `q`. The `plaintext.scaling_factor` also plays a role in determining the `scaling_factor` of the resulting ciphertext after `multiply_plain`.

## 7. Immutability

Similar to `Ciphertext`, `Plaintext` instances will be treated as immutable.

## 8. Example Usage

```python
# Context and Encoder are set up
# context = Context(...)
# encoder = Encoder(context)

# Encoding produces a Plaintext
# values = np.array([1.5, 2.0, -0.5])
# target_scale = context.initial_scale
# max_level = context.num_levels() - 1
# pt = encoder.encode(values, target_scale, max_level) # Encoder sets level

# Accessing attributes:
# print(f"Plaintext polynomial coeffs: {pt.coeffs}")
# print(f"Plaintext scaling factor: {pt.scaling_factor}")
# print(f"Plaintext level: {pt.level}")

# This pt would then be passed to an encrypt function
# ct = evaluator.encrypt(pt, public_key)

# After decryption:
# decrypted_pt = evaluator.decrypt(ct, secret_key)
# # decrypted_pt is also a Plaintext object
# # Its coeffs are noisy approximations of pt.coeffs
# # Its scaling_factor and level match ct
#
# final_values = encoder.decode(decrypted_pt)
```

The `Plaintext` class provides a clean interface between the encoding layer and the cryptographic layer, carrying the essential information needed for both processes.
---
Next, `docs/keys_designdoc.md`.
