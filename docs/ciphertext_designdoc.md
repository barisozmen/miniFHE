# Micro Design Document: Ciphertext

## 1. Introduction

The `Ciphertext` object is a fundamental data structure in the FHE library. It represents encrypted data. In the CKKS scheme (and many RLWE-based schemes), a freshly encrypted ciphertext typically consists of a pair of polynomials. This document details the structure and attributes of the `Ciphertext` class.

## 2. Purpose

*   To encapsulate the polynomial components of an encrypted message.
*   To store metadata associated with the ciphertext, such as its current computation `level`, `scaling_factor`, and a (conceptual) `noise_estimate`.
*   To provide a standardized representation for encrypted data that can be passed to and manipulated by the `Evaluator`.

## 3. Attributes

A `Ciphertext` object will have the following attributes:

*   **`c0`**: `Polynomial` (or `np.ndarray` representing polynomial coefficients)
    *   The first polynomial component of the ciphertext.
    *   In RLWE-based encryption `pk=(b,a), sk=s` where `b=-as+e`:
        *   `c0 = pk_b * u + e1 + m`  (if `u` is encryption randomness, `m` is plaintext poly)
        *   Or `c0 = pk_0 * v + e_0 + m` (if `pk=(pk_0,pk_1)`, `v` is randomness)
*   **`c1`**: `Polynomial` (or `np.ndarray` representing polynomial coefficients)
    *   The second polynomial component of the ciphertext.
    *   `c1 = pk_a * u + e2`
    *   Or `c1 = pk_1 * v + e_1`
*   **`level`**: `int`
    *   The current computation level of the ciphertext. This corresponds to an index in the `Context`'s chain of ciphertext moduli.
    *   A higher level usually means a larger modulus and more noise budget remaining. Operations like rescaling decrease the level. Bootstrapping resets it to the maximum.
*   **`scaling_factor`**: `float`
    *   The scaling factor `Δ` currently associated with the encrypted message.
    *   Plaintext values `v` were encoded as `round(Δ * v)`.
    *   Homomorphic multiplication `ct1 * ct2` results in a new ciphertext with `scaling_factor = ct1.scaling_factor * ct2.scaling_factor`.
    *   Rescaling reduces this `scaling_factor`, typically back to an initial scale or `ct.scaling_factor / q_dropped`.
*   **`noise_estimate`**: `float` (Conceptual)
    *   A conceptual or simplified numerical estimate of the noise present in the ciphertext.
    *   Fresh encryptions have a small initial noise.
    *   Homomorphic operations increase this noise.
    *   Bootstrapping resets it.
    *   This is primarily for educational tracking; precise noise analysis is highly complex.
*   **`modulus`**: `int` (Potentially, or derived from `level` and `context`)
    *   The actual ciphertext modulus `q` that the polynomial coefficients `c0, c1` are currently modulo.
    *   This can be stored directly or, more commonly, inferred by the `Evaluator` using `ciphertext.level` and the `Context`. Storing it might be redundant but could be convenient for debugging or certain operations.
    *   Decision: For now, `modulus` will not be a direct attribute but will be obtained via `context.get_modulus_for_level(ciphertext.level)`. This keeps `Ciphertext` lighter and reliant on the `Context` for modulus information, which is cleaner.

## 4. Methods

The `Ciphertext` class will primarily be a data container. It might have a simple constructor:

*   **`__init__(self, c0: np.ndarray, c1: np.ndarray, level: int, scaling_factor: float, noise_estimate: float)`**:
    *   Initializes the ciphertext with its components and metadata.
    *   Polynomials `c0` and `c1` are expected to be NumPy arrays representing their coefficients.

It generally does not perform cryptographic operations itself; such operations are the responsibility of the `Evaluator`.

## 5. Polynomial Representation

The attributes `c0` and `c1` will store polynomial coefficients as NumPy arrays. The degree of these polynomials is determined by `context.poly_degree` (N-1, as they are elements of R_q = Z_q[X]/(X^N+1)). All coefficients are integers modulo the current `q` associated with `ciphertext.level`.

## 6. Ciphertext Size after Multiplication

Standard CKKS ciphertext multiplication `ct1 * ct2` initially results in a 3-polynomial ciphertext `(d0, d1, d2)`. This is then "relinearized" back to a 2-polynomial ciphertext.
*   This `Ciphertext` class is designed to hold the 2-polynomial form.
*   During multiplication, the `Evaluator` will temporarily handle the 3-polynomial form before producing a final 2-polynomial `Ciphertext` object via relinearization.

## 7. Immutability

Consider whether `Ciphertext` objects should be immutable. If homomorphic operations in the `Evaluator` always return new `Ciphertext` objects, then immutability can simplify reasoning about the state.
*   Decision: `Ciphertext` instances will be treated as immutable. Operations will return new instances.

## 8. Example Usage

```python
# Context and other necessary components are set up
# ...

# Typically, a Ciphertext is created by an encrypt operation:
# ct = evaluator.encrypt(plaintext, public_key)
# ct will have c0, c1, level (max), scaling_factor (initial), noise_estimate (small)

# Accessing attributes:
# print(f"Ciphertext level: {ct.level}")
# print(f"Ciphertext scaling factor: {ct.scaling_factor}")
# poly_c0_coeffs = ct.c0

# If manually creating (e.g., for testing, though not typical user action):
# c0_coeffs = np.array([...])
# c1_coeffs = np.array([...])
# initial_noise = 10.0 # Arbitrary conceptual value
# ct_manual = Ciphertext(c0_coeffs, c1_coeffs, level=max_level, scaling_factor=initial_delta, noise_estimate=initial_noise)
```

The `Ciphertext` class, as designed here, serves as a well-defined container for encrypted data, carrying the necessary information for the `Evaluator` to perform homomorphic operations and manage scheme parameters like levels and scaling factors.
---
Next, `docs/plaintext_designdoc.md`.
