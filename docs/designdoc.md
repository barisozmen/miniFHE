# Design Document: Python FHE Library (CKKS Scheme)

## 1. Introduction

This document outlines the design for a Python library implementing a simplified version of the Cheon-Kim-Kim-Song (CKKS) homomorphic encryption scheme. The goal is to provide a clear, understandable, and educational implementation that captures the core concepts of CKKS, inspired by the elegance and clarity of Peter Norvig's coding style.

The library will support approximate arithmetic on encrypted real or complex numbers, enabling computations like addition, multiplication, and rotations on vectors of data. It will also include simulations of advanced FHE concepts like rescaling, key switching, and bootstrapping to manage noise and computational depth.

## 2. Goals

*   **Clarity and Readability**: The primary goal is to produce code that is easy to understand and follow, even for those new to FHE.
*   **Educational Value**: Serve as a learning tool for understanding the mechanics of the CKKS scheme.
*   **Functional Core**: Implement the essential operations of CKKS:
    *   Key Generation
    *   Encoding/Decoding (for real/complex vectors)
    *   Encryption/Decryption
    *   Homomorphic Addition
    *   Homomorphic Multiplication
    *   Homomorphic Rotations (Slot Permutations)
*   **Noise Management Simulation**: Include mechanisms for:
    *   Rescaling (Modulus Switching)
    *   Key Switching
    *   Bootstrapping (Conceptual Simulation)
*   **Modular Design**: Structure the library into logical components that can be understood and potentially extended independently.
*   **Pythonic Implementation**: Utilize Python's features effectively to create an elegant and idiomatic codebase.

## 3. Non-Goals

*   **Production-Ready Security**: This library is for educational purposes and will not offer the security guarantees of production-grade FHE libraries (e.g., SEAL, TenSEAL, PALISADE, HElib). It will use simplified cryptographic primitives and may not be resistant to all known attacks.
*   **Performance Optimization**: Clarity will be prioritized over raw performance.
*   **Full CKKS Feature Set**: Some advanced features or optimizations of the full CKKS scheme (e.g., RNS, full complex number arithmetic in bootstrapping, precise noise analysis using underlying lattice theory) will be simplified or simulated.
*   **Support for other HE Schemes**: The library will focus solely on a CKKS-like scheme.

## 4. Architecture Overview

The library will be structured around several key components:

1.  **`Context`**: Manages global parameters for the HE scheme, such as:
    *   Polynomial degree (N)
    *   Ciphertext modulus (q) / Modulus chain
    *   Scaling factor (Δ)
    *   Security parameters (simplified)

2.  **`Encoder`**: Handles the transformation of real/complex number vectors into plaintext polynomials suitable for CKKS, and vice-versa. This involves scaling and potentially an NTT-like transformation (simplified).

3.  **`Keys`**: Data structures for:
    *   **`SecretKey`**: Used for decryption.
    *   **`PublicKey`**: Derived from the secret key, used for encryption.
    *   **`RelinKey`**: Used for relinearizing ciphertexts after multiplication.
    *   **`GaloisKey`**: Used for performing homomorphic rotations.

4.  **`Plaintext`**: Represents data that has been encoded but not yet encrypted. Typically a polynomial.

5.  **`Ciphertext`**: Represents encrypted data. Typically a pair of polynomials (c0, c1) in CKKS. It will also track its current modulus, scale, and noise level (simulated).

6.  **`EncryptionScheme` / `Evaluator`**: The core engine containing methods for:
    *   `keygen()`: Generates public, secret, relinearization, and Galois keys.
    *   `encrypt(plaintext, public_key)`: Encrypts a plaintext.
    *   `decrypt(ciphertext, secret_key)`: Decrypts a ciphertext.
    *   `add(ciphertext1, ciphertext2)`: Homomorphically adds two ciphertexts.
    *   `multiply(ciphertext1, ciphertext2)`: Homomorphically multiplies two ciphertexts. This will involve relinearization.
    *   `relinearize(ciphertext, relin_key)`: Reduces the size of a ciphertext after multiplication.
    *   `rescale(ciphertext)`: Performs modulus switching to manage noise and scale.
    *   `rotate(ciphertext, steps, galois_key)`: Homomorphically rotates the slots of an encrypted vector.
    *   `bootstrap(ciphertext)`: (Simulated) Refreshes a ciphertext to reduce noise and reset scale.

7.  **`Utils`**: Helper functions, e.g., for polynomial arithmetic (simplified, possibly using NumPy for vector operations), prime number generation (for modulus selection, simplified).

## 5. Core Components (Micro Design Doc Pointers)

Detailed design for each component will be provided in separate micro design documents:

*   `docs/context_designdoc.md`
*   `docs/encoder_designdoc.md`
*   `docs/keys_designdoc.md`
*   `docs/plaintext_designdoc.md`
*   `docs/ciphertext_designdoc.md`
*   `docs/encryption_scheme_designdoc.md` (will also cover evaluator aspects)
*   `docs/operations_designdoc.md` (may be merged into encryption_scheme or detail specific arithmetic)
*   `docs/rescaling_designdoc.md`
*   `docs/rotations_designdoc.md`
*   `docs/key_switching_designdoc.md`
*   `docs/bootstrapping_designdoc.md`

## 6. Data Representation

*   **Polynomials**: Will likely be represented as NumPy arrays for ease of coefficient-wise operations. The underlying ring will be R_q = Z_q[X] / (X^N + 1), where N is a power of 2.
*   **Real/Complex Numbers**: Standard Python floats and complex numbers. Vectors will be NumPy arrays.

## 7. Noise Management (Simplified)

*   **Initial Noise**: Encryption will introduce a small amount of noise.
*   **Noise Growth**: Operations like addition and multiplication will increase the noise in the ciphertext. This will be tracked conceptually or with a simplified numerical estimate.
*   **Modulus Switching (Rescaling)**: After multiplication, the ciphertext modulus and the internal message scaling will be adjusted to reduce noise relative to the message. This allows for deeper computations.
*   **Bootstrapping**: A simulated process to take a noisy ciphertext, homomorphically decrypt it (using an encrypted secret key), and re-encrypt the message, effectively resetting the noise and scale.

## 8. Key Concepts from Conversation to Implement

*   **CKKS-style approximate arithmetic**: Focus on real number operations with controlled precision loss.
*   **Vectorized operations (SIMD)**: Encode vectors of numbers into single polynomials.
*   **Scale management**: Explicitly track and adjust the scaling factor `Δ`.
*   **Modulus chain / Levels**: Implement a concept of "levels" corresponding to different moduli in a chain, used for rescaling.
*   **Noise tracking (simulated)**: Each ciphertext will have a `noise_level` attribute, and operations will update it. `bootstrap` will reset it.
*   **Bootstrapping simulation**: `decrypt -> encode -> encrypt` loop, conceptually resetting noise and scale.
*   **Rotation simulation**: Use `np.roll` on the underlying plaintext vector for simplicity, with associated key switching simulation.
*   **Key switching simulation**: Conceptually "refreshing" a ciphertext after an operation that changes its underlying key structure (like rotation).

## 9. Directory Structure

```
fhe_library/
├── __init__.py
├── context.py
├── encoder.py
├── encryption_scheme.py  # Or evaluator.py
├── keys.py
├── operations.py         # Or integrated into encryption_scheme
├── ciphertext.py
├── plaintext.py
└── utils.py
docs/
├── designdoc.md
├── ... (micro design docs)
tests/
├── __init__.py
├── test_encoder.py
├── ...
examples/
└── simple_ckks_demo.py
README.md
requirements.txt
```

This design provides a roadmap for building the educational FHE library. Each component will be further detailed in its respective micro design document.
